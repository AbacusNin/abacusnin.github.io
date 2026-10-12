"""Positive, benign, false-positive, near-miss, and PNG-integrity checks."""

from pathlib import Path
import unittest

from PIL import Image

from extract_green_lsb import open_image, png_chunks, render
from lsb_triage import analyze


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class LsbLabTests(unittest.TestCase):
    def test_drawn_message_is_visible_and_ranked(self):
        image, chunks = open_image(FIXTURES / "fixture_green_lsb.png")
        try:
            view, count = render(image, "G", 0)
            with Image.open(FIXTURES / "fixture_green_lsb_extracted.png") as expected:
                self.assertEqual(view.tobytes(), expected.tobytes())
            self.assertEqual(count, 2000)
            self.assertEqual(analyze(image)["review_candidate"], "G")
            self.assertEqual(chunks[-1]["type"], "IEND")
        finally:
            image.close()

    def test_benign_false_positive_and_random_payload_limit(self):
        cases = [
            ("benign_random.png", None),
            ("benign_stripes.png", "G"),
            ("near_miss_random_payload.png", None),
        ]
        for name, expected in cases:
            with self.subTest(name=name):
                image, _ = open_image(FIXTURES / name)
                try:
                    self.assertEqual(analyze(image)["review_candidate"], expected)
                finally:
                    image.close()

    def test_container_tampering_is_rejected(self):
        data = (FIXTURES / "fixture_green_lsb.png").read_bytes()
        with self.assertRaisesRegex(ValueError, "IEND"):
            png_chunks(data + b"appended")
        changed = bytearray(data)
        changed[20] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            png_chunks(changed)
        with self.assertRaisesRegex(ValueError, "truncated"):
            png_chunks(data[:-6])


if __name__ == "__main__":
    unittest.main()
