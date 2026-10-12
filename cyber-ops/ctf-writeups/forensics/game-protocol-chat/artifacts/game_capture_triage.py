"""Offline triage for one cleartext, uncompressed Java game-protocol TCP flow."""

import argparse
import ipaddress
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path


MAX_CAPTURE = 32_000_000
MAX_RECORDS = 100_000
MAX_FRAME = 2_097_152


def pcap_segments(data):
    if len(data) < 24 or data[:4] != b"\xd4\xc3\xb2\xa1":
        raise ValueError("expected little-endian classic pcap")
    _, major, minor, _, _, _, link = struct.unpack_from("<IHHIIII", data)
    if (major, minor, link) != (2, 4, 1):
        raise ValueError("expected pcap v2.4 with Ethernet")
    pos = 24
    count = 0
    while pos < len(data):
        if pos + 16 > len(data):
            raise ValueError("truncated pcap record header")
        sec, usec, size, _wire_size = struct.unpack_from("<IIII", data, pos)
        pos += 16
        if size > 262_144 or pos + size > len(data):
            raise ValueError("invalid pcap record size")
        frame = data[pos:pos + size]
        pos += size
        count += 1
        if count > MAX_RECORDS:
            raise ValueError("too many records")
        if len(frame) < 54 or frame[12:14] != b"\x08\x00":
            continue
        ip = frame[14:]
        ihl = (ip[0] & 15) * 4
        if ip[0] >> 4 != 4 or ihl < 20 or len(ip) < ihl + 20 or ip[9] != 6:
            continue
        if int.from_bytes(ip[6:8], "big") & 0x1FFF:
            raise ValueError("IPv4 fragments are not supported")
        total = int.from_bytes(ip[2:4], "big")
        if total < ihl + 20 or len(ip) < total:
            raise ValueError("truncated IPv4 packet")
        tcp = ip[ihl:total]
        offset = (tcp[12] >> 4) * 4
        if offset < 20 or offset > len(tcp):
            raise ValueError("invalid TCP header")
        payload = tcp[offset:]
        if not payload:
            continue
        src = str(ipaddress.IPv4Address(ip[12:16]))
        dst = str(ipaddress.IPv4Address(ip[16:20]))
        sport = int.from_bytes(tcp[0:2], "big")
        dport = int.from_bytes(tcp[2:4], "big")
        seq = int.from_bytes(tcp[4:8], "big")
        yield count, (sec, usec), (src, sport, dst, dport), seq, payload


def reassemble(segments):
    if not segments:
        raise ValueError("empty stream")
    ordered = sorted(segments)
    first = ordered[0][0]
    out = bytearray()
    duplicates = 0
    for seq, payload in ordered:
        relative = seq - first
        if relative < 0:
            raise ValueError("TCP sequence wrap not supported")
        if relative > len(out):
            raise ValueError(f"TCP gap of {relative - len(out)} bytes")
        overlap = min(len(payload), len(out) - relative)
        if out[relative:relative + overlap] != payload[:overlap]:
            raise ValueError("conflicting TCP overlap")
        duplicates += overlap == len(payload)
        out.extend(payload[overlap:])
    return bytes(out), duplicates


def varint(data, pos):
    value = 0
    for index in range(5):
        if pos >= len(data):
            raise ValueError("short VarInt")
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << (7 * index)
        if byte < 128:
            if index == 4 and byte > 0x0F:
                raise ValueError("VarInt exceeds 32 bits")
            return value, pos
    raise ValueError("overlong VarInt")


def frames(data):
    pos = 0
    while pos < len(data):
        length, start = varint(data, pos)
        if not 1 <= length <= MAX_FRAME or start + length > len(data):
            raise ValueError(f"bad application frame at byte {pos}")
        packet_id, body_start = varint(data, start)
        if body_start > start + length:
            raise ValueError("packet ID extends past its frame")
        yield pos, packet_id, data[body_start:start + length]
        pos = start + length


