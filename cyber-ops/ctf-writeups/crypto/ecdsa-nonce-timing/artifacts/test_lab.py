import unittest
from pathlib import Path
import json
import uuid

from latency_leak_check import analyze


FIXTURES = Path(__file__).parent / "fixtures"


class TimingLab(unittest.TestCase):
    def test_leaky_controlled_benchmark(self):
        result = analyze(FIXTURES / "leaky.csv")
        self.assertTrue(result["review_leak"])
        self.assertAlmostEqual(result["slope_ns_per_bit"], 250.0, places=1)

    def test_flat_controlled_benchmark(self):
        result = analyze(FIXTURES / "flat.csv")
        self.assertFalse(result["review_leak"])
        self.assertEqual(result["slope_ns_per_bit"], 0.0)

    def test_sparse_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "At least 20"):
            analyze(FIXTURES / "sparse.csv")

    def test_stix_bundle_identifiers_and_references(self):
        bundle = json.loads((FIXTURES.parent / "technique_bundle.json").read_text(encoding="utf-8"))
        self.assertEqual(bundle["type"], "bundle")
        by_id = {obj["id"]: obj for obj in bundle["objects"]}
        self.assertEqual(len(by_id), 3)
        for identifier in [bundle["id"], *by_id]:
            kind, value = identifier.split("--", 1)
            self.assertEqual(uuid.UUID(value).version, 4)
        relation = next(obj for obj in bundle["objects"] if obj["type"] == "relationship")
        self.assertEqual(relation["relationship_type"], "mitigates")
        self.assertEqual(by_id[relation["source_ref"]]["type"], "course-of-action")
        self.assertEqual(by_id[relation["target_ref"]]["type"], "attack-pattern")


if __name__ == "__main__":
    unittest.main()
