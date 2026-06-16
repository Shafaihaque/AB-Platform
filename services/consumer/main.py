import json
import logging
import os
from kafka import KafkaConsumer
import clickhouse_connect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

KAFKA_BROKERS = os.environ.get("KAFKA_BROKERS", "localhost:9092")
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", "8123"))


def get_clickhouse():
    """Opens a connection to ClickHouse."""
    return clickhouse_connect.get_client(host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT)


def process_batch(client, messages: list[dict]):
    """Bulk-inserts a batch of events into ClickHouse."""
    rows = [
        [msg["experiment_id"], msg["variant_id"], msg["user_id"], msg["event_type"]]
        for msg in messages
    ]
    client.insert("events", rows, column_names=["experiment_id", "variant_id", "user_id", "event_type"])
    log.info(f"Wrote {len(rows)} events to ClickHouse")


def main():
    log.info("Starting consumer...")

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
