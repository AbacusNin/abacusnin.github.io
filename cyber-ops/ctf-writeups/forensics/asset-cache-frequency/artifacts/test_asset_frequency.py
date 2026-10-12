"""Synthetic positive, benign, and ambiguous asset-cache checks."""

from io import BytesIO
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from asset_frequency import ScanError, scan_directory, scan_stream


def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data)))


def png(label, size=128):
    """Make a valid one-pixel PNG with a harmless label and fixed byte length."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    image = _chunk(b"IDAT", zlib.compress(b"\x00\x20\x40\x60"))
    end = _chunk(b"IEND", b"")
    text_length = size - len(signature + ihdr + image + end) - 12
    value = b"label\x00" + label.encode("ascii")
    if text_length < len(value):
        raise ValueError("fixture too small")
    result = signature + ihdr + image + _chunk(
        b"tEXt", value + b" " * (text_length - len(value))) + end
    assert len(result) == size
    return result


class AssetFrequencyTests(unittest.TestCase):
    def test_stream_finds_one_singleton_among_repeated_assets(self):
        records = [png("road")] * 3 + [png("water")] * 3 + [png("caption")]
        result = scan_stream(BytesIO(b"".join(records)), file_size=128,
                             expected_count=7, max_bytes=1024,
                             max_distinct=10, min_repeat=3)
        self.assertEqual(result["frequency_histogram"], {"1": 1, "3": 2})
        self.assertEqual(result["rare_candidates"][0]["locations"], [6])
        self.assertEqual(result["assessment"], "review_candidates")

    def test_directory_repeats_without_rare_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i, label in enumerate(("road", "road", "road", "water", "water", "water")):
                (root / f"{i}.png").write_bytes(png(label))
            result = scan_directory(root, max_files=10, max_bytes=1024,
                                    max_file_bytes=128, max_distinct=10,
                                    min_repeat=3, suffix=".png")
            self.assertEqual(result["rare_candidates"], [])
            self.assertEqual(result["assessment"], "no_rare_candidates")

    def test_legitimate_new_tile_is_still_a_review_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for i, label in enumerate(("road", "road", "road", "new_vendor_tile")):
                (root / f"{i}.png").write_bytes(png(label))
            result = scan_directory(root, max_files=10, max_bytes=1024,
                                    max_file_bytes=128, max_distinct=10,
                                    min_repeat=3, suffix=".png")
            self.assertEqual(result["rare_candidates"][0]["locations"], ["3.png"])
            self.assertEqual(result["assessment"], "review_candidates")

    def test_stream_rejects_short_extra_and_bad_magic(self):
        good = png("road")
        for data, count in ((good[:-1], 1), (good + b"X", 1),
                            (b"X" + good[1:], 1)):
            with self.subTest(length=len(data), first=data[:1]):
                with self.assertRaises(ScanError):
                    scan_stream(BytesIO(data), file_size=128,
                                expected_count=count, max_bytes=1024,
                                max_distinct=10, min_repeat=3)


if __name__ == "__main__":
    unittest.main()
