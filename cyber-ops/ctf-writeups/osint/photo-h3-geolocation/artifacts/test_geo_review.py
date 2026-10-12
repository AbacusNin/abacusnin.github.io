import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from geo_path_review import angular_delta, bearing_deg, evaluate
from image_exposure_review import inspect_image


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "path_start": [0.001, -0.001],
            "path_end": [-0.001, -0.001],
            "subject": [0, 0],
            "heading_deg": 90,
            "subject_offset_window_deg": [-10, 10],
            "aux_path_fraction_window": [0.4, 0.6],
            "step_m": 10,
            "h3_resolution": 11,
        }

    def test_left_of_west_heading_is_southwest(self):
        self.assertEqual(angular_delta(225, 270), -45)
        self.assertEqual(angular_delta(315, 270), 45)
        self.assertAlmostEqual(bearing_deg((0, 0), (0, -1)), 270, places=3)

    def test_constrained_path_and_cell_deduplication(self):
        result = evaluate(self.config, lambda lat, lon, resolution: "synthetic-cell")
        self.assertGreater(result["matching_points"], 0)
        self.assertEqual(result["candidate_cells"], ["synthetic-cell"])
        self.assertTrue(all(0.4 <= x["fraction"] <= 0.6 for x in result["matches"]))

    def test_near_miss_and_invalid_path(self):
        config = dict(self.config, subject_offset_window_deg=[30, 40])
        self.assertEqual(evaluate(config)["matching_points"], 0)
        config = dict(self.config, path_end=self.config["path_start"])
        with self.assertRaises(ValueError):
            evaluate(config)


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(__file__).parent
        self.sample = self.folder / "_synthetic_test.jpg"

    def tearDown(self):
        self.sample.unlink(missing_ok=True)

    def test_gps_exif_detected(self):
        exif = Image.Exif()
        exif[34853] = {1: "N", 2: (40, 0, 0), 3: "W", 4: (105, 0, 0)}
        Image.new("RGB", (4, 4), "blue").save(self.sample, exif=exif)
        self.assertTrue(inspect_image(self.sample)["gps_exif_present"])

    def test_benign_image_still_needs_visual_review(self):
        Image.new("RGB", (4, 4), "blue").save(self.sample)
        result = inspect_image(self.sample)
        self.assertFalse(result["gps_exif_present"])
        self.assertTrue(result["visual_review_required"])

    def test_bad_file_rejected(self):
        self.sample.write_text("not an image", encoding="utf-8")
        with self.assertRaises(ValueError):
            inspect_image(self.sample)


if __name__ == "__main__":
    unittest.main()
