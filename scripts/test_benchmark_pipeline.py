import unittest

from scripts.benchmark_pipeline import make_event, percentile


class BenchmarkPipelineTests(unittest.TestCase):
    def test_percentile_uses_nearest_rank(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        self.assertEqual(percentile(values, 0.50), 3.0)
        self.assertEqual(percentile(values, 0.95), 5.0)

    def test_percentile_handles_no_values(self):
        self.assertIsNone(percentile([], 0.95))

    def test_make_event_is_unique_per_index(self):
        first = make_event("benchmark-run", 1)
        second = make_event("benchmark-run", 2)

        self.assertNotEqual(first["user_id"], second["user_id"])
        self.assertEqual(first["experiment_id"], "benchmark-run")
        self.assertEqual(first["event_type"], "exposure")


if __name__ == "__main__":
    unittest.main()
