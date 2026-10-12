"""Invert a documented one-byte XOR comparison table."""

import argparse
import hashlib
import json
from pathlib import Path


MAX_FILE_BYTES = 32_768
MAX_VALUES = 4_096


def recover(expected, key):
    if type(key) is not int or not 0 <= key <= 255:
        raise ValueError("key must be one byte")
    if not isinstance(expected, list) or not 1 <= len(expected) <= MAX_VALUES:
        raise ValueError("expected must be a nonempty byte list of at most 4096 values")
    if any(type(value) is not int or not 0 <= value <= 255 for value in expected):
        raise ValueError("expected entries must be bytes")
    return bytes(value ^ key for value in expected)


def decode_case(case):
    if not isinstance(case, dict) or set(case) != {"key", "expected", "length"}:
        raise ValueError("JSON needs exactly key, expected, and length")
    result = recover(case["expected"], case["key"])
    if type(case["length"]) is not int or case["length"] != len(result):
        raise ValueError("length gate disagrees with expected table")
    return result


def read_case(path):
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("JSON input exceeds 32 KiB")
    return decode_case(json.loads(path.read_text(encoding="utf-8")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path, help="JSON containing key, expected byte list, and length")
    parser.add_argument("--reveal", action="store_true", help="print recovered text; use only in an authorized private session")
    args = parser.parse_args()
    try:
        result = read_case(args.case)
        report = {
            "length": len(result),
            "printable_ascii": all(32 <= byte < 127 for byte in result),
            "sha256": hashlib.sha256(result).hexdigest(),
        }
        if args.reveal:
            report["recovered_text"] = result.decode("ascii")
        print(json.dumps(report, indent=2))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
