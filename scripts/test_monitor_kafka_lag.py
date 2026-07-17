import unittest

from scripts.monitor_kafka_lag import parse_consumer_group_output


class KafkaLagMonitorTests(unittest.TestCase):
    def test_parses_consumer_group_row(self):
        output = """
GROUP        TOPIC      PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG CONSUMER-ID
ab-consumer  ab.events  0         8968           9368           400 consumer-1
"""

        sample = parse_consumer_group_output(output)

        self.assertEqual(sample.current_offset, 8968)
        self.assertEqual(sample.log_end_offset, 9368)
        self.assertEqual(sample.lag, 400)


if __name__ == "__main__":
    unittest.main()
