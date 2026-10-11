#!/usr/bin/env python3
"""Find literal integer arrays that decode to mostly printable ASCII in Python source.

Uses Python's AST parser. It never imports or executes the file being inspected.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

MAX_SOURCE_BYTES = 2_000_000
MAX_ARRAY_VALUES = 4096
MIN_ARRAY_VALUES = 3


def literal_ints(node: ast.AST) -> list[int] | None:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    if not MIN_ARRAY_VALUES <= len(node.elts) <= MAX_ARRAY_VALUES:
        return None
    values = []
    for element in node.elts:
        if not isinstance(element, ast.Constant) or type(element.value) is not int:
            return None
        value = element.value
        if value < 0 or value >= (1 << 64):
            return None
        values.append(value)
    return values


def candidate_view(values: list[int], order: str) -> dict | None:
    raw = b"".join(value.to_bytes(8, order) for value in values)
    before_null = raw.split(b"\x00", 1)[0]
    if len(before_null) < 16:
        return None
    printable = sum(32 <= byte <= 126 or byte in (9, 10, 13) for byte in before_null)
    ratio = printable / len(before_null)
    if ratio < 0.95 or not any(65 <= byte <= 90 or 97 <= byte <= 122 for byte in before_null):
        return None
    return {"byte_order": order, "printable_ratio": round(ratio, 3), "null_terminated": b"\x00" in raw}


def scan_source(source: str) -> list[dict]:
    tree = ast.parse(source)
    findings = []
    for node in ast.walk(tree):
        values = literal_ints(node)
        if values is None:
            continue
        views = [view for order in ("big", "little") if (view := candidate_view(values, order))]
        if views:
            findings.append({"line": node.lineno, "integer_count": len(values), "views": views,
                             "status": "candidate_for_analyst_review"})
    return sorted(findings, key=lambda finding: finding["line"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Python source file to inspect without execution")
    args = parser.parse_args()
    if args.source.stat().st_size > MAX_SOURCE_BYTES:
        parser.error(f"source exceeds {MAX_SOURCE_BYTES} bytes")
    try:
        source = args.source.read_text(encoding="utf-8")
        findings = scan_source(source)
    except (UnicodeError, SyntaxError) as exc:
        parser.error(f"cannot parse source: {exc}")
    print(json.dumps({"file": args.source.name, "findings": findings}, indent=2))


if __name__ == "__main__":
    main()
