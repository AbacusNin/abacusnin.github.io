"""Synthetic positive, benign duplicate, near miss, and malformed-input checks."""

import json
from io import StringIO
import unittest
from pathlib import Path

from signature_r_audit import audit, audit_records


FIXTURE = Path(__file__).with_name("synthetic_signing.jsonl")


class AuditTests(unittest.TestCase):
    def test_fixture_has_one_distinct_hash_lead(self):
        leads = audit(FIXTURE)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["assessment"], "urgent_review")
        self.assertEqual((leads[0]["first_line"], leads[0]["second_line"]), (1, 3))

    def test_identical_retry_is_benign(self):
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        self.assertEqual(self._audit_lines(lines[:2]), [])

    def test_same_r_different_key_is_not_grouped(self):
        lines = FIXTURE.read_text(encoding="utf-8").splitlines()
        self.assertEqual(self._audit_lines([lines[0], lines[3]]), [])

    def test_malformed_signature_is_rejected(self):
        event = json.loads(FIXTURE.read_text(encoding="utf-8").splitlines()[0])
        event["r"] = "bad"
        with self.assertRaisesRegex(ValueError, "32-byte hex"):
            self._audit_lines([json.dumps(event)])

    def _audit_lines(self, lines):
        return audit_records(StringIO("\n".join(lines) + "\n"))


if __name__ == "__main__":
    unittest.main()
