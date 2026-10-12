"""Read a bounded classic PCAP, reconstruct HTTP POST bodies, and check framed PNG data.

This is an offline forensic aid, not a general TCP or HTTP implementation. It rejects
gaps, ambiguous overlaps, chunked transfer coding, duplicate indices, and bad CRCs.
"""

import argparse
import hashlib
import json
import struct
import zlib
from collections import defaultdict
from pathlib import Path

MAX_CAPTURE = 128 * 1024 * 1024
MAX_PACKET = 1024 * 1024
MAX_PACKETS = 200_000
MAX_FLOW = 64 * 1024 * 1024
MAX_HEADER = 16 * 1024
MAX_BODY = 256 * 1024
MAX_CHUNKS = 20_000
MAX_IMAGE = 64 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def pcap_packets(raw, server_port):
    if len(raw) < 24 or len(raw) > MAX_CAPTURE:
        raise ValueError("capture size outside 24 bytes..128 MiB")
    magic = raw[:4]
    formats = {b"\xd4\xc3\xb2\xa1": ("<", 1_000_000),
               b"\xa1\xb2\xc3\xd4": (">", 1_000_000),
               b"\x4d\x3c\xb2\xa1": ("<", 1_000_000_000),
               b"\xa1\xb2\x3c\x4d": (">", 1_000_000_000)}
    if magic not in formats:
        raise ValueError("only classic PCAP is supported")
    endian, scale = formats[magic]
    linktype = struct.unpack_from(endian + "I", raw, 20)[0]
    if linktype not in (1, 101):
        raise ValueError("only Ethernet and raw IPv4 link types are supported")
    offset = 24
    count = 0
    while offset < len(raw):
        if offset + 16 > len(raw):
            raise ValueError("truncated PCAP packet header")
        sec, fraction, incl, _orig = struct.unpack_from(endian + "IIII", raw, offset)
        offset += 16
        if incl > MAX_PACKET or offset + incl > len(raw):
            raise ValueError("truncated or oversized captured packet")
        frame = raw[offset:offset + incl]
        offset += incl
        count += 1
        if count > MAX_PACKETS:
            raise ValueError("packet count exceeds bound")
        if linktype == 1:
            if len(frame) < 14:
                continue
            ethertype = int.from_bytes(frame[12:14], "big")
            start = 14
            for _ in range(2):
                if ethertype not in (0x8100, 0x88A8):
                    break
                if len(frame) < start + 4:
                    raise ValueError("short VLAN header")
                ethertype = int.from_bytes(frame[start + 2:start + 4], "big")
                start += 4
            if ethertype != 0x0800:
                continue
            frame = frame[start:]
        if len(frame) < 20 or frame[0] >> 4 != 4:
            continue
        ihl = (frame[0] & 15) * 4
        if ihl < 20 or len(frame) < ihl:
            raise ValueError("bad IPv4 header length")
        total = int.from_bytes(frame[2:4], "big")
        if total < ihl or total > len(frame):
            raise ValueError("truncated IPv4 datagram")
        if int.from_bytes(frame[6:8], "big") & 0x3FFF:
            raise ValueError("fragmented IPv4 is unsupported")
        if frame[9] != 6:
            continue
        ip = frame[:total]
        tcp = ip[ihl:]
        if len(tcp) < 20:
            raise ValueError("short TCP header")
        sport, dport, sequence = struct.unpack_from("!HHI", tcp)
        if dport != server_port:
            continue
        tcp_header = (tcp[12] >> 4) * 4
        if tcp_header < 20 or tcp_header > len(tcp):
            raise ValueError("bad TCP header length")
        payload = tcp[tcp_header:]
        if payload:
            flow = (ip[12:16].hex(), sport, ip[16:20].hex(), dport)
            yield sec + fraction / scale, flow, sequence, payload


def reconstruct_flow(segments):
    ordered = sorted(segments, key=lambda item: item[1])
    if not ordered:
        return b"", []
    base = ordered[0][1]
    stream = bytearray()
    timing = []
    for timestamp, sequence, payload in ordered:
        start = sequence - base
        if start > len(stream):
            raise ValueError("TCP sequence gap; refusing zero fill")
        overlap = min(len(payload), len(stream) - start)
        if stream[start:start + overlap] != payload[:overlap]:
            raise ValueError("conflicting TCP overlap")
        if overlap < len(payload):
            new_start = len(stream)
            stream.extend(payload[overlap:])
            if len(stream) > MAX_FLOW:
                raise ValueError("TCP flow exceeds bound")
            timing.append((new_start, len(stream), timestamp))
    return bytes(stream), timing


def byte_time(timing, position):
    for start, end, timestamp in timing:
        if start <= position < end:
            return timestamp
    raise ValueError("request byte has no packet timestamp")


def split_requests(stream, timing):
    pos = 0
    requests = []
    while pos < len(stream):
        boundary = stream.find(b"\r\n\r\n", pos, pos + MAX_HEADER + 4)
        if boundary < 0:
            raise ValueError("missing or oversized HTTP header")
        header = stream[pos:boundary]
        lines = header.split(b"\r\n")
        try:
            line = lines[0].decode("ascii")
            method, path, version = line.split(" ")
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("invalid HTTP request line") from exc
        if version != "HTTP/1.1":
            raise ValueError("expected HTTP/1.1 request")
        headers = {}
        for row in lines[1:]:
            if b":" not in row:
                raise ValueError("malformed HTTP header")
            name, value = row.split(b":", 1)
            key = name.strip().lower()
            if key in headers:
                raise ValueError("duplicate HTTP header")
            headers[key] = value.strip()
        if b"transfer-encoding" in headers:
            raise ValueError("Transfer-Encoding unsupported")
        value = headers.get(b"content-length", b"0")
        if not value.isdigit():
            raise ValueError("invalid Content-Length")
        length = int(value)
        if length > MAX_BODY:
            raise ValueError("HTTP body exceeds bound")
        if method == "POST" and b"content-length" not in headers:
            raise ValueError("POST missing Content-Length")
        body_start = boundary + 4
        end = body_start + length
        if end > len(stream):
            raise ValueError("incomplete HTTP request body")
        requests.append({"method": method, "path": path, "headers": headers,
                         "body": stream[body_start:end],
                         "line_time": byte_time(timing, pos),
                         "body_first_time": byte_time(timing, body_start) if length else None,
                         "body_last_time": byte_time(timing, end - 1) if length else None})
        if len(requests) > MAX_CHUNKS:
            raise ValueError("request count exceeds bound")
        pos = end
    return requests


