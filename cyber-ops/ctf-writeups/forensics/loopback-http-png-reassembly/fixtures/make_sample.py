"""Generate a tiny, invented loopback PCAP with three framed HTTP POSTs."""

import hashlib
import struct
import zlib
from pathlib import Path


def png_chunk(kind, data):
    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def sample_png():
    ihdr = struct.pack("!IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    image = zlib.compress(b"\x00\x15\x76\x32")
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", image) + png_chunk(b"IEND", b"")


def http_stream():
    image = sample_png()
    pieces = [image[:25], image[25:51], image[51:]]
    stream = bytearray()
    for index, payload in enumerate(pieces):
        body = struct.pack("!I", index) + hashlib.sha256(payload).digest()[:4] + payload
        stream.extend(b"POST /upload HTTP/1.1\r\nHost: 127.0.0.1:8080\r\n")
        stream.extend(b"Content-Type: application/octet-stream\r\nConnection: keep-alive\r\n")
        stream.extend(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
        stream.extend(body)
    return bytes(stream)


def packet(payload, sequence):
    tcp = struct.pack("!HHIIHHHH", 54321, 8080, sequence, 0, 0x5018, 65535, 0, 0)
    ip_len = 20 + len(tcp) + len(payload)
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, ip_len, 1, 0, 64, 6, 0,
                     b"\x7f\x00\x00\x01", b"\x7f\x00\x00\x01")
    eth = b"\x00" * 12 + b"\x08\x00"
    return eth + ip + tcp + payload


def sample_pcap():
    stream = http_stream()
    # Packet cuts cross HTTP headers and bodies. The last record retransmits
    # a byte-identical interval; strict TCP reassembly must deduplicate it.
    cuts = [0, 19, 90, 141, 219, 303, len(stream)]
    out = bytearray(struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1))
    for index, (start, end) in enumerate(zip(cuts, cuts[1:])):
        frame = packet(stream[start:end], 1000 + start)
        out.extend(struct.pack("<IIII", 1000 + index, 0, len(frame), len(frame)))
        out.extend(frame)
    repeat = packet(stream[19:90], 1019)
    out.extend(struct.pack("<IIII", 1007, 0, len(repeat), len(repeat)))
    out.extend(repeat)
    return bytes(out)


def main():
    destination = Path(__file__).with_name("sample_loopback.pcap")
    with destination.open("xb") as handle:
        handle.write(sample_pcap())
    print(f"Created {destination.name} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
