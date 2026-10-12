"""Check the informational Sigma selection against invented normalized events."""

import json
import unittest
from pathlib import Path

import yaml
from sigma.collection import SigmaCollection

HERE = Path(__file__).parent


class CategoryReviewTests(unittest.TestCase):
    def test_rule_parses_and_selects_only_configured_codes(self):
        source = (HERE / "category_review.yml").read_text(encoding="utf-8")
        SigmaCollection.from_yaml(source)
        rule = yaml.safe_load(source)
        self.assertEqual(rule["level"], "informational")
        selected = set(rule["detection"]["selection"]["mcc"])
        events = [json.loads(line) for line in (HERE / "synthetic_category_events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual([(event["case"], event["mcc"] in selected) for event in events],
                         [(event["case"], event["expected"]) for event in events])


if __name__ == "__main__":
    unittest.main()
