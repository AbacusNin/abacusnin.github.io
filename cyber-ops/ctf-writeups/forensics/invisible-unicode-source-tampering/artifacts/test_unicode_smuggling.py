#!/usr/bin/env python3
"""Synthetic checks for the read-only Unicode source scanner."""

import unittest
from pathlib import Path

from unicode_smuggling_scanner import scan_file, scan_text

FIXTURES = Path(__file__).parent.parent / "fixtures"


class ScannerTests(unittest.TestCase):
    def test_tag_carrier_decodes_without_execution(self):
        result = scan_file(FIXTURES / "sample_carrier.py", show_decoded=True)
        self.assertEqual(result["counts"], {"unicode_tag": 20})
        self.assertEqual(result["tag_runs"][0]["decoded_ascii"], 'print("review only")')
        self.assertEqual(result["counts"]["unicode_tag"] * 4, 80)

    def test_clean_and_visible_unicode_are_clear(self):
        self.assertEqual(scan_file(FIXTURES / "clean_source.py")["counts"], {})
        self.assertEqual(scan_file(FIXTURES / "benign_unicode_source.py")["counts"], {})

    def test_emoji_tags_are_an_expected_false_positive(self):
        result = scan_file(FIXTURES / "benign_emoji_tags.py", show_decoded=True)
        self.assertEqual(result["counts"], {"unicode_tag": 6})
        self.assertEqual(result["tag_runs"][0]["decoded_ascii"], "gbeng")

    def test_special_tags_are_not_mapped_to_ascii(self):
        result = scan_text(chr(0xE0001) + chr(0xE007F), show_decoded=True)
        self.assertEqual(result["counts"], {"unicode_tag": 2})
        self.assertEqual(result["tag_runs"], [])

    def test_bidi_control_is_reported(self):
        result = scan_text("safe" + chr(0x202E) + "text")
        self.assertEqual(result["counts"], {"zero_width_or_bidi": 1})


if __name__ == "__main__":
    unittest.main()
