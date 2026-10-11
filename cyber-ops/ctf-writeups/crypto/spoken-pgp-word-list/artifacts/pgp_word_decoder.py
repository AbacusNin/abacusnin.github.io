#!/usr/bin/env python3
"""Decode ordered PGP Word List tokens without speech recognition or decryption."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

MAX_TOKENS = 100_000
WORD = re.compile(r"[A-Za-z][A-Za-z0-9-]*\Z")


def load_table(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    """Read a complete hex/even/odd TSV from an independently obtained word list."""
    if path.stat().st_size > 100_000:
        raise ValueError("word table exceeds 100 KB")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader((line for line in stream if not line.startswith("#")), delimiter="\t"))
    return parse_table(rows)


def parse_table(rows: list[dict[str, str]]) -> tuple[dict[str, int], dict[str, int]]:
    """Validate all byte indexes and both word columns before decoding."""
    if len(rows) != 256:
        raise ValueError("word table must have exactly 256 data rows")
    tables: tuple[dict[str, int], dict[str, int]] = ({}, {})
    values = set()
    all_words = set()
    for row in rows:
        try:
            raw_hex = row["hex"].strip()
            even = row["even"].strip().casefold()
            odd = row["odd"].strip().casefold()
            if not re.fullmatch(r"[0-9A-Fa-f]{2}", raw_hex):
                raise ValueError("byte column must contain two hex digits")
            value = int(raw_hex, 16)
            if not WORD.fullmatch(even) or not WORD.fullmatch(odd):
                raise ValueError("word columns must contain one alphabetic word")
            if value in values or even in all_words or odd in all_words or even == odd:
                raise ValueError("duplicate byte or word")
        except (KeyError, AttributeError) as exc:
            raise ValueError("expected TSV columns: hex, even, odd") from exc
        values.add(value)
        all_words.update((even, odd))
        tables[0][even] = value
        tables[1][odd] = value
    if values != set(range(256)):
        raise ValueError("word table must cover every byte from 00 through FF")
    return tables


def decode(tokens: list[str], tables: tuple[dict[str, int], dict[str, int]]) -> bytes:
    if not tokens or len(tokens) > MAX_TOKENS:
        raise ValueError(f"expected 1 to {MAX_TOKENS} ordered words")
    result = bytearray()
    for position, token in enumerate(tokens):
        word = token.casefold()
        if word not in tables[position % 2]:
            side = "even" if position % 2 == 0 else "odd"
            raise ValueError(f"word {position} is missing from the {side} list: {token}")
        result.append(tables[position % 2][word])
    return bytes(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wordlist", required=True, type=Path, help="complete tab-separated hex/even/odd table")
    parser.add_argument("--tokens", default="-", help="one word per line, or - for stdin")
    parser.add_argument("--format", choices=("hex", "ascii"), default="hex")
    args = parser.parse_args()
    try:
        tables = load_table(args.wordlist)
        if args.tokens == "-":
            raw = sys.stdin.buffer.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ValueError("token stream exceeds 2 MB")
            words = raw.decode("utf-8-sig").split()
        else:
            token_path = Path(args.tokens)
            if token_path.stat().st_size > 2_000_000:
                raise ValueError("token file exceeds 2 MB")
            words = token_path.read_text(encoding="utf-8-sig").split()
        output = decode(words, tables)
        if args.format == "ascii":
            print(output.decode("ascii"), end="")
        else:
            print(output.hex())
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"decode failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
