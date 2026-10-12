import struct
import unittest
import zlib

from xor_png_review import decode, parse_png, review


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def png_fixture():
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
    pixels = zlib.compress(b"\x00\x7f")
    return bytes.fromhex("89504e470d0a1a0a") + chunk(b"IHDR", ihdr) + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")


class ReviewTests(unittest.TestCase):
    def test_periodic_key_positive(self):
        raw = png_fixture()
        encrypted = decode(raw, b"labkey")
        result, recovered = review(encrypted)
        self.assertTrue(result["review_lead"])
        self.assertEqual(recovered, raw)
        self.assertEqual(result["key_length"], 6)

    def test_long_key_requires_supplied_candidate(self):
        raw = png_fixture()
        encrypted = decode(raw, b"fixtureLongKey123")
        self.assertFalse(review(encrypted)[0]["review_lead"])
        self.assertTrue(review(encrypted, b"fixtureLongKey123")[0]["review_lead"])

    def test_benign_random_blob(self):
        self.assertFalse(review(bytes(range(128)))[0]["review_lead"])

    def test_crc_near_miss(self):
        raw = bytearray(png_fixture())
        raw[30] ^= 1
        self.assertFalse(review(decode(raw, b"labkey"))[0]["review_lead"])

    def test_structural_checks(self):
        raw = png_fixture()
        self.assertEqual(parse_png(raw)["chunks"], ["IHDR", "IDAT", "IEND"])
        with self.assertRaises(ValueError):
            parse_png(raw + b"trailing")


if __name__ == "__main__":
    unittest.main()
