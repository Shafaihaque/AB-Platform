"""Benchmark the HTTP -> Kafka -> consumer -> ClickHouse event pipeline.

Each run uses a unique synthetic experiment ID, so its ClickHouse rows can be
counted independently without deleting existing experiment data.
"""

from __future__ import annotations

import argparse
import json
import math
import queue
import statistics
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


@dataclass
class Counters:
    attempted: int = 0
    accepted: int = 0
    failed: int = 0
    request_timeouts: int = 0
    connection_errors: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load-test AB Platform ingestion and verify ClickHouse delivery."
    )
    parser.add_argument("--events", type=positive_int, default=1_000)
    parser.add_argument("--concurrency", type=positive_int, default=20)
    parser.add_argument("--ingest-url", default="http://localhost:8080/events")
    parser.add_argument("--clickhouse-url", default="http://localhost:8123")
    parser.add_argument("--request-timeout", type=positive_float, default=10.0)
    parser.add_argument(
        "--drain-timeout",
        type=positive_float,
        default=120.0,
        help="Maximum seconds to wait for accepted events to reach ClickHouse.",
    )
    parser.add_argument(
        "--poll-interval",
        type=positive_float,
        default=0.5,
        help="Seconds between ClickHouse delivery checks.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the JSON benchmark report.",
    )
    return parser.parse_args()


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return ordered[index]


