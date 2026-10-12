"""Synthetic representation-triage cases, with no challenge content."""

import unittest
from pathlib import Path

from radix_triage import analyze_line, atbash, audit_text, decode, infer_radix


FIXTURE = Path(__file__).with_name("synthetic_messages.txt")


class RadixTests(unittest.TestCase):
    def test_base9_positive(self):
        tokens = FIXTURE.read_text(encoding="utf-8").splitlines()[0].split()
        self.assertEqual(infer_radix(tokens), 9)
        self.assertEqual(decode(tokens, 9), "24 keys stored in the archive")
        lead = analyze_line(" ".join(tokens), 1)
        self.assertEqual([item["radix"] for item in lead["printable_candidates"]], [9])

    def test_decimal_ascii_is_ambiguous(self):
        lead = audit_text(FIXTURE.read_text(encoding="utf-8"))[1]
        self.assertEqual([item["radix"] for item in lead["printable_candidates"]], [9, 10])
        self.assertEqual(lead["assessment"], "review_representation_not_intent")

    def test_nine_digit_near_miss_has_no_lead(self):
        self.assertIsNone(analyze_line(FIXTURE.read_text(encoding="utf-8").splitlines()[2], 3))

    def test_invalid_token_and_atbash(self):
        with self.assertRaises(ValueError):
            decode(["019"], 9)
        text = "gsv wilk klrmg rh xlmurinvw"
        self.assertEqual(atbash(atbash(text)), text)
        self.assertEqual(atbash(text), "the drop point is confirmed")


if __name__ == "__main__":
    unittest.main()
