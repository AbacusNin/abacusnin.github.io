"""Synthetic positive and rejection tests for the bounded affine probe."""

import unittest

import gl2_affine_probe as probe


class ProbeTests(unittest.TestCase):
    key = "matrixKEY{}"
    plain = "CTF{THE_MATRIX_IS_LINEAR}"

    def test_full_rank_recovers_synthetic_key(self):
        cipher = probe.encrypt(self.key, self.plain)
        _, _, rows = probe.affine_model(len(self.plain))
        positions = probe.independent_positions(rows, probe.Q)
        recovered, basis, rank = probe.crib_system(cipher, {i: self.plain[i] for i in positions})
        self.assertEqual((probe.chars(recovered), rank, len(basis)), (self.key, 11, 0))
        self.assertEqual(probe.decrypt(self.key, cipher), self.plain)

    def test_seven_cribs_leave_multiple_reencrypting_candidates(self):
        cipher = probe.encrypt(self.key, self.plain)
        _, _, rows = probe.affine_model(len(self.plain))
        positions = probe.independent_positions(rows, 7)
        one, basis, rank = probe.crib_system(cipher, {i: self.plain[i] for i in positions})
        other = [(a + b) % probe.P for a, b in zip(one, basis[0])]
        plain_one = probe.decrypt(probe.chars(one), cipher)
        plain_other = probe.decrypt(probe.chars(other), cipher)
        self.assertEqual((rank, len(basis), probe.P ** len(basis)), (7, 4, 20151121))
        self.assertNotEqual(plain_one, plain_other)
        self.assertEqual(probe.encrypt(probe.chars(one), plain_one), cipher)
        self.assertEqual(probe.encrypt(probe.chars(other), plain_other), cipher)

    def test_conflicting_crib_is_rejected(self):
        cipher = probe.encrypt(self.key, self.plain)
        _, _, rows = probe.affine_model(len(self.plain))
        positions = probe.independent_positions(rows, probe.Q)
        crib = {i: self.plain[i] for i in positions}
        changed = self.plain[0]
        crib[0] = "A" if changed != "A" else "B"
        # Add the original value at a dependent position if index zero was chosen.
        if 0 in positions:
            for index in range(len(self.plain)):
                if index not in positions:
                    crib[index] = self.plain[index]
                    break
        with self.assertRaises(ValueError):
            probe.crib_system(cipher, crib)

    def test_invalid_domain_and_positions_are_rejected(self):
        with self.assertRaises(ValueError):
            probe.encrypt(self.key, "a b")
        with self.assertRaises(ValueError):
            probe.encrypt("short", self.plain)
        with self.assertRaises(ValueError):
            probe.crib_system(probe.encrypt(self.key, self.plain), {False: "A"})


if __name__ == "__main__":
    unittest.main()
