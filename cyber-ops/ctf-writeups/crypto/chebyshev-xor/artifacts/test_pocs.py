"""Local math equivalence and static-review positive, benign, and near-miss tests."""

import unittest

from chebyshev_lab import P, chebyshev_fast, chebyshev_slow, keystream_bytes, matrix_reference, xor_cycle
from linear_recurrence import linrec
from recurrence_review import inspect


class Checks(unittest.TestCase):
    def test_reference_and_matrix_agree(self):
        for n in (0, 1, 2, 3, 5, 17, 100, 1000, 12345):
            self.assertEqual(chebyshev_fast(0x1337C0DE, n), chebyshev_slow(0x1337C0DE, n))
            self.assertEqual(chebyshev_fast(0x1337C0DE, n), matrix_reference(0x1337C0DE, n))
            self.assertEqual(chebyshev_fast(0x1337C0DE, n), linrec([2 * 0x1337C0DE, -1], [1, 0x1337C0DE], n, P))
        self.assertEqual(chebyshev_fast(0x1337C0DE, 10**25), matrix_reference(0x1337C0DE, 10**25))
        self.assertEqual(linrec([1, 1], [0, 1], 20, P), 6765)

    def test_35_byte_cycle_and_truncation(self):
        plain = b"flag{synthetic_chebyshev_case_123}\n"
        self.assertEqual(len(plain), 35)
        key = keystream_bytes(0x1337C0DE, 10**25)
        self.assertLessEqual(len(key), 32)
        cipher = xor_cycle(plain, key)
        self.assertEqual(xor_cycle(cipher, key), plain)
        self.assertEqual(len(bytes(c ^ k for c, k in zip(cipher, key))), len(key))

    def test_static_positive_benign_near_miss(self):
        positive = "p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f\nnew = (2 * amp * current - prev) % p\n"
        benign = "p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f\nnew = (current + prev) % p\n"
        near_miss = "p = 97\nnew = (2 * amp * current - prev) % p\n"
        self.assertEqual(len(inspect(positive)), 1)
        self.assertEqual(inspect(benign), [])
        self.assertEqual(inspect(near_miss), [])

    def test_bounds(self):
        with self.assertRaises(ValueError):
            chebyshev_fast(2, -1)
        with self.assertRaises(ValueError):
            chebyshev_slow(2, 100001)
        with self.assertRaises(ValueError):
            xor_cycle(b"abc", b"")


if __name__ == "__main__":
    unittest.main()
