"""Bounded analysis aid for a file-derived repeating XOR key. Never executes decoded data."""

from dataclasses import dataclass

MAX_FILE = 1_000_000


@dataclass(frozen=True)
class KeyRegion:
    label: str
    start: int
    length: int


def build_key(data: bytes, regions: list[KeyRegion]) -> bytes:
    if not data or len(data) > MAX_FILE or not 1 <= len(regions) <= 16:
        raise ValueError("invalid file size or region count")
    parts = []
    for region in regions:
        if region.start < 0 or region.length <= 0 or region.start + region.length > len(data):
            raise ValueError(f"invalid key region: {region.label}")
        parts.append(data[region.start:region.start + region.length])
    key = b"".join(parts)
    if len(key) > 4096:
        raise ValueError("key exceeds 4096 bytes")
    return key


def xor_cycle(data: bytes, key: bytes) -> bytes:
    if not key or len(data) > MAX_FILE:
        raise ValueError("empty key or oversized data")
    return bytes(value ^ key[index % len(key)] for index, value in enumerate(data))


def recover(data: bytes, regions: list[KeyRegion], offset: int, length: int) -> bytes:
    if offset < 0 or length <= 0 or offset + length > len(data):
        raise ValueError("invalid payload range")
    return xor_cycle(data[offset:offset + length], build_key(data, regions))


def crib_drag(ciphertext: bytes, crib: bytes, minimum_printable: int = 0) -> list[tuple[int, bytes, int]]:
    if not crib or len(crib) > len(ciphertext) or len(ciphertext) > MAX_FILE:
        raise ValueError("invalid crib or ciphertext")
    hits = []
    for offset in range(len(ciphertext) - len(crib) + 1):
        fragment = bytes(a ^ b for a, b in zip(ciphertext[offset:offset + len(crib)], crib))
        printable = sum(32 <= byte < 127 for byte in fragment)
        if printable >= minimum_printable:
            hits.append((offset, fragment, printable))
    return sorted(hits, key=lambda hit: (-hit[2], hit[0]))


def zero_ciphertext_tail(ciphertext: bytes, key: bytes, tail_start: int) -> bool:
    """Check the observed zero-ciphertext-tail condition; this does not prove its cause."""
    if not key or not 0 <= tail_start <= len(ciphertext):
        raise ValueError("invalid tail boundary")
    plaintext = xor_cycle(ciphertext, key)
    return all(
        ciphertext[i] == 0 and plaintext[i] == key[i % len(key)]
        for i in range(tail_start, len(ciphertext))
    )
