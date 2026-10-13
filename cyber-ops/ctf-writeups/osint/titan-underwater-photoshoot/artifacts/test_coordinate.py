"""Run the coordinate check against one synthetic in-bounds example and useful near misses."""

import unittest
from decimal import Decimal

from check_coordinate import check


BOUNDS = tuple(map(Decimal, ("7.39", "7.52", "98.25", "98.35")))


class CoordinateTests(unittest.TestCase):
    def test_in_bounds_example(self):
        result = check("7.500000", "98.300000", BOUNDS)
        self.assertEqual(result["flag"], "scriptCTF{7.500000_98.300000}")
        self.assertTrue(result["in_bounds"])

    def test_outside_bound_stays_a_candidate(self):
        result = check("7.520001", "98.300000", BOUNDS)
        self.assertFalse(result["in_bounds"])
        self.assertEqual(result["flag"], "scriptCTF{7.520001_98.300000}")

    def test_wrong_hemisphere_near_miss(self):
        result = check("-7.500000", "98.300000", BOUNDS)
        self.assertFalse(result["in_bounds"])

    def test_coordinate_domain(self):
        with self.assertRaises(ValueError):
            check("98.300000", "7.500000")

    def test_precision_and_nonfinite(self):
        for value in ("7.5000001", "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                check(value, "98.300000")


if __name__ == "__main__":
    unittest.main()
