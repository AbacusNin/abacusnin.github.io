"""Small offline regression checks for the two defensive proof-of-concept tools."""

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from http_capture_triage import inspect
from web_enum_detector import analyze


def row(seconds, source, path, status, host="example.test"):
    when = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return {"ts": when.isoformat(), "src_ip": source, "host": host, "path": path, "status": status}


class CaptureTests(unittest.TestCase):
    def test_synthetic_pcap(self):
        expected = json.loads((ROOT / "fixtures/expected_capture.json").read_text())
        actual = json.loads(json.dumps(inspect((ROOT / "fixtures/sample_http.pcap").read_bytes())))
        self.assertEqual(actual, expected)

    def test_truncation_and_wrong_format(self):
        data = (ROOT / "fixtures/sample_http.pcap").read_bytes()
        with self.assertRaisesRegex(ValueError, "truncated|invalid"):
            inspect(data[:-1])
        with self.assertRaisesRegex(ValueError, "classic pcap"):
            inspect(b"not a pcap")


class DetectorTests(unittest.TestCase):
    def test_positive_fixture_and_decoy(self):
        rows = [json.loads(line) for line in (ROOT / "fixtures/web_events.jsonl").read_text().splitlines()]
        expected = json.loads((ROOT / "fixtures/expected_detection.json").read_text())
        findings = analyze(rows, threshold=3)
        self.assertEqual(len(findings), 1)
        for key, value in expected.items():
            self.assertEqual(findings[0][key], value)

    def test_near_misses(self):
        base = [row(i, "192.0.2.1", f"/demo_{i}", 404) for i in range(3)]
        cases = [
            base + [row(4, "192.0.2.2", "/demo_3", 200)],
            base + [row(4, "192.0.2.1", "/demo_3", 200, host="other.test")],
            base + [row(4, "192.0.2.1", "/other_3", 200)],
            base + [row(301, "192.0.2.1", "/demo_3", 200)],
            [row(i, "192.0.2.1", "/demo_0", 404) for i in range(3)] + [row(4, "192.0.2.1", "/demo_3", 200)],
            [row(0, "192.0.2.1", "/demo_3", 200)] + base,
        ]
        for events in cases:
            with self.subTest(events=events):
                self.assertEqual(analyze(events, threshold=3), [])

    def test_unsorted_log_rejected(self):
        with self.assertRaisesRegex(ValueError, "sorted"):
            analyze([row(2, "192.0.2.1", "/demo_2", 404), row(1, "192.0.2.1", "/demo_1", 404)])


if __name__ == "__main__":
    unittest.main()
