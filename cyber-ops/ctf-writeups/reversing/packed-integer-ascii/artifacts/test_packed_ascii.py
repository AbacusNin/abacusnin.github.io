#!/usr/bin/env python3
"""Local checks for the integer decoder and static triage proof of concept."""

import unittest
from pathlib import Path

from int_unpack_decode import inspect, parse_values, unpack
from packed_ascii_triage import scan_source

FIXTURES = Path(__file__).parent.parent / "fixtures"


class PackedAsciiTests(unittest.TestCase):
    def test_sample_round_trip_and_endian_contrast(self):
        values = parse_values((FIXTURES / "sample_packed_ints.txt").read_text(encoding="utf-8"))
        self.assertEqual(unpack(values).decode("ascii"), "Sample meeting place and time go here")
        self.assertNotEqual(inspect(values)[1]["ascii"], inspect(values)[0]["ascii"])
        raw = b"Sample meeting place and time go here\x00QZ"
        self.assertEqual([int.from_bytes(raw[i:i + 8], "big") for i in range(0, len(raw), 8)], values)

    def test_positive_benign_and_near_miss(self):
        positive = scan_source((FIXTURES / "synthetic_packed_source.py").read_text(encoding="utf-8"))
        benign = scan_source((FIXTURES / "benign_numeric_source.py").read_text(encoding="utf-8"))
        near_miss = scan_source((FIXTURES / "near_miss_utf16_source.py").read_text(encoding="utf-8"))
        self.assertEqual(len(positive), 1)
        self.assertEqual(positive[0]["integer_count"], 5)
        self.assertEqual(benign, [])
        self.assertEqual(near_miss, [])

    def test_reject_bad_input(self):
        with self.assertRaises(ValueError):
            parse_values("123, __import__('os')")
        with self.assertRaises(ValueError):
            unpack([1 << 64], 8)


if __name__ == "__main__":
    unittest.main()
