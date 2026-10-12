"""Review local text for fixed-width numeric messages that may encode ASCII.

The report is a triage lead. It does not decide intent or expose decoded content.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_BYTES = 1_000_000
MAX_LINES = 1000
MAX_TOKENS = 1000
TOKEN_LINE = re.compile(r"[0-9]{3}(?: [0-9]{3}){9,999}")


def infer_radix(tokens):
    """Return the smallest possible radix for decimal-digit tokens."""
    return max(2, max(int(digit) for token in tokens for digit in token) + 1)


def decode(tokens, radix):
    """Decode positional integer tokens as ASCII, or reject invalid digits."""
    if not 2 <= radix <= 10:
        raise ValueError("radix must be between 2 and 10")
    values = []
    for token in tokens:
        if len(token) != 3 or not token.isascii() or not token.isdecimal():
            raise ValueError("each token must have exactly three ASCII digits")
        value = int(token, radix)
        if value > 127:
            raise ValueError("decoded value is outside ASCII")
        values.append(value)
    return "".join(chr(value) for value in values)


def atbash(text):
    """Reflect ASCII letters across their 26-letter alphabet."""
    chars = []
    for char in text:
        if "a" <= char <= "z":
            chars.append(chr(ord("z") - (ord(char) - ord("a"))))
        elif "A" <= char <= "Z":
            chars.append(chr(ord("Z") - (ord(char) - ord("A"))))
        else:
            chars.append(char)
    return "".join(chars)


def analyze_line(line, number):
    line = line.strip()
    if not TOKEN_LINE.fullmatch(line):
        return None
    tokens = line.split(" ")
    if len(tokens) > MAX_TOKENS:
        raise ValueError(f"line {number}: too many tokens")
    lower_bound = infer_radix(tokens)
    results = []
    for radix in range(max(2, lower_bound), 11):
        try:
            plaintext = decode(tokens, radix)
        except ValueError:
            continue
        printable = all(32 <= ord(char) <= 126 for char in plaintext)
        if not printable:
            continue
        results.append({
            "radix": radix,
            "decoded_sha256": hashlib.sha256(plaintext.encode("ascii")).hexdigest(),
            "letters": sum(char.isalpha() for char in plaintext),
            "spaces": plaintext.count(" "),
        })
    if not results:
        return None
    return {
        "line": number,
        "tokens": len(tokens),
        "digit_set": "".join(sorted(set("".join(tokens)))),
        "minimum_radix": lower_bound,
        "printable_candidates": results,
        "assessment": "review_representation_not_intent",
    }


def audit_text(text):
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        raise ValueError("more than 1,000 lines")
    return [result for number, line in enumerate(lines, 1)
            if (result := analyze_line(line, number)) is not None]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="authorized local UTF-8 content export")
    args = parser.parse_args()
    if args.input.stat().st_size > MAX_BYTES:
        parser.error("input exceeds 1 MB")
    text = args.input.read_text(encoding="utf-8")
    print(json.dumps({"leads": audit_text(text)}, indent=2))


if __name__ == "__main__":
    main()
