"""Triage simple cleartext HTTP transactions in a bounded classic pcap."""

import argparse
import json
import re
import struct
from collections import Counter, defaultdict, deque
from pathlib import Path


MAX_BYTES = 32_000_000
MAX_FRAMES = 200_000
MAX_FRAME_BYTES = 65_535
FAMILY = re.compile(r"^(/[^?#]+_)([0-9]+)$")


def inspect(data):
    if len(data) > MAX_BYTES:
        raise ValueError(f"capture exceeds {MAX_BYTES} bytes")
    if len(data) < 24 or data[:4] != b"\xd4\xc3\xb2\xa1":
        raise ValueError("expected little-endian classic pcap with microsecond timestamps")
    _magic, major, minor, _zone, _sigfigs, _snaplen, linktype = struct.unpack_from("<IHHIIII", data)
    if (major, minor) != (2, 4) or linktype != 1:
        raise ValueError("expected pcap v2.4 with Ethernet frames")
    offset = 24
    frames = 0
    requests = responses = linked = 0
    statuses = Counter()
    lengths = Counter()
    families = defaultdict(list)
    pending = defaultdict(deque)
    successes = []
    addresses = set()
    while offset < len(data):
        if offset + 16 > len(data):
            raise ValueError("truncated pcap record header")
        _sec, _usec, size, _wire_size = struct.unpack_from("<IIII", data, offset)
        offset += 16
        if size > MAX_FRAME_BYTES or offset + size > len(data):
            raise ValueError("invalid captured frame length")
        frame = memoryview(data)[offset:offset + size]
        offset += size
        frames += 1
        if frames > MAX_FRAMES:
            raise ValueError(f"capture exceeds {MAX_FRAMES} frames")
        if len(frame) < 34 or frame[12:14].tobytes() != b"\x08\x00":
            continue
        ip = frame[14:]
        ihl = (ip[0] & 15) * 4
        if ip[0] >> 4 != 4 or ihl < 20 or len(ip) < ihl + 20 or ip[9] != 6:
            continue
        src, dst = bytes(ip[12:16]), bytes(ip[16:20])
        addresses.add(src)
        addresses.add(dst)
        tcp = ip[ihl:]
        tcp_header = (tcp[12] >> 4) * 4
        if tcp_header < 20 or len(tcp) < tcp_header:
            continue
        sport = int.from_bytes(tcp[:2], "big")
        dport = int.from_bytes(tcp[2:4], "big")
        body = tcp[tcp_header:].tobytes()
        if body.startswith(b"GET "):
            first = body.partition(b"\r\n")[0].split(b" ")
            if len(first) < 3:
                continue
            uri = first[1].decode("utf-8", "replace")
            pending[(src, sport, dst, dport)].append(uri)
            requests += 1
            match = FAMILY.fullmatch(uri)
            if match:
                families[match.group(1)].append(int(match.group(2)))
        elif body.startswith(b"HTTP/"):
            header, _divider, packet_body = body.partition(b"\r\n\r\n")
            first = header.partition(b"\r\n")[0].split(b" ")
            if len(first) < 2 or not first[1].isdigit():
                continue
            status = int(first[1])
            statuses[status] += 1
            responses += 1
            q = pending[(dst, dport, src, sport)]
            uri = q.popleft() if q else None
            linked += uri is not None
            length_match = re.search(rb"(?im)^Content-Length:\s*([0-9]+)\r?$", header)
            length = int(length_match.group(1)) if length_match else None
            lengths[str(length) if length is not None else "missing"] += 1
            transfer_encoding = bool(re.search(rb"(?im)^Transfer-Encoding:", header))
            if status == 200:
                successes.append({"uri": uri, "content_length": length,
                                  "body_bytes_in_first_packet": len(packet_body),
                                  "transfer_encoding_present": transfer_encoding,
                                  "body_state": "declared_empty" if length == 0 and not transfer_encoding else "unknown"})
    family_report = []
    for prefix, values in sorted(families.items()):
        unique = set(values)
        family_report.append({"prefix": prefix, "requests": len(values),
                              "unique_indices": len(unique), "minimum": min(unique),
                              "maximum": max(unique),
                              "contiguous": len(unique) == max(unique) - min(unique) + 1})
    return {"frames": frames, "requests": requests, "responses": responses,
            "linked_responses": linked, "status_counts": dict(sorted(statuses.items())),
            "content_length_counts": dict(sorted(lengths.items())),
            "loopback_only": bool(addresses) and all(a == b"\x7f\x00\x00\x01" for a in addresses),
            "numeric_path_families": family_report, "successes": successes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    with args.capture.open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    print(json.dumps(inspect(data), indent=2))


if __name__ == "__main__":
    main()
