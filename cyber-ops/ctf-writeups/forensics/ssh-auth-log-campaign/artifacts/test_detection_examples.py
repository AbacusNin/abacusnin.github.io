"""Small synthetic checks of the intended Sigma selections and threshold.

Requires PyYAML. This does not convert rules to a SIEM backend.
"""

import unittest
from collections import Counter
from pathlib import Path

import yaml


HERE = Path(__file__).parent


def matches(selection, event):
    for field, expected in selection.items():
        name, operator = field.split("|", 1)
        if operator != "contains":
            raise ValueError(operator)
        options = expected if isinstance(expected, list) else [expected]
        if not any(part in event.get(name, "") for part in options):
            return False
    return True


class DetectionExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (HERE / "mr_ssh_failure_volume.yml").open(encoding="utf-8") as handle:
            cls.base_rule, cls.volume_rule = list(yaml.safe_load_all(handle))
        with (HERE / "ssh_http_probe.yml").open(encoding="utf-8") as handle:
            cls.http_rule = yaml.safe_load(handle)

    def test_volume_boundary_and_expected_false_positive(self):
        selection = self.base_rule["detection"]["selection"]
        correlation = self.volume_rule["correlation"]
        self.assertEqual(correlation["group-by"], ["src_ip", "host"])
        self.assertEqual(correlation["timespan"], "10m")
        threshold = correlation["condition"]["gt"]
        events = [
            {"message": "Failed password for root from 192.0.2.10", "src_ip": "192.0.2.10", "host": "lab"}
            for _ in range(50)
        ]
        events += [{"message": "Accepted publickey for alice from 192.0.2.10", "src_ip": "192.0.2.10", "host": "lab"}]
        events += [{"message": "Failed password for root from 192.0.2.11", "src_ip": "192.0.2.11", "host": "lab"}]
        counts = Counter((event["src_ip"], event["host"]) for event in events if matches(selection, event))
        self.assertFalse(any(count > threshold for count in counts.values()))
        # One more failure on the first source passes the bound.
        events.append({"message": "Failed password for guest from 192.0.2.10", "src_ip": "192.0.2.10", "host": "lab"})
        counts = Counter((event["src_ip"], event["host"]) for event in events if matches(selection, event))
        self.assertEqual(counts[("192.0.2.10", "lab")], 51)
        self.assertTrue(counts[("192.0.2.10", "lab")] > threshold)
        # The same 51 records from an authorized test would still alert.

    def test_http_probe_positive_and_near_miss(self):
        detection = self.http_rule["detection"]
        def hit(message):
            event = {"message": message}
            return matches(detection["selection"], event) and matches(detection["method"], event)
        self.assertTrue(hit("Bad protocol version identification 'GET / HTTP/1.1'"))
        self.assertFalse(hit("Bad protocol version identification 'SSH-2.0-client'"))
        self.assertFalse(hit("HTTP GET / from a web server"))


if __name__ == "__main__":
    unittest.main()
