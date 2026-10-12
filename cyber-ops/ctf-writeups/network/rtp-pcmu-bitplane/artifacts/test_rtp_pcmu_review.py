"""Synthetic positive, benign periodic, near-miss, and malformed-header checks."""
from pathlib import Path
import struct
import unittest

from rtp_pcmu_review import parse_rtp, review


def make_pcap(path, kind):
    with path.open("wb") as out:
        out.write(b"\xd4\xc3\xb2\xa1" + struct.pack("<HHIIII", 2, 4, 0, 0, 65535, 228))
        period = bytes((i * 37 + 23) % 256 for i in range(400))
        audio = bytearray(period * 80)
        if kind == "positive":
            audio[0] ^= 1
            audio[402] ^= 1
        elif kind == "near_miss":
            audio[0] ^= 1
            audio[402] ^= 1
            for row in range(2, 32):
                audio[row * 400 + row] ^= 1
        for i in range(0, len(audio), 160):
            payload = b"\x80\x00" + struct.pack("!HII", i // 160, i, 17) + audio[i:i+160]
            udp = struct.pack("!HHHH", 12000, 12002, 8 + len(payload), 0) + payload
            ip = bytearray(20)
            ip[0] = 0x45
            ip[2:4] = struct.pack("!H", 20 + len(udp))
            ip[8:10] = b"\x40\x11"
            ip[12:16] = bytes((192, 0, 2, 1))
            ip[16:20] = bytes((192, 0, 2, 2))
            frame = bytes(ip) + udp
            out.write(struct.pack("<IIII", 0, i // 160, len(frame), len(frame)) + frame)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).with_name("_synthetic_test.pcap")

    def tearDown(self):
        self.path.unlink(missing_ok=True)

    def test_positive(self):
        make_pcap(self.path, "positive")
        flow = review(self.path)["flows"][0]
        self.assertTrue(flow["review_lead"])
        self.assertEqual(flow["lsb_deviation_rows"], [0, 1])
        self.assertEqual(flow["sequence_gaps"], 0)
        self.assertEqual(flow["timestamp_gaps"], 0)

    def test_benign_repetition_without_deviations(self):
        make_pcap(self.path, "benign")
        self.assertFalse(review(self.path)["flows"][0]["review_lead"])

    def test_near_miss_non_sparse_changes(self):
        make_pcap(self.path, "near_miss")
        self.assertFalse(review(self.path)["flows"][0]["review_lead"])

    def test_malformed_extension(self):
        self.assertIsNone(parse_rtp(b"\x90\x00" + b"\x00" * 10 + b"\x12\x34\xff\xff"))


if __name__ == "__main__":
    unittest.main()
