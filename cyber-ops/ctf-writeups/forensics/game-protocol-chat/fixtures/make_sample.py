"""Build a tiny invented cleartext game-protocol capture for offline tests."""

import ipaddress
import struct
from pathlib import Path


def varint(value):
    out = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        out.append(byte | (128 if value else 0))
        if not value:
            return bytes(out)


def frame(packet_id, body):
    contents = varint(packet_id) + body
    return varint(len(contents)) + contents


def checksum(data):
    if len(data) % 2:
        data += b"\x00"
    words = struct.unpack("!" + "H" * (len(data) // 2), data)
    total = sum(words)
    while total >> 16:
        total = (total & 65535) + (total >> 16)
    return (~total) & 65535


def packet(src, sport, dst, dport, seq, payload, packet_id):
    src_ip = ipaddress.IPv4Address(src).packed
    dst_ip = ipaddress.IPv4Address(dst).packed
    tcp = struct.pack("!HHIIHHHH", sport, dport, seq, 0, 0x5018, 4096, 0, 0)
    pseudo = src_ip + dst_ip + struct.pack("!BBH", 0, 6, len(tcp) + len(payload))
    tcp = tcp[:16] + struct.pack("!H", checksum(pseudo + tcp + payload)) + tcp[18:]
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 20 + len(tcp) + len(payload), packet_id,
                     0, 64, 6, 0, src_ip, dst_ip)
    ip = ip[:10] + struct.pack("!H", checksum(ip)) + ip[12:]
    return b"\x00" * 12 + b"\x08\x00" + ip + tcp + payload


def chat(sender, text, timestamp):
    encoded = text.encode("utf-8")
    return frame(0x3F, varint(0) + sender + varint(0) + b"\x00" +
                 varint(len(encoded)) + encoded + struct.pack(">qq", timestamp, 0) +
                 varint(0) + b"\x00" + varint(0) + varint(1))


def make_pcap():
    host = b"example.test"
    handshake = frame(0, varint(774) + varint(len(host)) + host + struct.pack("!H", 25565) + varint(2))
    client_stream = handshake + frame(0x08, varint(5) + b"hello")
    first = bytes.fromhex("00112233445566778899aabbccddeeff")
    second = bytes.fromhex("102132435465768798a9babbdcddedef")
    t = 1_767_225_600_000
    server_stream = chat(first, "hi", t) + chat(second, "sample", t + 2000) + chat(first, "ok", t + 3000)
    frames = [
        packet("192.0.2.10", 40000, "198.51.100.20", 25565, 1000, client_stream, 1),
        packet("198.51.100.20", 25565, "192.0.2.10", 40000, 5000, server_stream, 2),
    ]
    header = struct.pack("<IHHIIII", 0xA1B2C3D4, 2, 4, 0, 0, 262144, 1)
    records = b"".join(struct.pack("<IIII", 1767225600 + i, 0, len(f), len(f)) + f
                       for i, f in enumerate(frames))
    return header + records


if __name__ == "__main__":
    target = Path(__file__).with_name("sample_game.pcap")
    target.write_bytes(make_pcap())
    print(target)
