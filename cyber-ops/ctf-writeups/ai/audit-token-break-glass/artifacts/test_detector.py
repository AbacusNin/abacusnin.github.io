"""Check reported signals, controls, and the fifteen-minute boundary."""

import json
from pathlib import Path
import unittest

from detect_break_glass import analyze, load_events, validate_event


HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "expected-results.json").read_text(encoding="utf-8"))


class DetectorTests(unittest.TestCase):
    def test_supplied_synthetic_fixture(self):
        actual = analyze(load_events(HERE / "fixtures" / "custodian-audit-sample.jsonl"))
        self.assertEqual(actual, EXPECTED["case_fixture"])

    def test_near_misses_and_boundary(self):
        actual = analyze(load_events(HERE / "fixtures" / "edge-cases.jsonl"))
        self.assertEqual(actual, EXPECTED["edge_fixture"])
        self.assertFalse(any(item["session_id"] in {"sess-near-window", "sess-attest", "sess-benign-mistype"}
                             for item in actual["findings"]))

    def test_invalid_time_and_missing_denial_reason(self):
        event = {"ts": "2026-01-10T12:00:00", "session_id": "s", "event_type": "break_glass_attempt",
                 "result": "deny", "deny_reason": "MRN mismatch"}
        with self.assertRaisesRegex(ValueError, "timezone"):
            validate_event(event, 1)
        event["ts"] += "Z"
        del event["deny_reason"]
        with self.assertRaisesRegex(ValueError, "deny_reason"):
            validate_event(event, 1)


if __name__ == "__main__":
    unittest.main()
