"""Synthetic candidate, benign, near-miss, and CLI checks."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from plate_sweep import candidates


HERE = Path(__file__).parent


class PlateSweepTests(unittest.TestCase):
    def test_positive_and_benign(self):
        text = (HERE / "synthetic_ocr.txt").read_text(encoding="utf-8")
        self.assertEqual(candidates(text), ["A 2 103", "RM-27C"])
        self.assertEqual(candidates("EXIT / MAIN LOBBY / CAFETERIA"), [])

    def test_near_miss_and_known_false_positive(self):
        self.assertEqual(candidates("R M 27 C"), [])
        # A room-shaped inventory code is still a hit for human review.
        self.assertEqual(candidates("Inventory label RM-27C on a storage bin"), ["RM-27C"])

    def test_cli_text_mode(self):
        result = subprocess.run(
            [sys.executable, "-B", str(HERE / "plate_sweep.py"), "--ocr-text", str(HERE / "synthetic_ocr.txt")],
            check=True, capture_output=True, text=True,
        )
        output = json.loads(result.stdout)
        self.assertEqual(output["candidate_frames"][0]["candidates"], ["A 2 103", "RM-27C"])
        self.assertTrue(output["review_required"])

    def test_cli_rejects_unbounded_rate(self):
        result = subprocess.run(
            [sys.executable, "-B", str(HERE / "plate_sweep.py"), "--ocr-text", str(HERE / "synthetic_ocr.txt"), "--fps", "0"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fps must be", result.stderr)


if __name__ == "__main__":
    unittest.main()