def handshake(body):
    version, pos = varint(body, 0)
    host_length, pos = varint(body, pos)
    if host_length > 255 or pos + host_length + 2 >= len(body):
        raise ValueError("invalid handshake server address")
    pos += host_length
    declared_port = int.from_bytes(body[pos:pos + 2], "big")
    state, pos = varint(body, pos + 2)
    if pos != len(body) or state not in (1, 2):
        raise ValueError("invalid handshake next state")
    return {"protocol_version": version, "declared_port": declared_port, "next_state": state}


def player_chat(body):
    """Read only fields needed for triage; later NBT/filter fields are not decoded."""
    _, pos = varint(body, 0)
    sender = body[pos:pos + 16]
    if len(sender) != 16:
        raise ValueError("short sender UUID")
    pos += 16
    _, pos = varint(body, pos)
    if pos >= len(body):
        raise ValueError("short chat signature flag")
    signed = body[pos]
    pos += 1
    if signed == 1:
        pos += 256
    elif signed != 0:
        raise ValueError("invalid chat signature flag")
    text_length, pos = varint(body, pos)
    if text_length > 256 or pos + text_length + 8 > len(body):
        raise ValueError("invalid chat text length")
    text = body[pos:pos + text_length].decode("utf-8")
    pos += text_length
    timestamp = struct.unpack_from(">q", body, pos)[0]
    if not 946_684_800_000 <= timestamp <= 4_102_444_800_000:
        raise ValueError("chat timestamp outside 2000-2100")
    return sender, text, signed == 1, timestamp


def inspect(data, show_chat=False):
    if len(data) > MAX_CAPTURE:
        raise ValueError("capture too large")
    streams = defaultdict(list)
    packet_count = 0
    for number, _time, key, seq, payload in pcap_segments(data):
        packet_count = number
        streams[key].append((seq, payload))
    if len(streams) != 2:
        raise ValueError("expected one bidirectional TCP flow")
    first_key = next(iter(streams))
    second_key = (first_key[2], first_key[3], first_key[0], first_key[1])
    if second_key not in streams:
        raise ValueError("TCP directions do not pair")
    joined = {key: reassemble(parts) for key, parts in streams.items()}
    decoded = {key: list(frames(joined[key][0])) for key in streams}
    candidates = []
    for key, packet_list in decoded.items():
        if packet_list and packet_list[0][1] == 0:
            try:
                candidates.append((key, handshake(packet_list[0][2])))
            except ValueError:
                pass
    if len(candidates) != 1:
        raise ValueError("expected one valid initial handshake")
    client_key, hello = candidates[0]
    server_key = (client_key[2], client_key[3], client_key[0], client_key[1])
    sender_labels = {}
    chats = []
    for offset, packet_id, body in decoded[server_key]:
        if packet_id != 0x3F:
            continue
        try:
            sender, message, signed, when = player_chat(body)
        except (ValueError, UnicodeError):
            continue
        label = sender_labels.setdefault(sender, f"sender_{len(sender_labels) + 1}")
        item = {"sender": label, "offset": offset, "length": len(message), "signed": signed,
                "relative_ms": when - chats[0]["timestamp_ms"] if chats else 0,
                "timestamp_ms": when}
        if show_chat:
            item["message"] = message
        chats.append(item)
    for item in chats:
        item.pop("timestamp_ms")
    return {"pcap_records": packet_count, "protocol_version": hello["protocol_version"],
            "next_state": hello["next_state"], "declared_port": hello["declared_port"],
            "client_frames": len(decoded[client_key]), "server_frames": len(decoded[server_key]),
            "client_payload_bytes": len(joined[client_key][0]),
            "server_payload_bytes": len(joined[server_key][0]),
            "tcp_duplicate_segments": joined[client_key][1] + joined[server_key][1],
            "client_chat_id_08_count": sum(pid == 0x08 for _, pid, _ in decoded[client_key]),
            "server_player_chat_count": len(chats), "chats": chats,
            "warning": "Packet ID 0x3F is version-specific; chat parsing is partial and requires state review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--show-chat", action="store_true", help="print decoded chat text locally")
    args = parser.parse_args()
    with args.capture.open("rb") as handle:
        data = handle.read(MAX_CAPTURE + 1)
    print(json.dumps(inspect(data, show_chat=args.show_chat), indent=2))


if __name__ == "__main__":
    main()
