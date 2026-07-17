import json
import logging
import os
import time
from kafka import KafkaConsumer
import clickhouse_connect
from prometheus_client import Counter, Histogram, start_http_server

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092")
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))
METRICS_PORT = int(os.environ.get("METRICS_PORT", "9101"))

EVENTS_PROCESSED = Counter(
    "ab_consumer_events_processed_total",
    "Total events successfully inserted into ClickHouse.",
)
BATCHES_PROCESSED = Counter(
    "ab_consumer_batches_processed_total",
    "Total event batches successfully inserted into ClickHouse.",
)
BATCH_SIZE = Histogram(
    "ab_consumer_batch_size",
    "Number of events in each attempted ClickHouse batch.",
    buckets=(1, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)
CLICKHOUSE_INSERT_DURATION = Histogram(
    "ab_consumer_clickhouse_insert_duration_seconds",
    "Time spent inserting an event batch into ClickHouse.",
)
CLICKHOUSE_INSERT_ERRORS = Counter(
    "ab_consumer_clickhouse_insert_errors_total",
    "Total failed ClickHouse batch inserts.",
)


def get_clickhouse():
    """Opens a connection to ClickHouse."""
    return clickhouse_connect.get_client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)


def process_batch(client, messages: list[dict]):
    """Bulk-inserts a batch of events into ClickHouse."""
    BATCH_SIZE.observe(len(messages))
    rows = [
        [msg["experiment_id"], msg["variant_id"], msg["user_id"], msg["event_type"]]
        for msg in messages
    ]

    insert_started = time.perf_counter()
    try:
        client.insert(
            "events",
            rows,
            column_names=["experiment_id", "variant_id", "user_id", "event_type"],
        )
    except Exception:
        CLICKHOUSE_INSERT_ERRORS.inc()
        raise
    finally:
        CLICKHOUSE_INSERT_DURATION.observe(time.perf_counter() - insert_started)

    EVENTS_PROCESSED.inc(len(rows))
    BATCHES_PROCESSED.inc()
    log.info(f"Wrote {len(rows)} events to ClickHouse")


def main():
    log.info("Starting consumer...")
    start_http_server(METRICS_PORT)
    log.info(f"Metrics server listening on :{METRICS_PORT}")

    consumer = KafkaConsumer(
        "ab.events",
        bootstrap_servers=KAFKA_BROKERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="ab-consumer",
        # on first start, read from the beginning of the topic
        auto_offset_reset="earliest",
    )

    client = get_clickhouse()
    log.info("Connected to Kafka and ClickHouse")

    while True:
        records = consumer.poll(timeout_ms=1000)
        batch = [msg.value for msgs in records.values() for msg in msgs]
        if batch:
            process_batch(client, batch)
            consumer.commit()


if __name__ == "__main__":
    main()
