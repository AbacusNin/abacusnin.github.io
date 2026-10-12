"""Checks for the offline indicator triage example."""

import subprocess
import sys
import unittest
from pathlib import Path

from reserved_ip_filter import classify, triage


HERE = Path(__file__).parent


class IndicatorFilterTests(unittest.TestCase):
    def test_documentation_and_benchmark_bounds(self):
        for value in ("192.0.2.1", "198.51.100.200", "203.0.113.254"):
            self.assertEqual(classify(value)[1:], ("documentation", "do_not_enrich"))
        for value in ("198.18.0.0", "198.19.255.255"):
            self.assertEqual(classify(value)[1:], ("benchmark", "do_not_enrich"))
        self.assertEqual(classify("198.20.0.1")[1], "unclassified")

    def test_local_values_and_special_near_miss(self):
        for value in ("10.1.2.3", "172.16.1.1", "192.168.1.2", "100.64.0.1", "169.254.2.3", "127.0.0.1"):
            self.assertEqual(classify(value)[2], "local_context_only")
        self.assertEqual(classify("192.0.0.9")[1:], ("unclassified", "review_before_enrichment"))
        self.assertEqual(classify("8.8.8.8")[1:], ("unclassified", "review_before_enrichment"))

    def test_invalid_and_bounded_input(self):
        self.assertEqual(classify("=HYPERLINK(\"bad\")"), ("", "invalid", "check_source"))
        self.assertEqual(classify("2001:db8::1"), ("", "not_ipv4", "check_source"))
        self.assertEqual(triage(b"# note\n\n192.0.2.1\n")[0], (3, "192.0.2.1", "documentation", "do_not_enrich"))
        with self.assertRaises(ValueError):
            triage(("1.1.1.1\n" * 10_001).encode())
        with self.assertRaises(ValueError):
            triage(("x" * 257).encode())

    def test_cli_fixture(self):
        result = subprocess.run(
            [sys.executable, str(HERE / "reserved_ip_filter.py"), str(HERE.parent / "fixtures" / "sample_ips.txt")],
            capture_output=True, text=True, check=True,
        )
        expected = (HERE.parent / "fixtures" / "expected_triage.tsv").read_text(encoding="utf-8")
        self.assertEqual(result.stdout.replace("\r\n", "\n"), expected)


if __name__ == "__main__":
    unittest.main()