def validate_png(blob):
    if not blob.startswith(PNG_SIGNATURE) or len(blob) > MAX_IMAGE:
        raise ValueError("reassembled content is not a bounded PNG")
    pos = 8
    types = []
    dimensions = None
    while pos < len(blob):
        if pos + 12 > len(blob):
            raise ValueError("truncated PNG chunk")
        size = int.from_bytes(blob[pos:pos + 4], "big")
        if size > MAX_IMAGE or pos + 12 + size > len(blob):
            raise ValueError("PNG chunk outside file")
        kind = blob[pos + 4:pos + 8]
        data = blob[pos + 8:pos + 8 + size]
        expected = int.from_bytes(blob[pos + 8 + size:pos + 12 + size], "big")
        if zlib.crc32(kind + data) & 0xFFFFFFFF != expected:
            raise ValueError("PNG CRC mismatch")
        types.append(kind.decode("ascii", errors="replace"))
        if len(types) == 1:
            if kind != b"IHDR" or size != 13:
                raise ValueError("invalid PNG IHDR")
            dimensions = struct.unpack_from("!II", data)
            if not all(dimensions) or any(x > 100_000 for x in dimensions):
                raise ValueError("implausible PNG dimensions")
        pos += 12 + size
        if kind == b"IEND":
            if size != 0 or pos != len(blob):
                raise ValueError("PNG trailing bytes after IEND")
            break
    if types.count("IHDR") != 1 or "IDAT" not in types or types.count("IEND") != 1:
        raise ValueError("incomplete PNG structure")
    return {"width": dimensions[0], "height": dimensions[1],
            "chunk_types": types, "text_chunk_count": sum(t in ("tEXt", "zTXt", "iTXt") for t in types)}


def inversion_report(selected):
    inversions = {}
    for field in ("line_time", "body_first_time", "body_last_time"):
        ordered = sorted(selected, key=lambda item: item[field])
        highest = -1
        backwards = []
        for request in ordered:
            if request["index"] < highest:
                backwards.append(request["index"])
            highest = max(highest, request["index"])
        inversions[field] = {"count": len(backwards), "lowest_index": min(backwards) if backwards else None}
    return inversions


def reassemble_frames(selected):
    chunks = {}
    for request in selected:
        body = request["body"]
        if len(body) < 8:
            raise ValueError("short application frame")
        index = int.from_bytes(body[:4], "big")
        tag, payload = body[4:8], body[8:]
        if index >= MAX_CHUNKS or hashlib.sha256(payload).digest()[:4] != tag:
            raise ValueError("invalid frame index or SHA-256 prefix")
        if index in chunks:
            raise ValueError("duplicate application index")
        chunks[index] = payload
        request["index"] = index
    if set(chunks) != set(range(len(chunks))):
        raise ValueError("missing or nonzero-start application index")
    return b"".join(chunks[i] for i in range(len(chunks)))


def analyze(raw, server_port=8080, path="/upload"):
    flows = defaultdict(list)
    packet_count = 0
    for timestamp, flow, sequence, payload in pcap_packets(raw, server_port):
        flows[flow].append((timestamp, sequence, payload))
        packet_count += 1
    requests = []
    for segments in flows.values():
        stream, timing = reconstruct_flow(segments)
        requests.extend(split_requests(stream, timing))
    selected = [request for request in requests if request["method"] == "POST" and request["path"] == path]
    if not selected:
        raise ValueError("no matching POST requests")
    blob = reassemble_frames(selected)
    png = validate_png(blob)
    inversions = inversion_report(selected)
    report = {"captured_data_packets": packet_count, "client_flows": len(flows),
              "http_requests": len(requests), "matching_posts": len(selected),
              "frame_count": len(selected), "frame_sha256_prefix_matches": len(selected),
              "reassembled_bytes": len(blob), "reassembled_sha256": hashlib.sha256(blob).hexdigest(),
              "png": png, "arrival_inversions": inversions,
              "scope": "Client-to-listener traffic only; no off-host forwarding or capture method inferred."}
    return report, blob


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", help="authorized classic PCAP")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--path", default="/upload")
    parser.add_argument("--output", help="optional new path for reconstructed PNG; will not overwrite")
    args = parser.parse_args()
    try:
        if not 1 <= args.port <= 65535 or not args.path.startswith("/"):
            raise ValueError("invalid port or request path")
        source = Path(args.capture)
        if source.stat().st_size > MAX_CAPTURE:
            raise ValueError("capture exceeds 128 MiB")
        report, blob = analyze(source.read_bytes(), args.port, args.path)
        if args.output:
            with Path(args.output).open("xb") as handle:
                handle.write(blob)
        print(json.dumps(report, indent=2))
    except (OSError, ValueError, struct.error) as exc:
        parser.exit(2, f"analysis failed: {exc}\n")


if __name__ == "__main__":
    main()
