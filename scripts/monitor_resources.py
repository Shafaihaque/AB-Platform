"""Sample CPU and memory for the local pipeline processes and containers."""

from __future__ import annotations

import argparse
import csv
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


CONTAINERS = {
    "ab-platform-kafka-1": "kafka",
    "ab-platform-clickhouse-1": "clickhouse",
    "ab-platform-zookeeper-1": "zookeeper",
    "ab-platform-postgres-1": "postgres",
    "ab-platform-redis-1": "redis",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor AB pipeline resources.")
    parser.add_argument("--go-pid", type=int, required=True)
    parser.add_argument("--consumer-pid", type=int, required=True)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def memory_to_mib(value: str) -> float:
    number = float(value[:-3])
    unit = value[-3:]
    if unit == "KiB":
        return number / 1024
    if unit == "MiB":
        return number
    if unit == "GiB":
        return number * 1024
    raise ValueError(f"Unsupported memory unit: {unit}")


def process_tree(root_pid: int) -> list[int]:
    descendants: list[int] = []
    pending = [root_pid]
    while pending:
        parent = pending.pop()
        completed = subprocess.run(
            ["pgrep", "-P", str(parent)],
            capture_output=True,
            text=True,
            check=False,
        )
        children = [int(value) for value in completed.stdout.split()]
        descendants.extend(children)
        pending.extend(children)
    return [root_pid, *descendants]


def process_usage(root_pid: int) -> tuple[float, float]:
    pids = process_tree(root_pid)
    completed = subprocess.run(
        ["ps", "-o", "%cpu=,rss=", "-p", ",".join(map(str, pids))],
        check=True,
        capture_output=True,
        text=True,
    )
    cpu = 0.0
    memory_kib = 0
    for line in completed.stdout.splitlines():
        fields = line.split()
        if len(fields) == 2:
            cpu += float(fields[0])
            memory_kib += int(fields[1])
    return cpu, memory_kib / 1024


def container_usage() -> dict[str, tuple[float, float]]:
    completed = subprocess.run(
        [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    usage: dict[str, tuple[float, float]] = {}
    for line in completed.stdout.splitlines():
        name, cpu_text, memory_text = line.split("|", maxsplit=2)
        service = CONTAINERS.get(name)
        if service is None:
            continue
        used_memory = memory_text.split(" / ", maxsplit=1)[0]
        usage[service] = (
            float(cpu_text.removesuffix("%")),
            memory_to_mib(used_memory),
        )
    return usage


def collect_sample(go_pid: int, consumer_pid: int) -> dict[str, float | str]:
    go_cpu, go_memory = process_usage(go_pid)
    consumer_cpu, consumer_memory = process_usage(consumer_pid)
    containers = container_usage()
    sample: dict[str, float | str] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "go_cpu_percent": go_cpu,
        "go_memory_mib": go_memory,
        "consumer_cpu_percent": consumer_cpu,
        "consumer_memory_mib": consumer_memory,
    }
    for service in CONTAINERS.values():
        cpu, memory = containers.get(service, (0.0, 0.0))
        sample[f"{service}_cpu_percent"] = cpu
        sample[f"{service}_memory_mib"] = memory
    return sample


def main() -> int:
    args = parse_args()
    if args.interval <= 0 or args.samples <= 0:
        raise SystemExit("--interval and --samples must be greater than zero")

    samples: list[dict[str, float | str]] = []
    print("sample  go CPU  consumer CPU  Kafka CPU  ClickHouse CPU")
    print("-" * 61)
    for index in range(args.samples):
        sample = collect_sample(args.go_pid, args.consumer_pid)
        samples.append(sample)
        print(
            f"{index + 1:>6}  "
            f"{sample['go_cpu_percent']:>6.1f}%  "
            f"{sample['consumer_cpu_percent']:>11.1f}%  "
            f"{sample['kafka_cpu_percent']:>8.1f}%  "
            f"{sample['clickhouse_cpu_percent']:>13.1f}%"
        )
        if index < args.samples - 1:
            time.sleep(args.interval)

    print("\nPeak observed resources")
    for service in ["go", "consumer", *CONTAINERS.values()]:
        peak_cpu = max(float(sample[f"{service}_cpu_percent"]) for sample in samples)
        peak_memory = max(float(sample[f"{service}_memory_mib"]) for sample in samples)
        print(f"{service:<12} CPU {peak_cpu:>7.1f}%   memory {peak_memory:>8.1f} MiB")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=samples[0].keys())
            writer.writeheader()
            writer.writerows(samples)
        print(f"CSV samples: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
