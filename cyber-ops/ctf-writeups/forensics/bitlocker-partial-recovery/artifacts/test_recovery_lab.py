"""Exercise positive, expected activity, and near misses in the local lab."""

import json
import io
import struct
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fve_inventory import SHARED_BITLOCKER_GUID, inspect
from recovery_events import detect
from recovery_structure import count_completions, scan, valid_group

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"


class RecoveryLabTests(unittest.TestCase):
    def test_partial_structure_positive_and_noise(self):
        report = scan((FIXTURES / "sample_note.txt").read_text(encoding="utf-8"))
        self.assertEqual(report["partial_shapes"], 2)
        self.assertEqual(report["structurally_valid_partial"], 1)
        self.assertEqual(report["completion_counts"], [909])
        self.assertEqual(count_completions("57"), 909)

    def test_group_bounds(self):
        self.assertTrue(valid_group("000000"))
        self.assertFalse(valid_group("123456"))
        self.assertFalse(valid_group("999999"))
        self.assertFalse(valid_group("12345x"))

    def test_event_positive_and_benign(self):
        events = [json.loads(line) for line in (FIXTURES / "sample_events.jsonl").read_text().splitlines()]
        findings = detect(events)
        self.assertEqual({finding["kind"] for finding in findings},
                         {"recovery_read_spike", "unapproved_recovery_unlock"})
        self.assertTrue(all(finding["actor"] == "unexpected-reader" for finding in findings))
        self.assertEqual(next(f["distinct_targets"] for f in findings if f["kind"] == "recovery_read_spike"), 3)

    def test_repeat_target_and_outside_window_do_not_alert(self):
        times = ["10:00:00", "10:03:00", "10:20:00"]
        events = [{"time": f"2026-01-01T{time}Z", "kind": "ad_recovery_read", "actor": "a",
                   "target_id": target, "attribute_name": "ms-FVE-RecoveryPassword"}
                  for time, target in zip(times, ["same", "same", "new"])]
        self.assertEqual(detect(events), [])

    def test_bad_event_rejected(self):
        with self.assertRaises(ValueError):
            detect([{"kind": "ad_recovery_read", "actor": "x", "time": "2026-01-01T10:00:00",
                     "target_id": "y", "attribute_name": "ms-FVE-RecoveryPassword"}])

    def test_inventory_rejects_false_signature_and_out_of_bounds_metadata(self):
        class FakePath:
            def __init__(self, data):
                self.data = data

            def stat(self):
                return SimpleNamespace(st_size=len(self.data))

            def open(self, mode):
                return io.BytesIO(self.data)

        with patch("fve_inventory.Path", return_value=FakePath(bytes(512))):
            with self.assertRaisesRegex(ValueError, "missing FVE"):
                inspect("fake.img")
        header = bytearray(512)
        header[3:11] = b"-FVE-FS-"
        header[0xA0:0xB0] = SHARED_BITLOCKER_GUID.bytes_le
        struct.pack_into("<QQQ", header, 0xB0, 512, 1024, 1536)
        with patch("fve_inventory.Path", return_value=FakePath(header)):
            with self.assertRaisesRegex(ValueError, "outside image"):
                inspect("fake.img")


if __name__ == "__main__":
    unittest.main()
