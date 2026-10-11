"""Synthetic checks for the saved Commons upload-history reviewer."""

import copy
import json
from pathlib import Path
import unittest

from commons_history_audit import review


FIXTURE = Path(__file__).parent.parent / "fixtures" / "sample_history.json"


class HistoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_oldest_visible_account_not_latest(self):
        result = review(self.doc)
        self.assertEqual(result["oldest_visible_account"], "FirstUploader")
        self.assertEqual(result["visible_versions"], 2)

    def test_hidden_earliest_account_stays_unresolved(self):
        doc = copy.deepcopy(self.doc)
        first = doc["query"]["pages"]["12"]["imageinfo"][1]
        first.pop("user")
        first["userhidden"] = ""
        self.assertEqual(review(doc)["status"], "unresolved")

    def test_continuation_is_rejected(self):
        doc = copy.deepcopy(self.doc)
        doc["continue"] = {"iicontinue": "next-page", "continue": "||"}
        with self.assertRaisesRegex(ValueError, "incomplete"):
            review(doc)

    def test_missing_file_and_wrong_repository_are_rejected(self):
        doc = copy.deepcopy(self.doc)
        doc["query"]["pages"]["12"]["missing"] = ""
        with self.assertRaisesRegex(ValueError, "missing"):
            review(doc)
        doc = copy.deepcopy(self.doc)
        doc["query"]["pages"]["12"]["imagerepository"] = "shared"
        with self.assertRaisesRegex(ValueError, "another repository"):
            review(doc)

    def test_order_does_not_depend_on_api_array_order(self):
        doc = copy.deepcopy(self.doc)
        doc["query"]["pages"]["12"]["imageinfo"].reverse()
        self.assertEqual(review(doc)["oldest_visible_account"], "FirstUploader")


if __name__ == "__main__":
    unittest.main()
