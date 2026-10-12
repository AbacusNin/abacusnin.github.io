"""Offline, bounded scan for one-byte XOR copies of known strings.

Use on files you are authorized to inspect. A match is a review lead, not a
malware verdict. The module also exposes strict hex and prefix-recovery helpers.
"""

import argparse
import json
from pathlib import Path

MAX_FILE_BYTES = 20_000_000
MAX_MATCHES = 100


def decode_hex(text):
    compact = text.strip()
    if not compact or len(compact) % 2 or any(c not in "0123456789abcdefABCDEF" for c in compact):
        raise ValueError("expected a nonempty, even-length hex string")
    return bytes.fromhex(compact)


def recover_prefix_key(ciphertext, known_prefix):
    if not ciphertext or not known_prefix or len(known_prefix) > len(ciphertext):
        raise ValueError("anchor must be nonempty and no longer than ciphertext")
    keys = bytes(c ^ p for c, p in zip(ciphertext, known_prefix))
    if len(set(keys)) != 1:
        return None
    return keys[0]


def xor_bytes(data, key):
    if not isinstance(key, int) or isinstance(key, bool) or not 0 <= key <= 255:
        raise ValueError("key must be one byte")
    return bytes(value ^ key for value in data)


def scan(data, anchors, max_matches=MAX_MATCHES):
    if not isinstance(data, bytes) or len(data) > MAX_FILE_BYTES:
        raise ValueError("data must be bytes no larger than 20 MB")
    if not 1 <= len(anchors) <= 16 or not 1 <= max_matches <= MAX_MATCHES:
        raise ValueError("supply 1-16 anchors and a bounded match limit")
    if any(not isinstance(a, bytes) or not 6 <= len(a) <= 128 or not a.isascii() for a in anchors):
        raise ValueError("anchors must be ASCII byte strings of length 6-128")
    results = []
    for anchor in anchors:
        size = len(anchor)
        for offset in range(len(data) - size + 1):
            key = data[offset] ^ anchor[0]
            if key == 0:
                continue
            if all(data[offset + i] ^ key == expected for i, expected in enumerate(anchor[1:], 1)):
                results.append({"offset": offset, "key_hex": f"{key:02x}",
                                "anchor_ascii": anchor.decode("ascii")})
                if len(results) >= max_matches:
                    return results
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="local sample; no execution or network access")
    parser.add_argument("--anchor", action="append", required=True,
                        help="known ASCII string, 6-128 bytes; repeat up to 16 times")
    args = parser.parse_args()
    try:
        if not args.file.is_file() or args.file.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("file missing or exceeds 20 MB")
        anchors = [value.encode("ascii") for value in args.anchor]
        matches = scan(args.file.read_bytes(), anchors)
    except (UnicodeEncodeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps({"file": args.file.name, "matches": matches, "truncated": len(matches) >= MAX_MATCHES}, indent=2))


if __name__ == "__main__":
    main()
