import unittest

from prometheus_client import REGISTRY

from main import process_batch


MESSAGES = [
    {
        "experiment_id": "experiment-1",
        "variant_id": "variant-1",
        "user_id": "user-1",
        "event_type": "exposure",
    },
    {
        "experiment_id": "experiment-1",
        "variant_id": "variant-2",
        "user_id": "user-2",
        "event_type": "exposure",
    },
]


def metric_value(name: str) -> float:
    return REGISTRY.get_sample_value(name) or 0.0


class SuccessfulClient:
    def __init__(self):
        self.rows = None

    def insert(self, table, rows, column_names):
        self.rows = rows


class FailingClient:
    def insert(self, table, rows, column_names):
        raise RuntimeError("ClickHouse unavailable")


class ProcessBatchTests(unittest.TestCase):
    def test_success_records_processed_events_and_batch(self):
        client = SuccessfulClient()
        events_before = metric_value("ab_consumer_events_processed_total")
        batches_before = metric_value("ab_consumer_batches_processed_total")

        process_batch(client, MESSAGES)

        self.assertEqual(len(client.rows), 2)
        self.assertEqual(
            metric_value("ab_consumer_events_processed_total") - events_before,
            2,
        )
        self.assertEqual(
            metric_value("ab_consumer_batches_processed_total") - batches_before,
            1,
        )

    def test_failure_records_error_without_processed_events(self):
        events_before = metric_value("ab_consumer_events_processed_total")
        errors_before = metric_value("ab_consumer_clickhouse_insert_errors_total")

        with self.assertRaisesRegex(RuntimeError, "ClickHouse unavailable"):
            process_batch(FailingClient(), MESSAGES)

        self.assertEqual(
            metric_value("ab_consumer_events_processed_total"),
            events_before,
        )
        self.assertEqual(
            metric_value("ab_consumer_clickhouse_insert_errors_total") - errors_before,
            1,
        )


if __name__ == "__main__":
    unittest.main()
