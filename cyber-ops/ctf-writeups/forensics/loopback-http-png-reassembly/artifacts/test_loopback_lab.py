"""Positive, benign, malformed, and near-miss checks for the synthetic lab."""

import json
import hashlib
import sys
import unittest
from pathlib import Path

from pcap_http_reassemble import (analyze, inversion_report, reassemble_frames, reconstruct_flow,
                                  split_requests, validate_png)
from post_burst_hunt import hunt

HERE = Path(__file__).resolve().parent
FIXTURES = HERE.parent / "fixtures"
sys.path.insert(0, str(FIXTURES))
from make_sample import sample_pcap, sample_png  # noqa: E402


class LoopbackLabTests(unittest.TestCase):
    def test_three_posts_reconstruct_png_and_ignore_retransmission(self):
        report, blob = analyze(sample_pcap())
        self.assertEqual(report["matching_posts"], 3)
        self.assertEqual(report["frame_sha256_prefix_matches"], 3)
        self.assertEqual(report["client_flows"], 1)
        self.assertEqual(blob, sample_png())
        self.assertEqual(report["png"]["chunk_types"], ["IHDR", "IDAT", "IEND"])
        self.assertTrue(all(part["count"] == 0 for part in report["arrival_inversions"].values()))

    def test_bad_integrity_tag_rejected(self):
        raw = sample_pcap().replace(b"POST /upload", b"POST /uploaD", 1)
        with self.assertRaises(ValueError):
            analyze(raw)
        # Keep the original tag and change a payload byte.
        image = sample_png()
        body = b"\x00\x00\x00\x00" + hashlib.sha256(image).digest()[:4] + image
        changed = body[:-1] + bytes([body[-1] ^ 1])
        with self.assertRaisesRegex(ValueError, "SHA-256 prefix"):
            reassemble_frames([{"body": changed}])

    def test_tcp_gap_and_conflicting_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError, "gap"):
            reconstruct_flow([(1.0, 100, b"abc"), (2.0, 104, b"z")])
        with self.assertRaisesRegex(ValueError, "overlap"):
            reconstruct_flow([(1.0, 100, b"abc"), (2.0, 101, b"XZ")])

    def test_http_framing_and_png_crc_rejected(self):
        data = b"POST /upload HTTP/1.1\r\nContent-Length: 10\r\n\r\nabc"
        with self.assertRaisesRegex(ValueError, "incomplete"):
            split_requests(data, [(0, len(data), 1.0)])
        data = b"POST /upload HTTP/1.1\r\nContent-Length: 1\r\nContent-Length: 1\r\n\r\na"
        with self.assertRaisesRegex(ValueError, "duplicate"):
            split_requests(data, [(0, len(data), 1.0)])
        image = bytearray(sample_png())
        image[20] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            validate_png(bytes(image))

    def test_inversion_positive_and_zero(self):
        ordered = [{"index": i, "line_time": i, "body_first_time": i,
                    "body_last_time": i} for i in range(3)]
        self.assertEqual(inversion_report(ordered)["line_time"]["count"], 0)
        reordered = [dict(record) for record in ordered]
        reordered[1]["line_time"], reordered[2]["line_time"] = 2, 1
        self.assertEqual(inversion_report(reordered)["line_time"],
                         {"count": 1, "lowest_index": 1})

    def test_burst_positive_approved_and_near_miss(self):
        events = [json.loads(line) for line in (FIXTURES / "sample_events.jsonl").read_text().splitlines()]
        findings = hunt(events)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["host"], "workstation-a")
        self.assertEqual(findings[0]["post_count"], 3)
        self.assertEqual(hunt([event for event in events if event["host"] != "workstation-a"]), [])
        outlier = dict(events[0], body_bytes=200000)
        self.assertEqual(hunt(events + [outlier])[0]["post_count"], 3)


if __name__ == "__main__":
    unittest.main()
