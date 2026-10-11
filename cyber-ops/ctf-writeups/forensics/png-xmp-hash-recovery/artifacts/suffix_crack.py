#!/usr/bin/env python3
"""Recover word-plus-numeric-suffix preimages of authorized, unsalted fast hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

MAX_WORDLIST = 10_000_000
MAX_HASH_FILE = 10_000
MAX_HASHES = 16
ALGORITHMS = ("blake2b", "sha512", "sha3_512", "sha256", "sha384", "blake2s")
WORD = re.compile(r"[A-Za-z]+\Z")


def load_hashes(path: Path, algorithm: str) -> list[str]:
    if path.stat().st_size > MAX_HASH_FILE:
        raise ValueError("hash file exceeds 10 KB")
    width = hashlib.new(algorithm).digest_size * 2
    values = [line.strip().lower() for line in path.read_text(encoding="ascii").splitlines() if line.strip()]
    if not 1 <= len(values) <= MAX_HASHES or any(not re.fullmatch(rf"[0-9a-f]{{{width}}}", value) for value in values):
        raise ValueError(f"expected 1-{MAX_HASHES} plain {width}-hex-character {algorithm} digests")
    return values


def crack(words: list[str], hashes: list[str], algorithm: str = "blake2b", suffix_width: int = 3,
          max_candidates: int = 1_000_000, case: str = "lower") -> tuple[list[str | None], int, bool]:
    if not 1 <= suffix_width <= 4 or max_candidates < 1:
        raise ValueError("suffix width must be 1-4 and candidate cap must be positive")
    wanted: dict[str, list[int]] = {}
    for index, digest in enumerate(hashes):
        wanted.setdefault(digest.lower(), []).append(index)
    found: list[str | None] = [None] * len(hashes)
    attempts = 0
    for raw in words:
        word = raw.strip()
        if case == "lower":
            word = word.lower()
        if not WORD.fullmatch(word):
            continue
        prefix = hashlib.new(algorithm)
        prefix.update(word.encode("ascii"))
        for number in range(10 ** suffix_width):
            if attempts >= max_candidates:
                return found, attempts, True
            suffix = f"{number:0{suffix_width}d}"
            candidate = prefix.copy()
            candidate.update(suffix.encode("ascii"))
            attempts += 1
            digest = candidate.hexdigest()
            if digest in wanted:
                for index in wanted.pop(digest):
                    found[index] = word + suffix
                if not wanted:
                    return found, attempts, False
    return found, attempts, False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wordlist", type=Path)
    parser.add_argument("hash_file", type=Path, help="one digest per line, in desired output order")
    parser.add_argument("--algorithm", choices=ALGORITHMS, default="blake2b")
    parser.add_argument("--suffix-width", type=int, default=3)
    parser.add_argument("--case", choices=("lower", "as-is"), default="lower")
    parser.add_argument("--max-candidates", type=int, default=1_000_000)
    args = parser.parse_args()
    try:
        if args.wordlist.is_symlink() or args.hash_file.is_symlink():
            raise ValueError("symbolic links are not read")
        if args.wordlist.stat().st_size > MAX_WORDLIST:
            raise ValueError("wordlist exceeds 10 MB")
        hashes = load_hashes(args.hash_file, args.algorithm)
        words = args.wordlist.read_text(encoding="utf-8-sig").splitlines()
        recovered, attempts, capped = crack(words, hashes, args.algorithm, args.suffix_width,
                                             args.max_candidates, args.case)
        print(json.dumps({"algorithm": args.algorithm, "suffix_width": args.suffix_width,
                          "attempts": attempts, "candidate_cap_reached": capped,
                          "recovered": recovered}, indent=2))
        return 2 if capped else 1 if any(value is None for value in recovered) else 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"recovery failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
