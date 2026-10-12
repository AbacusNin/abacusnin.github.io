"""Offline positive, benign, and malformed-input checks for the game-protocol lab."""

import json
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / "fixtures")]
from game_capture_triage import inspect, reassemble, varint
from game_egress_triage import evaluate
from make_sample import make_pcap


class CaptureTests(unittest.TestCase):
    def test_synthetic_capture_and_expected_report(self):
        data = (ROOT / "fixtures/sample_game.pcap").read_bytes()
        self.assertEqual(data, make_pcap())
        expected = json.loads((ROOT / "fixtures/expected_capture.json").read_text())
        self.assertEqual(inspect(data), expected)
        self.assertFalse(any("message" in chat for chat in expected["chats"]))

    def test_opt_in_chat_and_sender_order(self):
        result = inspect(make_pcap(), show_chat=True)
        self.assertEqual([item["message"] for item in result["chats"]], ["hi", "sample", "ok"])
        self.assertEqual([item["sender"] for item in result["chats"]],
                         ["sender_1", "sender_2", "sender_1"])

    def test_bad_capture_and_varint(self):
        with self.assertRaisesRegex(ValueError, "classic pcap"):
            inspect(b"not a capture")
        with self.assertRaisesRegex(ValueError, "record size"):
            inspect(make_pcap()[:-1])
        with self.assertRaisesRegex(ValueError, "overlong VarInt"):
            varint(b"\x80" * 5, 0)

    def test_tcp_gap_and_conflicting_overlap(self):
        with self.assertRaisesRegex(ValueError, "TCP gap"):
            reassemble([(100, b"abc"), (105, b"def")])
        with self.assertRaisesRegex(ValueError, "conflicting TCP overlap"):
            reassemble([(100, b"abc"), (102, b"XX")])


class FlowTests(unittest.TestCase):
    def test_positive_benign_and_near_miss(self):
        rows = [json.loads(line) for line in (ROOT / "fixtures/flow_events.jsonl").read_text().splitlines()]
        expected = json.loads((ROOT / "fixtures/expected_flow_findings.json").read_text())
        self.assertEqual({"findings": evaluate(rows)}, expected)
        self.assertEqual([item["handshake"] for item in expected["findings"]],
                         ["verified", "unverified"])

    def test_policy_field_must_be_boolean(self):
        row = json.loads((ROOT / "fixtures/flow_events.jsonl").read_text().splitlines()[0])
        row["approved_game_use"] = "false"
        with self.assertRaisesRegex(ValueError, "boolean"):
            evaluate([row])


if __name__ == "__main__":
    unittest.main()
