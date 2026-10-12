"""Synthetic positive, benign, near-miss, and coverage checks."""

import unittest
from pathlib import Path

from auth_log_triage import analyze


HERE = Path(__file__).parent


class TriageTests(unittest.TestCase):
    def test_synthetic_cases(self):
        result = analyze(HERE / "synthetic_secure.log")
        self.assertEqual(result["line_count"], 9)
        self.assertEqual(result["service_counts"], {"sshd": 8, "vsftpd": 1})
        self.assertEqual(sum(result["service_counts"].values()), 9)
        self.assertEqual(result["failed_users"], {"root": 2, "guest": 1, "admin": 1})
        self.assertEqual(result["closed_sources"], {"192.0.2.10": 1})
        self.assertEqual(result["http_to_ssh_events"], 1)
        self.assertEqual(result["failure_then_success_sources"], ["198.51.100.7"])
        self.assertNotIn("203.0.113.8", result["failure_then_success_sources"])
        self.assertEqual(result["rejected_addresses"], {"failed_bad_ip": 1})

    def test_unparsed_header_is_visible(self):
        result = analyze(HERE / "synthetic_malformed.log")
        self.assertEqual(result["unparsed_headers"], 1)
        self.assertEqual(sum(result["service_counts"].values()) + result["unparsed_headers"], 1)

    def test_line_limit(self):
        with self.assertRaises(ValueError):
            analyze(HERE / "synthetic_secure.log", max_line_bytes=8)


if __name__ == "__main__":
    unittest.main()
