import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xor_anchor_scan import decode_hex, recover_prefix_key, scan, xor_bytes


class XorReviewTests(unittest.TestCase):
    def test_source_synthetic_example(self):
        data = decode_hex("040e0305391a0d101d071a030f120e073f\n")
        self.assertEqual(recover_prefix_key(data, b"FLAG{"), 0x42)
        self.assertEqual(xor_bytes(data, 0x42), b"FLAG{XOR_EXAMPLE}")

    def test_encoded_anchor_match(self):
        marker = b"lab-control.example"
        sample = b"MZ" + b"\0" * 8 + xor_bytes(marker, 0x42)
        self.assertEqual(scan(sample, [marker]),
                         [{"offset": 10, "key_hex": "42", "anchor_ascii": "lab-control.example"}])

    def test_benign_and_near_miss(self):
        marker = b"lab-control.example"
        self.assertEqual(scan(b"MZ and ordinary program data", [marker]), [])
        altered = bytearray(xor_bytes(marker, 0x42))
        altered[-1] ^= 1
        self.assertEqual(scan(bytes(altered), [marker]), [])

    def test_wrong_anchor_and_bad_input(self):
        data = decode_hex("040e0305391a0d101d071a030f120e073f")
        self.assertIsNone(recover_prefix_key(data, b"WRONG"))
        for bad in ("abc", "zz", ""):
            with self.assertRaises(ValueError):
                decode_hex(bad)
        with self.assertRaises(ValueError):
            scan(b"data", [b"short"])


if __name__ == "__main__":
    unittest.main()
