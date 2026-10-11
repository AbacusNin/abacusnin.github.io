"""Synthetic checks for the PNG metadata scanner and suffix recovery tool."""

import hashlib
import struct
import sys
import unittest
import zlib
from pathlib import Path

from png_xmp_audit import PNG_MAGIC, scan
from suffix_crack import crack, load_hashes


HERE = Path(__file__).parent
FIXTURES = HERE.parent / "fixtures"
WORDS = ("ceremony042", "vows173", "bouquet999")
DIGESTS = tuple(hashlib.blake2b(word.encode("ascii")).hexdigest() for word in WORDS)


def chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def png(comment: str | None = None, other: str | None = None, compressed: bool = False) -> bytes:
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    fields = []
    if comment is not None:
        fields.append(f"<exif:UserComment>{comment}</exif:UserComment>")
    if other is not None:
        fields.append(f"<test:Other>{other}</test:Other>")
    xml = ('<x:xmpmeta xmlns:x="adobe:ns:meta/" '
           'xmlns:exif="http://ns.adobe.com/exif/1.0/" '
           'xmlns:test="urn:synthetic:test">' + "".join(fields) + '</x:xmpmeta>').encode()
    payload = b"XML:com.adobe.xmp\x00" + (b"\x01\x00" if compressed else b"\x00\x00") + b"\x00\x00"
    payload += zlib.compress(xml) if compressed else xml
    return PNG_MAGIC + ihdr + chunk(b"iTXt", payload) + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00")) + chunk(b"IEND", b"")


class AuditTests(unittest.TestCase):
    def test_positive_and_redacted_default(self):
        result = scan(png("-".join(DIGESTS)))
        self.assertEqual(result["candidate_512_bit_values"], 3)
        self.assertTrue(result["three_value_pattern"])
        self.assertNotIn("digests", result)
        self.assertEqual(scan(png("-".join(DIGESTS), compressed=True))["candidate_512_bit_values"], 3)

    def test_benign_and_near_miss(self):
        self.assertEqual(scan(png(other=DIGESTS[0]))["candidate_512_bit_values"], 0)
        self.assertEqual(scan(png(comment=DIGESTS[0][:-1]))["candidate_512_bit_values"], 0)

    def test_bad_crc_is_rejected(self):
        data = bytearray(png("-".join(DIGESTS)))
        data[-5] ^= 1
        with self.assertRaises(ValueError):
            scan(bytes(data))


class RecoveryTests(unittest.TestCase):
    def test_synthetic_fixture_and_three_targets(self):
        hashes = load_hashes(FIXTURES / "sample_hashes.txt", "blake2b")
        self.assertEqual(hashes, list(DIGESTS))
        words = (FIXTURES / "sample_words.txt").read_text().splitlines()
        recovered, attempts, capped = crack(words, hashes)
        self.assertEqual(recovered, list(WORDS))
        self.assertFalse(capped)
        self.assertLessEqual(attempts, 4000)

    def test_unresolved_and_cap(self):
        missing = hashlib.blake2b(b"absent123").hexdigest()
        result, _, capped = crack(["vows"], [missing])
        self.assertEqual(result, [None])
        self.assertFalse(capped)
        result, attempts, capped = crack(["vows"], [missing], max_candidates=100)
        self.assertEqual(result, [None])
        self.assertEqual(attempts, 100)
        self.assertTrue(capped)


if __name__ == "__main__":
    if "--generate-fixture" in sys.argv:
        (FIXTURES / "sample_hashes.txt").write_text("\n".join(DIGESTS) + "\n", encoding="ascii")
        sys.argv.remove("--generate-fixture")
    unittest.main()
