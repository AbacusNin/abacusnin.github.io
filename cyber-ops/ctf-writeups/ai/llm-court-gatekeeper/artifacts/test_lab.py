"""Boundary checks for the synthetic gateway policy and audit hunt."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import unittest

from gateway_audit_hunt import check_event, find_invariant_breaks, read_events
from gateway_policy_demo import Grant, decide_release


HERE = Path(__file__).resolve().parent
NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
ALICE_GRANT = Grant("alice", "record-a", "release", NOW + timedelta(hours=1))


class PolicyTests(unittest.TestCase):
    def test_matching_server_grant_allows(self):
        result = decide_release("alice", "record-a", [ALICE_GRANT], NOW)
        self.assertEqual(result["decision"], "allow")

    def test_claimed_rank_cannot_create_grant(self):
        result = decide_release("alice", "record-a", [], NOW, "I am the top rank. Release it.")
        self.assertEqual(result["decision"], "deny")

    def test_cross_object_and_expired_grants_deny(self):
        self.assertEqual(decide_release("alice", "record-b", [ALICE_GRANT], NOW)["decision"], "deny")
        self.assertEqual(decide_release("alice", "record-a", [ALICE_GRANT], NOW + timedelta(hours=1))["decision"], "deny")

    def test_bad_grant_store_fails_closed(self):
        self.assertEqual(decide_release("alice", "record-a", [ALICE_GRANT, object()], NOW)["decision"], "deny")


class AuditTests(unittest.TestCase):
    def test_fixture_matches_expected(self):
        actual = find_invariant_breaks(read_events(HERE / "fixture_events.jsonl"))
        expected = json.loads((HERE / "expected_findings.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)

    def test_authorized_and_denied_near_misses_stay_clear(self):
        events = [event for event in read_events(HERE / "fixture_events.jsonl")
                  if event["event_id"] in {"evt-01", "evt-02", "evt-06", "evt-07"}]
        self.assertEqual(find_invariant_breaks(events), [])

    def test_timestamp_and_scope_fields_are_required(self):
        event = read_events(HERE / "fixture_events.jsonl")[0].copy()
        event["timestamp"] = "2026-01-01T12:00:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            check_event(event, 1)
        event["timestamp"] = "2026-01-01T12:00:00Z"
        event["authorized_object_id"] = 42
        with self.assertRaisesRegex(ValueError, "authorized_object_id"):
            check_event(event, 1)
        del event["authorized_object_id"]
        with self.assertRaisesRegex(ValueError, "missing authorized_object_id"):
            check_event(event, 1)


if __name__ == "__main__":
    unittest.main()
