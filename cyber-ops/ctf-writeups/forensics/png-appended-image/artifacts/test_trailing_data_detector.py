import json
import subprocess
import sys
import unittest
import zlib
from pathlib import Path

from artifacts.trailing_data_detector import PNG_SIG, PngError, inspect


PAGE = Path(__file__).resolve().parents[1]


def chunk(kind, body=b""):
    return (len(body).to_bytes(4, "big") + kind + body +
            zlib.crc32(kind + body).to_bytes(4, "big"))


def png(note=b""):
    ihdr = (1).to_bytes(4, "big") * 2 + bytes([8, 2, 0, 0, 0])
    rgb_row = b"\x00\x20\x60\xa0"
    return (PNG_SIG + chunk(b"IHDR", ihdr) +
            (chunk(b"tEXt", note) if note else b"") +
            chunk(b"IDAT", zlib.compress(rgb_row)) + chunk(b"IEND"))


class TrailingDataTests(unittest.TestCase):
    def test_invented_fixture_matches_report_and_carves(self):
        sample = PAGE / "fixtures/sample_appended.png"
        expected = json.loads((PAGE / "fixtures/expected_report.json").read_text())
        result = inspect(sample.read_bytes())
        self.assertEqual(result["carrier_end"], expected["carrier_end"])
        self.assertEqual(result["trailing_bytes"], expected["trailing_bytes"])
        self.assertEqual(len(result["carves"]), 1)
        self.assertEqual(result["carves"][0]["sha256"], expected["carve_sha256"])
        self.assertTrue(result["carves"][0]["signature_repaired"])
        self.assertIn("SAMPLE TRAILER", [run["preview"] for run in result["printable_runs"]])
        command = [sys.executable, str(PAGE / "artifacts/trailing_data_detector.py"),
                   str(sample)]
        report = json.loads(subprocess.check_output(command, text=True))
        self.assertEqual(report["carves"][0]["sha256"], expected["carve_sha256"])

    def test_marker_inside_chunk_does_not_end_carrier(self):
        data = png(b"note\x00IEND fake marker in metadata")
        result = inspect(data)
        self.assertEqual(result["carrier_end"], len(data))
        self.assertEqual(result["trailing_bytes"], 0)
        self.assertEqual(result["carves"], [])

    def test_benign_trailer_and_bad_candidate(self):
        carrier = png()
        fake = bytearray(png()[8:])
        fake[-1] ^= 1
        for trailer in (b"SAMPLE TRAILER", bytes(fake)):
            result = inspect(carrier + trailer)
            self.assertEqual(result["trailing_bytes"], len(trailer))
            self.assertEqual(result["carves"], [])

    def test_signed_and_stripped_second_images(self):
        carrier = png()
        second = png()
        for appended, repaired in ((second, False), (second[8:], True)):
            result = inspect(carrier + appended)
            self.assertEqual(len(result["carves"]), 1)
            self.assertEqual(result["carves"][0]["bytes"], second)
            self.assertEqual(result["carves"][0]["signature_repaired"], repaired)

    def test_crc_and_size_rejections(self):
        broken = bytearray(png())
        broken[-1] ^= 1
        with self.assertRaises(PngError):
            inspect(bytes(broken))
        with self.assertRaises(PngError):
            inspect(png() + b"x" * 16_000_000)


if __name__ == "__main__":
    unittest.main()
