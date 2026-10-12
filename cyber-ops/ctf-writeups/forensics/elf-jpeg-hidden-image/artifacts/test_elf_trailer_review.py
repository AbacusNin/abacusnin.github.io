import struct
import unittest
from elf_trailer_review import review, u64_elf_extent


def sample(section_after_table=False, embedded_jpeg=False):
    end = 0x210 if section_after_table else 0x140
    data = bytearray(end)
    data[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<HHIQQQIHHHHHH", data, 16,
                     2, 62, 1, 0, 0x40, 0x100, 0, 64, 56, 1, 64, 1, 0)
    struct.pack_into("<IIQQQQQQ", data, 0x40, 1, 4, 0x80, 0, 0, 0x40, 0x40, 8)
    if section_after_table:
        struct.pack_into("<IIQQQQIIQQ", data, 0x100,
                         0, 1, 0, 0, 0x200, 16, 0, 0, 1, 0)
        if embedded_jpeg:
            data[0x200:0x20a] = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    return bytes(data)


class ReviewTests(unittest.TestCase):
    def test_positive_appended_jfif(self):
        original = sample()
        changed = original + b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"X" * 20
        result = review(original, changed)
        self.assertTrue(result["same_baseline_prefix"])
        self.assertEqual(result["suspect_unmapped_tail_bytes"], 30)
        self.assertTrue(result["tail_starts_jfif"])

    def test_benign_unchanged(self):
        original = sample()
        result = review(original, original)
        self.assertEqual(result["assessment"], "no_unmapped_tail")

    def test_near_miss_section_after_table(self):
        original = sample(section_after_table=True, embedded_jpeg=True)
        self.assertEqual(u64_elf_extent(original), 0x210)
        result = review(original, original)
        self.assertEqual(result["suspect_unmapped_tail_bytes"], 0)

    def test_malformed_header(self):
        with self.assertRaises(ValueError):
            u64_elf_extent(b"\x7fELF\x02\x01" + b"\x00" * 10)


if __name__ == "__main__":
    unittest.main()
