"""Offline PCMU periodicity triage for classic Ethernet or raw-IP pcap files.

This proof of concept reads bounded files, reports metadata and periodicity,
and never prints or decodes an embedded message.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct

MAX_FILE = 32 * 1024 * 1024
MAX_PACKETS = 100_000
MAX_FLOW_BYTES = 8 * 1024 * 1024


def udp_payloads(path):
    if path.stat().st_size > MAX_FILE:
        raise ValueError("capture exceeds 32 MiB limit")
    blob = path.read_bytes()
    if len(blob) < 24 or blob[:4] not in (b"\xd4\xc3\xb2\xa1", b"\xa1\xb2\xc3\xd4"):
        raise ValueError("expected classic pcap")
    endian = "<" if blob[0] == 0xd4 else ">"
    linktype = struct.unpack_from(endian + "I", blob, 20)[0]
    if linktype not in (1, 228):
        raise ValueError("only Ethernet and raw IPv4 are supported")
    offset = 24
    count = 0
    while offset < len(blob):
        if offset + 16 > len(blob):
            raise ValueError("truncated pcap record")
        _, _, captured, original = struct.unpack_from(endian + "IIII", blob, offset)
        offset += 16
        if captured > original or offset + captured > len(blob):
            raise ValueError("invalid pcap record length")
        frame = blob[offset:offset + captured]
        offset += captured
        count += 1
        if count > MAX_PACKETS:
            raise ValueError("capture exceeds packet limit")
        if linktype == 1:
            if len(frame) < 14 or frame[12:14] != b"\x08\x00":
                continue
            ip = frame[14:]
        else:
            ip = frame
        if len(ip) < 20 or ip[0] >> 4 != 4:
            continue
        ihl = (ip[0] & 15) * 4
        if ihl < 20 or len(ip) < ihl + 8 or ip[9] != 17:
            continue
        if struct.unpack_from("!H", ip, 6)[0] & 0x3fff:
            continue
        total = struct.unpack_from("!H", ip, 2)[0]
        if total < ihl + 8 or len(ip) < total:
            continue
        sport, dport, udp_len = struct.unpack_from("!HHH", ip, ihl)
        if udp_len < 8 or ihl + udp_len > total:
            continue
        src = ".".join(map(str, ip[12:16]))
        dst = ".".join(map(str, ip[16:20]))
        yield (src, sport, dst, dport), ip[ihl + 8:ihl + udp_len]


def parse_rtp(data):
    if len(data) < 12 or data[0] >> 6 != 2:
        return None
    if data[1] & 127 != 0:  # static PT 0: PCMU
        return None
    cc = data[0] & 15
    pos = 12 + 4 * cc
    if len(data) < pos:
        return None
    if data[0] & 16:
        if len(data) < pos + 4:
            return None
        words = struct.unpack_from("!H", data, pos + 2)[0]
        pos += 4 + 4 * words
    if pos >= len(data):
        return None
    end = len(data)
    if data[0] & 32:
        padding = data[-1]
        if padding == 0 or padding > end - pos:
            return None
        end -= padding
    if end <= pos:
        return None
    sequence, timestamp, ssrc = struct.unpack_from("!HII", data, 2)
    return sequence, timestamp, ssrc, data[pos:end]


def analyze(payloads, period, minimum_packets):
    parsed = [parse_rtp(p) for p in payloads]
    if len(parsed) < minimum_packets or any(p is None for p in parsed):
        return None
    ssrcs = {p[2] for p in parsed}
    if len(ssrcs) != 1:
        return None
    seq_gaps = sum((parsed[i][0] - parsed[i-1][0]) % 65536 != 1 for i in range(1, len(parsed)))
    ts_gaps = sum((parsed[i][1] - parsed[i-1][1]) % 2**32 != len(parsed[i-1][3]) for i in range(1, len(parsed)))
    audio = b"".join(p[3] for p in parsed)
    if len(audio) > MAX_FLOW_BYTES:
        raise ValueError("RTP flow exceeds 8 MiB limit")
    if len(audio) < period * 4:
        return None
    n = min(50_000, len(audio) - period)
    match = sum(audio[i] == audio[i + period] for i in range(n)) / n
    rows = [audio[i:i + period] for i in range(0, len(audio) - period + 1, period)]
    baseline = [sum(row[j] & 1 for row in rows) > len(rows) // 2 for j in range(period)]
    altered = [i for i, row in enumerate(rows)
               if any((row[j] & 1) != baseline[j] for j in range(period))]
    return {
        "packets": len(parsed), "payload_bytes": len(audio), "ssrc_count": len(ssrcs),
        "sequence_gaps": seq_gaps, "timestamp_gaps": ts_gaps,
        "period_samples": period, "byte_match_rate": round(match, 6),
        "lsb_deviation_rows": altered[:20], "lsb_deviation_row_count": len(altered),
        "review_lead": match >= 0.95 and 0 < len(altered) <= max(2, len(rows) // 10),
    }


def review(path, period=400, minimum_packets=10):
    flows = defaultdict(list)
    for key, payload in udp_payloads(path):
        flows[key].append(payload)
    results = []
    for key, payloads in flows.items():
        result = analyze(payloads, period, minimum_packets)
        if result:
            result["flow"] = {"src_ip": key[0], "src_port": key[1],
                              "dst_ip": key[2], "dst_port": key[3]}
            results.append(result)
    return {"flows": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pcap", type=Path)
    parser.add_argument("--period", type=int, default=400)
    parser.add_argument("--minimum-packets", type=int, default=10)
    args = parser.parse_args()
    if not 8 <= args.period <= 4000 or not 2 <= args.minimum_packets <= 1000:
        parser.error("period must be 8..4000 and minimum-packets 2..1000")
    print(json.dumps(review(args.pcap, args.period, args.minimum_packets), indent=2))


if __name__ == "__main__":
    main()
