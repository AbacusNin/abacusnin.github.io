import unittest
from network_hunt import analyze


class HuntTests(unittest.TestCase):
    def test_correlated_synthetic_case(self):
        events = [
            {"type": "arp", "opcode": 2, "mac": "02:00:00:00:00:01", "ip": "192.0.2.1"},
            {"type": "arp", "opcode": 2, "mac": "02:00:00:00:00:01", "ip": "192.0.2.2"},
            {"type": "icmp", "icmp_type": 5, "src": "192.0.2.9", "gateway": "192.0.2.2"},
        ]
        for i in range(12):
            events.append({"type": "http", "method": "POST", "src": "192.0.2.1",
                           "dst": "192.0.2.2", "uri": "/ping", "ts": i,
                           "response_bytes": 342 + (i % 2)})
        kinds = {x["kind"] for x in analyze(events, {"192.0.2.254"})}
        self.assertEqual(kinds, {"multi_ip_arp_claim", "unauthorized_redirect",
                                 "post_burst", "length_oracle_hypothesis"})

    def test_benign_multi_ip_still_requires_review(self):
        events = [{"type": "arp", "opcode": 2, "mac": "02:00:00:00:00:02", "ip": ip}
                  for ip in ("192.0.2.10", "192.0.2.11")]
        self.assertEqual([x["kind"] for x in analyze(events, set())],
                         ["multi_ip_arp_claim"])

    def test_near_miss(self):
        events = [{"type": "icmp", "icmp_type": 5, "src": "192.0.2.254"}]
        events += [{"type": "http", "method": "POST", "src": "192.0.2.10",
                    "dst": "192.0.2.20", "uri": "/ping", "ts": i,
                    "response_bytes": 342 + (i % 3)} for i in range(12)]
        self.assertEqual([x["kind"] for x in analyze(events, {"192.0.2.254"})],
                         ["post_burst"])


if __name__ == "__main__":
    unittest.main()
