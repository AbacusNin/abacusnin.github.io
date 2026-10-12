import unittest
from progressive_shift_review import candidates, decode


SYNTHETIC_CIPHERTEXT = "fkyd{Kilakydbnx_Cqqmz_Glrieq_Btvgidv_Iskf}"
SYNTHETIC_PLAINTEXT = "flag{Positional_Shift_Cipher_Example_Text}"


class ProgressiveShiftTests(unittest.TestCase):
    def test_positive_with_crib_across_separator(self):
        found = candidates(SYNTHETIC_CIPHERTEXT, "flag{Pos")
        self.assertEqual(found, [{"basis": "absolute", "step": 1,
                                  "plaintext": SYNTHETIC_PLAINTEXT}])

    def test_short_crib_expected_false_positive(self):
        found = candidates(SYNTHETIC_CIPHERTEXT, "flag{")
        self.assertIn("letters", {item["basis"] for item in found})
        self.assertIn("absolute", {item["basis"] for item in found})

    def test_benign_nonmatch(self):
        self.assertEqual(candidates("hello_world", "flag{"), [])

    def test_near_miss_wrong_basis(self):
        self.assertNotEqual(decode(SYNTHETIC_CIPHERTEXT, 1, "letters"),
                            SYNTHETIC_PLAINTEXT)

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            candidates("hello\nworld", "hello")


if __name__ == "__main__":
    unittest.main()