def clickhouse_count(
    clickhouse_url: str,
    experiment_id: str,
    timeout: float,
) -> int:
    response = requests.get(
        clickhouse_url,
        params={
            "query": (
                "SELECT count() FROM events "
                "WHERE experiment_id = {experiment_id:String}"
            ),
            "param_experiment_id": experiment_id,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return int(response.text.strip())


def make_event(run_id: str, index: int) -> dict[str, str]:
    return {
        "experiment_id": run_id,
        "variant_id": f"benchmark-variant-{index % 2}",
        "user_id": f"{run_id}-user-{index}",
        "event_type": "exposure",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_publish_phase(
    *,
    run_id: str,
    total_events: int,
    concurrency: int,
    ingest_url: str,
    request_timeout: float,
) -> tuple[Counters, dict[int, int], list[float], float]:
    work_queue: queue.Queue[tuple[int, dict[str, str]] | None] = queue.Queue(
        maxsize=concurrency * 4
    )
    counters = Counters()
    status_codes: dict[int, int] = {}
    latencies_ms: list[float] = []
    lock = threading.Lock()

    def worker() -> None:
        session = requests.Session()
        while True:
            item = work_queue.get()
            try:
                if item is None:
                    return

                _, event = item
                request_started = time.perf_counter()
                try:
                    response = session.post(
                        ingest_url,
                        json=event,
                        timeout=request_timeout,
                    )
                    elapsed_ms = (time.perf_counter() - request_started) * 1_000
                    with lock:
                        counters.attempted += 1
                        latencies_ms.append(elapsed_ms)
                        status_codes[response.status_code] = (
                            status_codes.get(response.status_code, 0) + 1
                        )
                        if response.status_code == 202:
                            counters.accepted += 1
                        else:
                            counters.failed += 1
                except requests.Timeout:
                    with lock:
                        counters.attempted += 1
                        counters.failed += 1
                        counters.request_timeouts += 1
                except requests.ConnectionError:
                    with lock:
                        counters.attempted += 1
                        counters.failed += 1
                        counters.connection_errors += 1
            finally:
                work_queue.task_done()

    workers = [
        threading.Thread(target=worker, name=f"benchmark-worker-{index}", daemon=True)
        for index in range(concurrency)
    ]
    for worker_thread in workers:
        worker_thread.start()

    started = time.perf_counter()
    for index in range(total_events):
        work_queue.put((index, make_event(run_id, index)))

    for _ in workers:
        work_queue.put(None)

    work_queue.join()
    duration = time.perf_counter() - started
    for worker_thread in workers:
        worker_thread.join()

    return counters, status_codes, latencies_ms, duration


def wait_for_clickhouse(
    *,
    clickhouse_url: str,
    run_id: str,
    expected_count: int,
    request_timeout: float,
    drain_timeout: float,
    poll_interval: float,
) -> tuple[int, float, bool]:
    started = time.perf_counter()
    last_count = 0

    while True:
        last_count = clickhouse_count(clickhouse_url, run_id, request_timeout)
        if last_count >= expected_count:
            return last_count, time.perf_counter() - started, True

        elapsed = time.perf_counter() - started
        if elapsed >= drain_timeout:
            return last_count, elapsed, False

        time.sleep(poll_interval)


def rounded(value: float | None) -> float | None:
    return round(value, 3) if value is not None else None


def print_summary(report: dict[str, Any]) -> None:
    print("\nAB Platform pipeline benchmark")
    print("-" * 38)
    print(f"Run ID:                 {report['run_id']}")
    print(f"Events attempted:       {report['publish']['attempted']:,}")
    print(f"Events accepted (202):  {report['publish']['accepted']:,}")
    print(f"Failed requests:        {report['publish']['failed']:,}")
    print(f"Publish duration:       {report['publish']['duration_seconds']:.3f} s")
    print(f"Accepted throughput:    {report['publish']['accepted_per_second']:,.2f}/s")
    print(f"Request latency p50:    {report['publish']['latency_ms']['p50']} ms")
    print(f"Request latency p95:    {report['publish']['latency_ms']['p95']} ms")
    print(f"ClickHouse final count: {report['delivery']['stored_events']:,}")
    print(f"Consumer catch-up:      {report['delivery']['catch_up_seconds']:.3f} s")
    print(f"End-to-end duration:    {report['delivery']['end_to_end_seconds']:.3f} s")
    print(f"Complete delivery:      {report['delivery']['complete']}")


def main() -> int:
    args = parse_args()
    run_id = f"benchmark-{uuid.uuid4()}"

    print(f"Checking ClickHouse at {args.clickhouse_url}...")
    initial_count = clickhouse_count(
        args.clickhouse_url,
        run_id,
        args.request_timeout,
    )
    if initial_count != 0:
        raise RuntimeError(f"Unexpected pre-existing rows for unique run ID: {run_id}")

    print(
        f"Publishing {args.events:,} events with concurrency "
        f"{args.concurrency} to {args.ingest_url}..."
    )
    benchmark_started = time.perf_counter()
    counters, status_codes, latencies_ms, publish_duration = run_publish_phase(
        run_id=run_id,
        total_events=args.events,
        concurrency=args.concurrency,
        ingest_url=args.ingest_url,
        request_timeout=args.request_timeout,
    )

    print(
        f"Waiting up to {args.drain_timeout:.0f}s for "
        f"{counters.accepted:,} accepted events to reach ClickHouse..."
    )
    stored_events, catch_up_duration, complete = wait_for_clickhouse(
        clickhouse_url=args.clickhouse_url,
        run_id=run_id,
        expected_count=counters.accepted,
        request_timeout=args.request_timeout,
        drain_timeout=args.drain_timeout,
        poll_interval=args.poll_interval,
    )
    end_to_end_duration = time.perf_counter() - benchmark_started

    latency_mean = statistics.fmean(latencies_ms) if latencies_ms else None
    report: dict[str, Any] = {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "requested_events": args.events,
            "concurrency": args.concurrency,
            "ingest_url": args.ingest_url,
            "clickhouse_url": args.clickhouse_url,
        },
        "publish": {
            **asdict(counters),
            "status_codes": {str(code): count for code, count in status_codes.items()},
            "duration_seconds": rounded(publish_duration),
            "accepted_per_second": rounded(
                counters.accepted / publish_duration if publish_duration else 0.0
            ),
            "latency_ms": {
                "mean": rounded(latency_mean),
                "p50": rounded(percentile(latencies_ms, 0.50)),
                "p95": rounded(percentile(latencies_ms, 0.95)),
                "p99": rounded(percentile(latencies_ms, 0.99)),
                "max": rounded(max(latencies_ms) if latencies_ms else None),
            },
        },
        "delivery": {
            "stored_events": stored_events,
            "missing_events": max(0, counters.accepted - stored_events),
            "catch_up_seconds": rounded(catch_up_duration),
            "end_to_end_seconds": rounded(end_to_end_duration),
            "complete": complete and stored_events == counters.accepted,
        },
    }

    print_summary(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"JSON report:            {args.output}")

    return 0 if report["delivery"]["complete"] and counters.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
