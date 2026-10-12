"""Bounded offline builder and decoder for one CAT048 FSPEC layout."""

import argparse
import json
from pathlib import Path


FSPEC = bytes.fromhex("fdd2")
RECORD_SIZE = 29
MAX_BLOCK = 65535
MAX_FILE = 1024 * 1024


def _integer(value, maximum, name):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f"{name} must be an integer from 0 to {maximum}")
    return value


def encode_mode3a(code):
    if not isinstance(code, str) or len(code) != 4 or any(ch not in "01234567" for ch in code):
        raise ValueError("Mode-3/A must be four octal digits")
    return int(code, 8).to_bytes(2, "big")


def decode_mode3a(raw):
    value = int.from_bytes(raw, "big")
    if value & 0xF000:
        raise ValueError("unsupported Mode-3/A V/G/L or spare bits")
    return f"{value:04o}"


def encode_ident(text):
    if not isinstance(text, str) or len(text) > 8 or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 " for ch in text):
        raise ValueError("callsign must use up to eight uppercase letters, digits, or spaces")
    value = 0
    for ch in text.ljust(8):
        code = ord(ch) - 64 if "A" <= ch <= "Z" else ord(ch)
        value = (value << 6) | code
    return value.to_bytes(6, "big")


def decode_ident(raw):
    value = int.from_bytes(raw, "big")
    chars = []
    for shift in range(42, -1, -6):
        code = (value >> shift) & 0x3F
        if 1 <= code <= 26:
            chars.append(chr(code + 64))
        elif 48 <= code <= 57 or code == 32:
            chars.append(chr(code))
        else:
            raise ValueError("unsupported aircraft-identification code")
    return "".join(chars).rstrip()


def build_record(sac, sic, track_number, mode_s, mode3a, callsign, spi=False):
    _integer(sac, 255, "SAC")
    _integer(sic, 255, "SIC")
    _integer(track_number, 4095, "track number")
    _integer(mode_s, 0xFFFFFF, "Mode-S address")
    if type(spi) is not bool:
        raise ValueError("SPI must be a boolean")
    return b"".join((
        FSPEC,
        bytes((sac, sic)),                    # I048/010
        bytes.fromhex("000100"),             # I048/140 invented time of day
        bytes((0xA9 if spi else 0xA1, 0x02)), # I048/020, first extent ends
        bytes.fromhex("20004000"),           # I048/040 invented polar position
        encode_mode3a(mode3a),               # I048/070
        bytes.fromhex("0050"),               # I048/090 invented flight level
        mode_s.to_bytes(3, "big"),           # I048/220
        encode_ident(callsign),              # I048/240
        track_number.to_bytes(2, "big"),     # I048/161
        b"\x40",                            # I048/170 track status, no extent
    ))


def build_block(records):
    payload = b"".join(records)
    if not records or any(len(record) != RECORD_SIZE for record in records) or len(payload) + 3 > MAX_BLOCK:
        raise ValueError("block needs fixed-size records and a 16-bit total length")
    return b"\x30" + (len(payload) + 3).to_bytes(2, "big") + payload


def decode_record(raw):
    if len(raw) != RECORD_SIZE or raw[:2] != FSPEC:
        raise ValueError("unsupported record length or FSPEC")
    if raw[7] & 1 != 1 or raw[8] & 1 or raw[28] & 1 or raw[26] & 0xF0:
        raise ValueError("unsupported descriptor or track-status extent")
    return {
        "sac": raw[2], "sic": raw[3],
        "track_number": int.from_bytes(raw[26:28], "big") & 0x0FFF,
        "spi": bool(raw[7] & 0x08),
        "mode3a": decode_mode3a(raw[13:15]),
        "mode_s": f"{int.from_bytes(raw[17:20], 'big'):06X}",
        "callsign": decode_ident(raw[20:26]),
        "fspec": raw[:2].hex(), "record_length": len(raw),
    }


def decode_blocks(data):
    if not data or len(data) > MAX_FILE:
        raise ValueError("capture must contain 1 to 1048576 bytes")
    blocks = []
    cursor = 0
    while cursor < len(data):
        if len(data) - cursor < 3 or data[cursor] != 0x30:
            raise ValueError("truncated header or unexpected ASTERIX category")
        length = int.from_bytes(data[cursor + 1:cursor + 3], "big")
        if length < 3 + RECORD_SIZE or cursor + length > len(data) or (length - 3) % RECORD_SIZE:
            raise ValueError("invalid block length for this fixed record layout")
        body = data[cursor + 3:cursor + length]
        records = [decode_record(body[i:i + RECORD_SIZE]) for i in range(0, len(body), RECORD_SIZE)]
        blocks.append({"length": length, "records": records})
        cursor += length
    return blocks


def main():
    parser = argparse.ArgumentParser(description="Offline CAT048 fixed-subset demo or decode")
    parser.add_argument("--decode", type=Path, help="decode a local binary capture (up to 1 MiB)")
    args = parser.parse_args()
    if args.decode:
        if args.decode.stat().st_size > MAX_FILE:
            parser.error("capture exceeds 1 MiB")
        data = args.decode.read_bytes()
    else:
        data = build_block([
            build_record(10, 1, 256, 0xA1B2C3, "7040", "SAMPLE01"),
            build_record(10, 1, 256, 0x0BADFF, "7500", "SAMPLE01", spi=True),
        ])
    print(json.dumps({"blocks": decode_blocks(data)}, indent=2))


if __name__ == "__main__":
    main()
