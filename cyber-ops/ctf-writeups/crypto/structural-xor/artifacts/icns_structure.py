"""Shallow ICNS container-structure check. Does not validate icon image payloads."""

import struct

MAX_FILE = 1_000_000


def inspect(data: bytes) -> dict:
    if len(data) > MAX_FILE:
        raise ValueError("file exceeds 1 MB local review bound")
    if not data.startswith(b"icns"):
        return {"kind": "not_icns", "valid_structure": None, "reason": "no icns magic"}
    if len(data) < 8:
        return {"kind": "icns_claim", "valid_structure": False, "reason": "truncated header"}
    declared = struct.unpack(">I", data[4:8])[0]
    if declared != len(data):
        return {"kind": "icns_claim", "valid_structure": False, "reason": "declared length differs from file length"}
    offset = 8
    chunks = 0
    while offset < len(data):
        if offset + 8 > len(data):
            return {"kind": "icns_claim", "valid_structure": False, "reason": "truncated element header"}
        size = struct.unpack(">I", data[offset + 4:offset + 8])[0]
        if size < 8 or offset + size > len(data):
            return {"kind": "icns_claim", "valid_structure": False, "reason": "invalid element length"}
        offset += size
        chunks += 1
    return {"kind": "icns_claim", "valid_structure": bool(chunks), "reason": "element lengths parsed" if chunks else "no elements"}
