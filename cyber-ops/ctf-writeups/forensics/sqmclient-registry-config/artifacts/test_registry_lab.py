from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import regxml_review
import registry_event_review


FIXTURES = Path(__file__).parent / "fixtures"


class SnapshotTests(unittest.TestCase):
    def test_full_case_pattern_and_lengths(self):
        result = regxml_review.review(FIXTURES / "case.xml")
        self.assertTrue(result["complete_case_pattern"])
        keys = {row["key_suffix"]: row for row in result["keys"]}
        self.assertEqual(keys["microsoft\\sqmclient"]["types_and_lengths"]["Token"]["decoded_bytes"], 32)
        self.assertEqual(keys["classes\\installer"]["types_and_lengths"]["Upload"]["decoded_bytes"], 34)

    def test_benign_snapshot(self):
        result = regxml_review.review(FIXTURES / "benign.xml")
        self.assertFalse(result["complete_case_pattern"])
        self.assertTrue(all(not row["matched_names"] for row in result["keys"]))

    def test_one_value_is_a_near_miss(self):
        result = regxml_review.review(FIXTURES / "near_miss.xml")
        self.assertFalse(result["complete_case_pattern"])
        self.assertEqual(result["keys"][0]["matched_names"], ["Token"])

    def test_truncated_xml_fails_closed(self):
        with self.assertRaises(ET.ParseError):
            regxml_review.review(FIXTURES / "truncated.xml")

    def test_dtd_is_rejected(self):
        with self.assertRaises(ValueError):
            regxml_review.review(FIXTURES / "doctype.xml")


class EventTests(unittest.TestCase):
    def test_full_case_and_near_miss_on_different_hosts(self):
        reports = {row["host"]: row for row in registry_event_review.review(FIXTURES / "events.jsonl")["hosts"]}
        self.assertTrue(reports["LAB-CASE"]["complete_case_pattern"])
        self.assertFalse(reports["LAB-NEAR"]["complete_case_pattern"])
        self.assertNotIn("LAB-BENIGN", reports)

    def test_malformed_event_is_rejected(self):
        with self.assertRaises(ValueError):
            registry_event_review.review(FIXTURES / "malformed.jsonl")


if __name__ == "__main__":
    unittest.main()
