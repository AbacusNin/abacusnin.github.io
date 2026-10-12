#!/usr/bin/env python3
"""Read-only, bounded triage for one narrow class of ELF-like files."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

MAX_BYTES = 32 * 1024 * 1024


def inspect(data: bytes) -> dict:
    counts = Counter(data)
    size = len(data)
    prefix = data[:4]
    elf_like = len(data) >= 7 and prefix[:3] == b"\x7fEL"
    valid_ident = elf_like and data[4] in (1, 2) and data[5] in (1, 2) and data[6] == 1
    changed_magic = valid_ident and data[3] != ord("F")
    no_nulls = size >= 4096 and counts[0] == 0
    space_majority = size >= 4096 and counts[0x20] * 2 > size
    signals = []
    if changed_magic:
        signals.append("ELF-like identification with changed fourth magic byte")
    if no_nulls:
        signals.append("no NUL bytes in a file of at least 4096 bytes")
    if space_majority:
        signals.append("space bytes occupy more than half the file")
    candidate = changed_magic and no_nulls and space_majority
    return {
        "size": size,
        "prefix_hex": prefix.hex(),
        "elf_like_ident": bool(valid_ident),
        "zero_count": counts[0],
        "space_count": counts[0x20],
        "space_ratio": round(counts[0x20] / size, 4) if size else 0,
        "signals": signals,
        "review_lead": bool(candidate),
        "meaning": "heuristic review lead, not proof of maliciousness or original bytes",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        with args.file.open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        parser.error(str(exc))
    if len(data) > MAX_BYTES:
        parser.error("input exceeds 32 MiB limit")
    print(json.dumps(inspect(data), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
