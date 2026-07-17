import unittest

from scripts.monitor_resources import memory_to_mib


class ResourceMonitorTests(unittest.TestCase):
    def test_converts_memory_units_to_mib(self):
        self.assertEqual(memory_to_mib("1024KiB"), 1.0)
        self.assertEqual(memory_to_mib("25MiB"), 25.0)
        self.assertEqual(memory_to_mib("2GiB"), 2048.0)


if __name__ == "__main__":
    unittest.main()
