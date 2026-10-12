"""Local synthetic checks for the IQ reviewer."""

import unittest

from iq_review import inspect
from make_fixture import create, FS, TUNE_HZ


class SyntheticRFTests(unittest.TestCase):
    def test_repeated_ook_packet(self):
        result = inspect(create(), FS, TUNE_HZ)
        self.assertEqual(result["status"], "candidate")
        self.assertEqual(result["modulation"], "OOK")
        self.assertEqual(result["events"], 5)
        self.assertEqual(result["pulse_width_clusters_us"], [500, 1000])
        self.assertLess(abs(result["target_carrier_hz"] - TUNE_HZ), 500)

    def test_beacon_and_telemetry_do_not_make_a_target(self):
        result = inspect(create("beacon-only"), FS, TUNE_HZ)
        self.assertEqual(result["status"], "ambiguous_target")

    def test_repeated_multilevel_amplitude_is_not_ook(self):
        result = inspect(create("ask-near-miss"), FS, TUNE_HZ)
        self.assertEqual(result["status"], "review_modulation")
        self.assertEqual(result["modulation"], "multi-level ASK candidate")


if __name__ == "__main__":
    unittest.main()
