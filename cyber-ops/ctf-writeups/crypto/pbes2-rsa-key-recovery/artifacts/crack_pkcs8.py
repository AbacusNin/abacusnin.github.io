#!/usr/bin/env python3
"""Bounded local dictionary check for an encrypted PKCS#8 PEM key."""

import argparse
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_private_key


def find_password(pem, candidates, limit=10000):
    if b"-----BEGIN ENCRYPTED PRIVATE KEY-----" not in pem[:80]:
        raise ValueError("expected an ENCRYPTED PRIVATE KEY PEM")
    if not 1 <= limit <= 100000:
        raise ValueError("candidate limit must be between 1 and 100000")
    for line_number, raw in enumerate(candidates, 1):
        if line_number > limit:
            break
        password = raw.rstrip(b"\r\n")
        if not password or len(password) > 256:
            continue
        try:
            key = load_pem_private_key(pem, password=password)
        except (ValueError, TypeError):
            continue
        return line_number, password, key
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("key", type=Path)
    parser.add_argument("wordlist", type=Path)
    parser.add_argument("--limit", type=int, default=10000)
    parser.add_argument("--reveal", action="store_true", help="print the recovered passphrase to this terminal")
    args = parser.parse_args()
    try:
        if args.key.stat().st_size > 1024 * 1024:
            parser.error("key file exceeds 1 MiB")
        pem = args.key.read_bytes()
        with args.wordlist.open("rb") as candidates:
            found = find_password(pem, candidates, args.limit)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if found is None:
        print("No match within the candidate limit.")
        return 1
    line_number, password, key = found
    print(f"Matched wordlist line {line_number}; {type(key).__name__}, {key.key_size} bits.")
    if args.reveal:
        print("Passphrase (explicit reveal):", password.decode("latin-1"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
