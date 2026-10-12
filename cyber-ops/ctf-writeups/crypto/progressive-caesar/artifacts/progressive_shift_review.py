#!/usr/bin/env python3
"""Bounded offline reviewer for positional alphabet shifts."""
import argparse
from pathlib import Path

MAX_BYTES = 4096


def decode(ciphertext, step, basis):
    if basis not in ("absolute", "letters"):
        raise ValueError("unknown index basis")
    out = []
    letter_index = 0
    for absolute_index, ch in enumerate(ciphertext):
        if ch.isascii() and ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            index = absolute_index if basis == "absolute" else letter_index
            out.append(chr(base + (ord(ch) - base + index * step) % 26))
            letter_index += 1
        else:
            out.append(ch)
    return "".join(out)


def candidates(ciphertext, crib):
    if not ciphertext or len(ciphertext) > MAX_BYTES:
        raise ValueError("ciphertext must contain 1 to 4096 characters")
    if not crib or len(crib) > len(ciphertext):
        raise ValueError("crib must fit inside ciphertext")
    if any(ord(c) < 32 or ord(c) > 126 for c in ciphertext + crib):
        raise ValueError("ASCII printable input only")
    results = []
    for basis in ("absolute", "letters"):
        for step in range(26):
            plain = decode(ciphertext, step, basis)
            if plain.startswith(crib):
                results.append({"basis": basis, "step": step, "plaintext": plain})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ciphertext_file", help="Local UTF-8 file with one ciphertext line")
    parser.add_argument("--crib", required=True, help="Known plaintext prefix")
    args = parser.parse_args()
    path = Path(args.ciphertext_file)
    if path.stat().st_size > MAX_BYTES:
        parser.error("ciphertext file exceeds 4096 bytes")
    try:
        ciphertext = path.read_text(encoding="utf-8").rstrip("\r\n")
        found = candidates(ciphertext, args.crib)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))
    for item in found:
        print(f"{item['basis']} step={item['step']}: {item['plaintext']}")
    if not found:
        print("No matching positional-shift candidate")


if __name__ == "__main__":
    main()
