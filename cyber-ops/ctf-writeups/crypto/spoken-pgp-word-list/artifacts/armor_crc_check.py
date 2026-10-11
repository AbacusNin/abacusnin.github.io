#!/usr/bin/env python3
"""Check a legacy OpenPGP ASCII armor wrapper, Base64, and optional CRC-24."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 1_000_000
BASE64_LINE = re.compile(r"[A-Za-z0-9+/]+={0,2}\Z")


def crc24(data: bytes) -> int:
    value = 0xB704CE
    for byte in data:
        value ^= byte << 16
        for _ in range(8):
            value <<= 1
            if value & 0x1000000:
                value ^= 0x1864CFB
    return value & 0xFFFFFF


def inspect_armor(data: bytes) -> dict:
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("armor must be ASCII") from exc
    lines = text.splitlines()
    if len(lines) < 5 or lines[0] != "-----BEGIN PGP MESSAGE-----" or lines[-1] != "-----END PGP MESSAGE-----":
        raise ValueError("expected one complete PGP MESSAGE armor block")
    blank = 1
    while blank < len(lines) and lines[blank]:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]*: [ -~]+", lines[blank]):
            raise ValueError("malformed armor header")
        blank += 1
    if blank >= len(lines) - 2:
        raise ValueError("missing blank line and encoded body")
    body = lines[blank + 1:-1]
    stated = None
    if body[-1].startswith("="):
        checksum = body.pop()
        if not re.fullmatch(r"=[A-Za-z0-9+/]{4}", checksum):
            raise ValueError("malformed CRC-24 line")
        try:
            stated_bytes = base64.b64decode(checksum[1:], validate=True)
        except binascii.Error as exc:
            raise ValueError("invalid CRC-24 Base64") from exc
        if len(stated_bytes) != 3:
            raise ValueError("CRC-24 must decode to three bytes")
        stated = int.from_bytes(stated_bytes, "big")
    if not body or any(not BASE64_LINE.fullmatch(line) for line in body):
        raise ValueError("malformed encoded body")
    if any(len(line) != 64 for line in body[:-1]) or len(body[-1]) > 64:
        raise ValueError("encoded body lines must wrap at 64 characters")
    try:
        packet = base64.b64decode("".join(body), validate=True)
    except binascii.Error as exc:
        raise ValueError("invalid body Base64") from exc
    if not packet:
        raise ValueError("empty decoded body")
    computed = crc24(packet)
    return {
        "encoded_lines": len(body),
        "packet_bytes": len(packet),
        "packet_sha256": hashlib.sha256(packet).hexdigest(),
        "crc24_present": stated is not None,
        "crc24_computed": f"{computed:06X}",
        "crc24_stated": f"{stated:06X}" if stated is not None else None,
        "crc24_match": computed == stated if stated is not None else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("armor", type=Path)
    args = parser.parse_args()
    try:
        if args.armor.is_symlink():
            raise ValueError("symbolic links are not read")
        if args.armor.stat().st_size > MAX_BYTES:
            raise ValueError("armor exceeds 1 MB")
        result = inspect_armor(args.armor.read_bytes())
        print(json.dumps(result, indent=2))
        return 1 if result["crc24_match"] is False else 0
    except (OSError, ValueError) as exc:
        print(f"armor check failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
