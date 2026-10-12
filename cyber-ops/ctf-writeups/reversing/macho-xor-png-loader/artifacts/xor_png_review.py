#!/usr/bin/env python3
"""Bounded, offline review of a candidate repeating-XOR PNG blob."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zlib

PNG_PREFIX = bytes.fromhex("89504e470d0a1a0a0000000d49484452")
MAX_INPUT = 32 * 1024 * 1024
MAX_BLOB = 16 * 1024 * 1024
MAX_INFLATED = 64 * 1024 * 1024


def parse_png(data: bytes) -> dict:
    if not data.startswith(PNG_PREFIX):
        raise ValueError("PNG signature or IHDR prefix mismatch")
    pos = 8
    chunks = []
    idat = bytearray()
    width = height = None
    while pos + 12 <= len(data):
        size = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + size
        if size > MAX_BLOB or end > len(data):
            raise ValueError("chunk length exceeds blob")
        payload = data[pos + 8:pos + 8 + size]
        expected = int.from_bytes(data[pos + 8 + size:end], "big")
        if zlib.crc32(kind + payload) & 0xffffffff != expected:
            raise ValueError("chunk CRC mismatch")
        if not chunks:
            if kind != b"IHDR" or size != 13:
                raise ValueError("first chunk must be 13-byte IHDR")
            width = int.from_bytes(payload[:4], "big")
            height = int.from_bytes(payload[4:8], "big")
            if not width or not height or width * height > 10_000_000:
                raise ValueError("invalid or oversized dimensions")
            if payload[10] != 0 or payload[11] != 0 or payload[12] not in (0, 1):
                raise ValueError("unsupported IHDR method")
        elif kind == b"IHDR":
            raise ValueError("duplicate IHDR")
        if kind == b"IDAT":
            idat.extend(payload)
        if kind == b"IEND":
            if size or not idat or end != len(data):
                raise ValueError("invalid IEND or trailing bytes")
            stream = zlib.decompressobj()
            inflated = stream.decompress(bytes(idat), MAX_INFLATED + 1)
            if len(inflated) > MAX_INFLATED or stream.unconsumed_tail or not stream.eof or stream.unused_data:
                raise ValueError("invalid or oversized IDAT stream")
            chunks.append("IEND")
            return {"width": width, "height": height, "chunks": chunks,
                    "inflated_bytes": len(inflated)}
        if not all(65 <= b <= 90 or 97 <= b <= 122 for b in kind):
            raise ValueError("invalid chunk type")
        chunks.append(kind.decode("ascii"))
        pos = end
    raise ValueError("missing IEND")


def decode(blob: bytes, key: bytes) -> bytes:
    if not key or len(key) > 64:
        raise ValueError("key must contain 1 to 64 bytes")
    return bytes(value ^ key[i % len(key)] for i, value in enumerate(blob))


def review(blob: bytes, candidate_key: bytes | None = None) -> tuple[dict, bytes | None]:
    if len(blob) < len(PNG_PREFIX) or len(blob) > MAX_BLOB:
        raise ValueError("blob length outside supported range")
    prefix = bytes(a ^ b for a, b in zip(blob[:16], PNG_PREFIX))
    candidates = []
    if candidate_key is not None:
        candidates.append(("supplied", candidate_key))
    for n in range(1, 17):
        key = prefix[:n]
        if all(prefix[i] == key[i % n] for i in range(16)):
            candidates.append(("prefix-period", key))
    for method, key in candidates:
        plain = decode(blob, key)
        try:
            structure = parse_png(plain)
        except (ValueError, zlib.error):
            continue
        return ({"review_lead": True, "method": method, "key_length": len(key),
                 "blob_sha256": hashlib.sha256(blob).hexdigest(),
                 "png_structure": structure,
                 "meaning": "syntactic and CRC checks only; image pixels and intent unverified"}, plain)
    return ({"review_lead": False, "tested_key_lengths": list(range(1, 17)),
             "supplied_key_tested": candidate_key is not None,
             "meaning": "no validated PNG candidate under these assumptions"}, None)


def read_limited(path: Path, limit: int) -> bytes:
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f"input exceeds {limit} bytes")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="raw blob or binary containing the blob")
    parser.add_argument("--offset", type=lambda x: int(x, 0), default=0)
    parser.add_argument("--size", type=lambda x: int(x, 0))
    parser.add_argument("--candidate-key-file", type=Path)
    parser.add_argument("--output", type=Path, help="write validated candidate PNG")
    args = parser.parse_args()
    try:
        data = read_limited(args.file, MAX_INPUT)
        if args.offset < 0 or args.offset > len(data):
            raise ValueError("offset outside file")
        size = args.size if args.size is not None else len(data) - args.offset
        if size < 16 or size > MAX_BLOB or args.offset + size > len(data):
            raise ValueError("blob size outside file or supported range")
        key = read_limited(args.candidate_key_file, 64) if args.candidate_key_file else None
        result, plain = review(data[args.offset:args.offset + size], key)
        if args.output:
            if plain is None:
                raise ValueError("no validated candidate to write")
            with args.output.open("xb") as output:
                output.write(plain)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
