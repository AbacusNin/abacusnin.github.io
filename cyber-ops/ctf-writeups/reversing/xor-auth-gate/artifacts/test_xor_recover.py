import json
from pathlib import Path
import unittest

from xor_recover import decode_case, read_case, recover


FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "example_expected.json"


class XorRecoveryTests(unittest.TestCase):
    def test_positive_fixture_and_round_trip(self):
        case = json.loads(FIXTURE.read_text(encoding="utf-8"))
        recovered = read_case(FIXTURE)
        self.assertEqual(recovered, b"admit the test user")
        self.assertEqual([byte ^ case["key"] for byte in recovered], case["expected"])

    def test_benign_table_is_not_an_auth_finding(self):
        self.assertEqual(recover([0x4b, 0x48], 0x19), b"RQ")

    def test_near_miss_length_gate_is_rejected(self):
        case = json.loads(FIXTURE.read_text(encoding="utf-8"))
        case["length"] -= 1
        with self.assertRaisesRegex(ValueError, "length gate"):
            decode_case(case)

    def test_bad_bytes_and_boolean_key_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "entries must be bytes"):
            recover([256], 23)
        with self.assertRaisesRegex(ValueError, "key must be one byte"):
            recover([1], True)


if __name__ == "__main__":
    unittest.main()
