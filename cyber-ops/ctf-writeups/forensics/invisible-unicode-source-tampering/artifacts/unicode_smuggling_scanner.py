#!/usr/bin/env python3
"""Read-only source scanner for Unicode Tags and selected invisible controls.

Exit 0: no findings. Exit 1: findings. Exit 2: unreadable or oversized input.
The scanner never imports, compiles, or executes a scanned file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

MAX_FILE_BYTES = 1_000_000
MAX_FILES = 1000
SOURCE_SUFFIXES = {".py", ".js", ".ts", ".sh", ".md"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}


def kind(codepoint: int, index: int, include_pua: bool = False) -> str | None:
    if 0xE0000 <= codepoint <= 0xE007F:
        return "unicode_tag"
    if 0x200B <= codepoint <= 0x200F or 0x202A <= codepoint <= 0x202E:
        return "zero_width_or_bidi"
    if 0x2060 <= codepoint <= 0x2064:
        return "invisible_operator_or_joiner"
    if codepoint == 0xFEFF and index > 0:
        return "embedded_bom"
    if include_pua and (0xE000 <= codepoint <= 0xF8FF or 0xF0000 <= codepoint <= 0x10FFFD):
        return "private_use_review"
    return None


def scan_text(text: str, include_pua: bool = False, show_decoded: bool = False) -> dict:
    counts: Counter[str] = Counter()
    hits = []
    runs = []
    run = []
    run_line = 0
    line = column = 1

    def end_run() -> None:
        nonlocal run
        if run:
            entry = {"line": run_line, "tag_characters": len(run)}
            if show_decoded:
                entry["decoded_ascii"] = "".join(run)[:500]
                entry["truncated"] = len(run) > 500
            runs.append(entry)
            run = []

    for index, char in enumerate(text):
        codepoint = ord(char)
        category = kind(codepoint, index, include_pua)
        if category:
            counts[category] += 1
            if len(hits) < 100:
                hits.append({"line": line, "column": column, "codepoint": f"U+{codepoint:04X}", "kind": category})
        if 0xE0020 <= codepoint <= 0xE007E:
            if not run:
                run_line = line
            run.append(chr(codepoint - 0xE0000))
        else:
            end_run()
        if char == "\n":
            line += 1
            column = 1
        else:
            column += 1
    end_run()
    return {"counts": dict(counts), "hits": hits, "tag_runs": runs}


def scan_file(path: Path, include_pua: bool = False, show_decoded: bool = False) -> dict:
    if path.is_symlink():
        raise ValueError("symbolic links are not scanned")
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        raise ValueError(f"file exceeds {MAX_FILE_BYTES} bytes")
    data = path.read_bytes()
    text = data.decode("utf-8")
    result = scan_text(text, include_pua, show_decoded)
    return {"file": str(path), "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data), **result}


def collect(paths: list[Path]) -> list[Path]:
    found = []
    for path in paths:
        if path.is_file() or path.is_symlink():
            found.append(path)
        elif path.is_dir():
            for item in path.rglob("*"):
                if any(part in SKIP_DIRS for part in item.parts):
                    continue
                if item.is_file() and item.suffix.lower() in SOURCE_SUFFIXES:
                    found.append(item)
                    if len(found) > MAX_FILES:
                        raise ValueError(f"more than {MAX_FILES} files selected")
        else:
            raise ValueError(f"missing path: {path}")
    if len(found) > MAX_FILES:
        raise ValueError(f"more than {MAX_FILES} files selected")
    return sorted(set(found))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--show-decoded", action="store_true", help="include up to 500 decoded ASCII characters per Tag run")
    parser.add_argument("--include-pua", action="store_true", help="also review private-use code points")
    args = parser.parse_args()
    try:
        selected = collect(args.paths)
    except ValueError as exc:
        parser.error(str(exc))
    findings = []
    errors = []
    for path in selected:
        try:
            result = scan_file(path, args.include_pua, args.show_decoded)
            if result["counts"]:
                findings.append(result)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append({"file": str(path), "error": str(exc)})
    print(json.dumps({"files_scanned": len(selected), "findings": findings, "errors": errors}, indent=2, ensure_ascii=True))
    sys.exit(2 if errors else 1 if findings else 0)


if __name__ == "__main__":
    main()
