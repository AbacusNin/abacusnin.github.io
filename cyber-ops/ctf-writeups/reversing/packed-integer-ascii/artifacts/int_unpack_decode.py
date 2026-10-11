#!/usr/bin/env python3
"""Decode fixed-width integers as ASCII bytes without executing input files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

MAX_INPUT_BYTES = 1_000_000
MAX_VALUES = 4096
DECIMAL = re.compile(r"[0-9]+")


def parse_values(text: str) -> list[int]:
    tokens = DECIMAL.findall(text)
    if not tokens or len(tokens) > MAX_VALUES:
        raise ValueError(f"expected 1-{MAX_VALUES} decimal integers")
    residue = DECIMAL.sub("", text)
    if any(char not in " \t\r\n,[]()" for char in residue):
        raise ValueError("input may contain decimal integers, separators, and brackets only")
    return [int(token) for token in tokens]


def unpack(values: list[int], width: int = 8, order: str = "big", strip_null: bool = True) -> bytes:
    if not 1 <= width <= 16:
        raise ValueError("width must be between 1 and 16 bytes")
    if order not in {"big", "little"}:
        raise ValueError("order must be big or little")
    if not values or len(values) > MAX_VALUES:
        raise ValueError(f"expected 1-{MAX_VALUES} values")
    maximum = 1 << (8 * width)
    if any(not isinstance(value, int) or value < 0 or value >= maximum for value in values):
        raise ValueError("an integer is outside the selected unsigned block width")
    raw = b"".join(value.to_bytes(width, order) for value in values)
    return raw.split(b"\x00", 1)[0] if strip_null else raw


def inspect(values: list[int], width: int = 8, strip_null: bool = True) -> list[dict]:
    views = []
    for order in ("big", "little"):
        raw = unpack(values, width, order, strip_null)
        try:
            text = raw.decode("ascii")
            ascii_ok = True
        except UnicodeDecodeError:
            text = None
            ascii_ok = False
        views.append({"byte_order": order, "ascii": text, "ascii_valid": ascii_ok, "hex": raw.hex()})
    return views


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("values", nargs="*", help="decimal integers")
    parser.add_argument("--file", type=Path, help="text file of decimal integers")
    parser.add_argument("--width", type=int, default=8, help="bytes per integer, default 8")
    parser.add_argument("--byteorder", choices=("big", "little"), default="big")
    parser.add_argument("--auto", action="store_true", help="show both byte orders for human comparison")
    parser.add_argument("--keep-null", action="store_true", help="keep bytes after the first null")
    args = parser.parse_args()
    if args.file and args.values:
        parser.error("use --file or positional integers")
    if args.file:
        if args.file.stat().st_size > MAX_INPUT_BYTES:
            parser.error(f"input exceeds {MAX_INPUT_BYTES} bytes")
        source = args.file.read_text(encoding="utf-8")
    else:
        source = " ".join(args.values)
    try:
        values = parse_values(source)
        views = inspect(values, args.width, not args.keep_null)
    except ValueError as exc:
        parser.error(str(exc))
    selected = views if args.auto else [next(view for view in views if view["byte_order"] == args.byteorder)]
    print(json.dumps(selected, indent=2))


if __name__ == "__main__":
    main()
