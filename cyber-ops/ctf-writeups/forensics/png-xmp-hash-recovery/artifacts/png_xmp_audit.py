#!/usr/bin/env python3
"""Read PNG XMP UserComment fields and flag 128-hex-character values for review."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_FILE = 20_000_000
MAX_CHUNKS = 10_000
MAX_XMP = 1_000_000
COMMENT_TAG = "{http://ns.adobe.com/exif/1.0/}UserComment"
DIGEST = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{128}(?![0-9A-Fa-f])")


def png_chunks(data: bytes):
    if not data.startswith(PNG_MAGIC):
        raise ValueError("missing PNG signature")
    offset = len(PNG_MAGIC)
    count = 0
    ended = False
    has_image_data = False
    while offset < len(data):
        if count >= MAX_CHUNKS or len(data) - offset < 12:
            raise ValueError("chunk count or framing limit exceeded")
        length = struct.unpack_from(">I", data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("truncated PNG chunk")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        if count == 0 and (kind != b"IHDR" or length != 13):
            raise ValueError("missing or malformed first IHDR chunk")
        if kind == b"IHDR" and count != 0:
            raise ValueError("duplicate IHDR chunk")
        if kind == b"IDAT":
            has_image_data = True
        if kind == b"IEND" and (length != 0 or not has_image_data):
            raise ValueError("malformed IEND or missing IDAT")
        stated_crc = struct.unpack_from(">I", data, offset + 8 + length)[0]
        if zlib.crc32(kind + payload) & 0xFFFFFFFF != stated_crc:
            raise ValueError(f"bad CRC for PNG chunk {kind!r}")
        yield kind, payload
        count += 1
        offset = end
        if kind == b"IEND":
            ended = True
            break
    if not ended or offset != len(data):
        raise ValueError("missing IEND or trailing bytes")


def itxt_xmp(payload: bytes) -> bytes | None:
    keyword, separator, rest = payload.partition(b"\x00")
    if not separator or keyword != b"XML:com.adobe.xmp":
        return None
    if len(rest) < 2:
        raise ValueError("truncated XMP iTXt header")
    compressed, method = rest[:2]
    if compressed not in (0, 1) or method != 0:
        raise ValueError("unsupported XMP iTXt compression")
    language, separator, rest = rest[2:].partition(b"\x00")
    if not separator:
        raise ValueError("missing iTXt language separator")
    translated, separator, raw = rest.partition(b"\x00")
    if not separator:
        raise ValueError("missing iTXt translated-keyword separator")
    if compressed:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(raw, MAX_XMP + 1)
        if len(raw) > MAX_XMP or decoder.unconsumed_tail or not decoder.eof or decoder.unused_data:
            raise ValueError("compressed XMP exceeds limit or is malformed")
    if len(raw) > MAX_XMP:
        raise ValueError("XMP exceeds 1 MB")
    return raw


def scan(data: bytes, show_digests: bool = False) -> dict:
    if len(data) > MAX_FILE:
        raise ValueError("PNG exceeds 20 MB")
    chunk_count = xmp_count = comment_count = 0
    values: list[str] = []
    triple = False
    for kind, payload in png_chunks(data):
        chunk_count += 1
        if kind != b"iTXt":
            continue
        raw = itxt_xmp(payload)
        if raw is None:
            continue
        xmp_count += 1
        if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
            raise ValueError("XMP declarations are not accepted")
        try:
            root = ET.fromstring(raw.decode("utf-8-sig"))
        except (UnicodeError, ET.ParseError) as exc:
            raise ValueError("malformed XMP XML") from exc
        for element in root.iter(COMMENT_TAG):
            comment_count += 1
            comment = "".join(element.itertext()).strip()
            matches = DIGEST.findall(comment)
            values.extend(matches)
            if re.fullmatch(r"[0-9A-Fa-f]{128}(?:-[0-9A-Fa-f]{128}){2}", comment):
                triple = True
    result = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "chunks": chunk_count,
        "xmp_packets": xmp_count,
        "usercomment_fields": comment_count,
        "candidate_512_bit_values": len(values),
        "three_value_pattern": triple,
        "assessment": "review candidate; algorithm and meaning are unverified" if values else "no 128-hex UserComment values found",
    }
    if show_digests:
        result["digests"] = values
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("png", type=Path)
    parser.add_argument("--show-digests", action="store_true", help="print candidate values for authorized local analysis")
    args = parser.parse_args()
    try:
        if args.png.is_symlink():
            raise ValueError("symbolic links are not read")
        if args.png.stat().st_size > MAX_FILE:
            raise ValueError("PNG exceeds 20 MB")
        result = scan(args.png.read_bytes(), args.show_digests)
        print(json.dumps(result, indent=2))
        return 1 if result["candidate_512_bit_values"] else 0
    except (OSError, ValueError) as exc:
        print(f"scan failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
