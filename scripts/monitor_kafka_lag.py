"""Sample Kafka consumer lag using Kafka's consumer-group CLI."""

from __future__ import annotations

import argparse
import csv
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class LagSample:
    timestamp: str
    current_offset: int
    log_end_offset: int
    lag: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor the AB consumer's Kafka lag.")
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def parse_consumer_group_output(output: str) -> LagSample:
    for line in output.splitlines():
        fields = line.split()
        if len(fields) >= 6 and fields[0] == "ab-consumer" and fields[1] == "ab.events":
            return LagSample(
                timestamp=datetime.now(timezone.utc).isoformat(),
                current_offset=int(fields[3]),
                log_end_offset=int(fields[4]),
                lag=int(fields[5]),
            )
    raise RuntimeError("Could not find ab-consumer / ab.events lag data")


def collect_sample() -> LagSample:
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "kafka",
        "kafka-consumer-groups",
        "--bootstrap-server",
        "kafka:29092",
        "--describe",
        "--group",
        "ab-consumer",
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_consumer_group_output(completed.stdout)


def write_csv(path: Path, samples: list[LagSample]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(["timestamp", "current_offset", "log_end_offset", "lag"])
        for sample in samples:
            writer.writerow(
                [
                    sample.timestamp,
                    sample.current_offset,
                    sample.log_end_offset,
                    sample.lag,
                ]
            )


def main() -> int:
    args = parse_args()
    if args.interval <= 0:
        raise SystemExit("--interval must be greater than zero")
    if args.samples <= 0:
        raise SystemExit("--samples must be greater than zero")

    samples: list[LagSample] = []
    print("timestamp                         current       end       lag")
    print("-" * 68)

    for index in range(args.samples):
        sample = collect_sample()
        samples.append(sample)
        print(
            f"{sample.timestamp:<33} "
            f"{sample.current_offset:>9} "
            f"{sample.log_end_offset:>9} "
            f"{sample.lag:>9}"
        )
        if index < args.samples - 1:
            time.sleep(args.interval)

    print(f"\nPeak observed lag: {max(sample.lag for sample in samples):,}")
    if args.output:
        write_csv(args.output, samples)
        print(f"CSV samples:       {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
