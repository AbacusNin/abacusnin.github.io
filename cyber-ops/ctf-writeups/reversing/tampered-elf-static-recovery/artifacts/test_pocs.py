import unittest

from elf_substitution_review import inspect


def make_elf_like(magic=b"\x7fELF", fill=b"\x00"):
    ident = magic + bytes([2, 1, 1])
    return ident + fill * (4096 - len(ident))


class ReviewTests(unittest.TestCase):
    def test_synthetic_corrupt_candidate(self):
        raw = make_elf_like()
        altered = raw.replace(b"\x00", b" ")
        altered = altered[:3] + b"K" + altered[4:]
        result = inspect(altered)
        self.assertTrue(result["review_lead"])
        self.assertEqual(result["zero_count"], 0)
        self.assertEqual(result["prefix_hex"], "7f454c4b")

    def test_valid_elf_like_file_is_not_flagged(self):
        self.assertFalse(inspect(make_elf_like())["review_lead"])

    def test_header_only_change_is_near_miss(self):
        result = inspect(make_elf_like(magic=b"\x7fELK"))
        self.assertFalse(result["review_lead"])
        self.assertGreater(result["zero_count"], 0)

    def test_many_to_one_transform(self):
        self.assertEqual(b"\x00".replace(b"\x00", b" "), b" ")
        self.assertEqual(b" ".replace(b"\x00", b" "), b" ")
        self.assertEqual(bytes.fromhex("bf6d000000").replace(b"\x00", b" "),
                         bytes.fromhex("bf6d202020"))

    def test_short_file_is_not_flagged(self):
        self.assertFalse(inspect(b"\x7fELK\x02\x01\x01" + b" " * 30)["review_lead"])


if __name__ == "__main__":
    unittest.main()
