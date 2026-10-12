"""Find structurally plausible BitLocker recovery passwords without printing them."""

import argparse
import json
import re
from pathlib import Path

GROUP = re.compile(r"[0-9]{6}\Z")
FULL = re.compile(r"(?<![0-9])(?:[0-9]{6}-){7}[0-9]{6}(?![0-9])")
PARTIAL = re.compile(r"(?<![0-9])(?:[0-9]{6}-){7}[0-9]{2}\?{4}(?![0-9])")
MAX_TEXT_BYTES = 1024 * 1024


def valid_group(group):
    if not GROUP.fullmatch(group):
        return False
    value = int(group)
    return value % 11 == 0 and value // 11 < 65536


def count_completions(prefix):
    if not re.fullmatch(r"[0-9]{2}", prefix):
        raise ValueError("prefix must be exactly two ASCII digits")
    low = int(prefix) * 10_000
    high = low + 10_000
    return sum(valid_group(f"{candidate:06d}") for candidate in range(low, high))


def scan(text):
    full_matches = list(FULL.finditer(text))
    partial_matches = list(PARTIAL.finditer(text))
    valid_full = sum(all(valid_group(group) for group in hit.group().split("-")) for hit in full_matches)
    valid_partial = [hit for hit in partial_matches if all(valid_group(group) for group in hit.group().split("-")[:7])]
    return {
        "full_shapes": len(full_matches),
        "structurally_valid_full": valid_full,
        "partial_shapes": len(partial_matches),
        "structurally_valid_partial": len(valid_partial),
        "completion_counts": [count_completions(hit.group().split("-")[-1][:2]) for hit in valid_partial],
        "note": "Format validity does not prove a candidate unlocks any volume. No key text is emitted.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", help="local UTF-8 transcription or document export")
    args = parser.parse_args()
    path = Path(args.document)
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError("document exceeds 1 MiB bound")
        print(json.dumps(scan(path.read_text(encoding="utf-8")), indent=2))
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(2, f"scan failed: {exc}\n")


if __name__ == "__main__":
    main()
