"""Synthetic positive, benign, and near-miss checks for structure and XOR review."""

import struct
import unittest

from icns_structure import inspect
from structural_xor_lab import KeyRegion, build_key, crib_drag, recover, xor_cycle, zero_ciphertext_tail


class LocalChecks(unittest.TestCase):
    def test_structural_positive_benign_near_miss(self):
        element = b"icp4" + struct.pack(">I", 11) + b"abc"
        valid = b"icns" + struct.pack(">I", 8 + len(element)) + element
        self.assertTrue(inspect(valid)["valid_structure"])
        self.assertFalse(inspect(b"icns" + struct.pack(">I", 169) + b"bait")["valid_structure"])
        self.assertIsNone(inspect(b"ordinary text")["valid_structure"])
        self.assertFalse(inspect(b"icns" + struct.pack(">I", 12) + b"bait")["valid_structure"])

    def test_three_regions_crib_and_zero_cipher_tail(self):
        key = b"icns\x01" + b"nam\x06ab" + b"lzmaX"
        self.assertEqual(len(key), 16)
        plain = b"flag{synthetic_structural_xor_case}"
        self.assertEqual(len(plain), 35)
        cipher = xor_cycle(plain, key) + b"\x00" * 4
        prefix = b"icns" + b"\x01" + b"nam\x06ab" + b"lzmaX"
        artifact = prefix + b":" + cipher
        regions = [KeyRegion("outer", 0, 5), KeyRegion("inner", 5, 6), KeyRegion("stream", 11, 5)]
        self.assertEqual(build_key(artifact, regions), key)
        self.assertEqual(recover(artifact, regions, 17, len(cipher))[:len(plain)], plain)
        hits = crib_drag(b":" + cipher, b"flag{")
        self.assertTrue(any(offset == 1 and fragment == key[:5] for offset, fragment, _ in hits))
        self.assertTrue(zero_ciphertext_tail(cipher, key, len(plain)))
        self.assertFalse(zero_ciphertext_tail(cipher, key, len(plain) - 1))

    def test_bounds(self):
        with self.assertRaises(ValueError):
            build_key(b"short", [KeyRegion("outside", 2, 8)])
        with self.assertRaises(ValueError):
            xor_cycle(b"data", b"")
        with self.assertRaises(ValueError):
            recover(b"data", [KeyRegion("key", 0, 1)], 3, 3)


if __name__ == "__main__":
    unittest.main()
