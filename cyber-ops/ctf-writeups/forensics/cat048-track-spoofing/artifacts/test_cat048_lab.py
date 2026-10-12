"""Synthetic protocol and detection checks, including benign and near-miss cases."""

import json
from pathlib import Path
import unittest

import cat048_subset as cat
import track_integrity_check as hunt


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class Cat048LabTests(unittest.TestCase):
    def test_synthetic_block_round_trip(self):
        ordinary = cat.build_record(10, 1, 256, 0xA1B2C3, "7040", "SAMPLE01")
        changed = cat.build_record(10, 1, 256, 0x0BADFF, "7500", "SAMPLE01", spi=True)
        blocks = cat.decode_blocks(cat.build_block([ordinary, changed]))
        self.assertEqual(blocks[0]["length"], 61)
        self.assertEqual(blocks[0]["records"][0]["mode3a"], "7040")
        self.assertEqual(blocks[0]["records"][1]["mode_s"], "0BADFF")
        self.assertTrue(blocks[0]["records"][1]["spi"])
        for name, expected_addr in (("benign_cat048.hex", "A1B2C3"), ("forged_example.hex", "0BADFF")):
            raw = bytes.fromhex((FIXTURES / name).read_text(encoding="utf-8").strip())
            self.assertEqual(cat.decode_blocks(raw)[0]["records"][0]["mode_s"], expected_addr)

    def test_truncated_or_unknown_layout_is_rejected(self):
        record = cat.build_record(10, 1, 256, 0xA1B2C3, "7040", "SAMPLE01")
        block = cat.build_block([record])
        with self.assertRaises(ValueError):
            cat.decode_blocks(block[:-1])
        with self.assertRaises(ValueError):
            cat.decode_blocks(block[:3] + b"\x00" + block[4:])
        with self.assertRaises(ValueError):
            cat.encode_mode3a("8900")

    def test_hunt_positive_benign_near_miss_and_source_gap(self):
        registry = hunt.load_registry(FIXTURES / "protected_registry.json")
        events = hunt.load_events(FIXTURES / "ingest_events.jsonl")
        result = hunt.check(registry, events)
        self.assertEqual([item["event_id"] for item in result], ["unauthorized-peer", "source-gap"])
        self.assertEqual(result[0]["reasons"], [
            "unexpected_authenticated_peer", "registered_identity_mismatch", "suspicious_classification"
        ])
        self.assertEqual(result[1]["reasons"], ["provenance_unavailable"])
        expected = json.loads((FIXTURES / "expected_findings.json").read_text(encoding="utf-8"))
        self.assertEqual({"findings": result, "finding_count": len(result)}, expected)


if __name__ == "__main__":
    unittest.main()
