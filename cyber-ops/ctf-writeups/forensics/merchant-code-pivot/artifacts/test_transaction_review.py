"""Synthetic checks for the MCC pivot, null trap, and malformed input."""

import io
import unittest
from decimal import Decimal
from pathlib import Path

from transaction_review import load_rows, parse_rows, review

FIXTURE = Path(__file__).with_name("synthetic_transactions.csv")


class TransactionReviewTests(unittest.TestCase):
    def test_five_operations_and_negative_name_match(self):
        result = review(load_rows(FIXTURE), "3795", "5311", "8011", Decimal("50"), "hotel")
        self.assertEqual(result["q1_entity_code_count"], 2)
        self.assertEqual(result["q1_name_hits"], 0)
        self.assertEqual(result["q2_unique_merchant"], "River Goods")
        self.assertEqual(result["q3_dominant_codes"], ["3795", "8011"])
        self.assertEqual(result["q4_spend_total"], "100.30")
        self.assertEqual(result["q5_above_threshold_count"], 2)

    def test_ambiguous_merchant_category(self):
        rows = load_rows(FIXTURE)
        rows.append({"timestamp": "2026-01-04", "merchant": "Other Goods", "mcc": "5311", "amount": Decimal("1")})
        self.assertIsNone(review(rows, "3795", "5311", "8011", Decimal("50"))["q2_unique_merchant"])

    def test_bad_amount_rejected(self):
        bad = io.StringIO("timestamp,merchant,mcc,amount\n2026-01-01,A,5311,NaN\n")
        with self.assertRaisesRegex(ValueError, "invalid MCC or amount"):
            parse_rows(bad)

    def test_missing_field_rejected(self):
        bad = io.StringIO("timestamp,merchant,mcc\n2026-01-01,A,5311\n")
        with self.assertRaisesRegex(ValueError, "required columns"):
            parse_rows(bad)


if __name__ == "__main__":
    unittest.main()
