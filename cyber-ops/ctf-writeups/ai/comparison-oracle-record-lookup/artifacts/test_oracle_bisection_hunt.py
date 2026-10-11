#!/usr/bin/env python3
"""Synthetic positive, benign, near-miss, gap, and input tests for the hunt."""

import json
import unittest
from pathlib import Path

from oracle_bisection_hunt import find_runs, parse_event


HERE = Path(__file__).parent


class HuntTests(unittest.TestCase):
    def test_fixture_matches_expected(self):
        lines = (HERE / "oracle_events.jsonl").read_text(encoding="utf-8").splitlines()
        events = [parse_event(line, index) for index, line in enumerate(lines, 1)]
        expected = json.loads((HERE / "expected_findings.json").read_text(encoding="utf-8"))
        self.assertEqual(find_runs(events), expected)

    def test_gap_breaks_sequence(self):
        lines = (HERE / "oracle_events.jsonl").read_text(encoding="utf-8").splitlines()[:5]
        events = [parse_event(line, index) for index, line in enumerate(lines, 1)]
        events[3]["parsed_time"] = events[3]["parsed_time"].replace(minute=20)
        self.assertEqual(find_runs(events), [])

    def test_timezone_required(self):
        event = {
            "timestamp": "2026-10-01T12:00:00", "actor": "a", "endpoint": "record-lookup",
            "candidate": "ID-7FFF", "response": "AFTER",
        }
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_event(json.dumps(event), 1)


if __name__ == "__main__":
    unittest.main()
