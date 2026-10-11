"""Meaningful positive, benign, near-miss, and boundary checks for the lab."""

from datetime import timedelta
import json
from pathlib import Path
import unittest

from make_fixture import events, make_event
from protocol_oracle_hunt import find_oracle_patterns, parse_time, read_events


class OracleHuntTests(unittest.TestCase):
    def test_fixture_has_only_one_lead(self):
        observed = find_oracle_patterns(read_events(Path(__file__).with_name("fixture_events.jsonl")))
        expected = json.loads(Path(__file__).with_name("expected_findings.json").read_text(encoding="utf-8"))
        self.assertEqual(observed, expected)
        self.assertEqual(len(events()), 62)

    def test_benign_and_near_miss_remain_clear(self):
        controls = [row for row in events() if row.get("TokenHash") in ("synthetic-stale-client", "synthetic-short-burst")]
        for row in controls:
            row["_time"] = parse_time(row["TimeGenerated"], 1)
        self.assertEqual(find_oracle_patterns(controls), [])

    def test_ten_minute_boundary_is_inclusive(self):
        rows = [make_event(i * 30, "boundary-token", i % 5) for i in range(20)]
        for row in rows:
            row["_time"] = parse_time(row["TimeGenerated"], 1)
        self.assertEqual(len(find_oracle_patterns(rows)), 1)
        rows[-1]["_time"] = rows[0]["_time"] + timedelta(minutes=10, seconds=1)
        self.assertEqual(find_oracle_patterns(rows), [])

    def test_naive_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            parse_time("2026-01-01T00:00:00", 1)


if __name__ == "__main__":
    unittest.main()
