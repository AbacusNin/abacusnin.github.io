"""Inspect a slash-token message without assuming that it is Morse."""

import argparse
import json
from pathlib import Path
import re


MORSE = dict(zip(
    (".-", "-...", "-.-.", "-..", ".", "..-.", "--.", "....", "..", ".---",
     "-.-", ".-..", "--", "-.", "---", ".--.", "--.-", ".-.", "...", "-",
     "..-", "...-", ".--", "-..-", "-.--", "--.."),
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
))
MAX_BYTES = 1_000_000
MAX_TOKENS = 100_000


def parse_stream(raw):
    text = raw[:-2] if raw.endswith("\r\n") else raw[:-1] if raw.endswith("\n") else raw
    if not text or not re.fullmatch(r"[\\/]{1,4}(?: [\\/]{1,4})*", text):
        raise ValueError("expected one line of 1-4 mark tokens separated by single spaces")
    tokens = text.split(" ")
    if len(tokens) > MAX_TOKENS:
        raise ValueError("too many tokens")
    return tokens


def morse_read(tokens, dot):
    output = []
    invalid = []
    for index, token in enumerate(tokens, 1):
        code = "".join("." if mark == dot else "-" for mark in token)
        letter = MORSE.get(code)
        if letter is None:
            invalid.append(index)
        output.append(letter or "?")
    return {"text": "".join(output), "invalid_positions": invalid}


def check_candidate(tokens, candidate):
    if not re.fullmatch(r"[a-z]+", candidate):
        raise ValueError("candidate must contain lowercase a-z only, with no spaces")
    if len(candidate) != len(tokens):
        raise ValueError("candidate length must equal token count")
    mapping = {}
    conflicts = []
    for index, (token, letter) in enumerate(zip(tokens, candidate), 1):
        prior = mapping.setdefault(token, letter)
        if prior != letter:
            conflicts.append({"position": index, "token": token, "prior": prior, "candidate": letter})
    return {"consistent": not conflicts, "conflicts": conflicts}


def segments(tokens, lengths):
    if any(length <= 0 for length in lengths) or sum(lengths) != len(tokens):
        raise ValueError("word lengths must be positive and sum to token count")
    result = []
    start = 0
    for length in lengths:
        chunk = tokens[start:start + length]
        outside = set(tokens[:start] + tokens[start + length:])
        result.append({
            "start_position": start + 1,
            "length": length,
            "local_tokens": sorted(set(chunk) - outside),
        })
        start += length
    return result


def analyze(tokens, candidate=None, word_lengths=None):
    ids = {}
    pattern = []
    for token in tokens:
        pattern.append(ids.setdefault(token, len(ids)))
    result = {
        "token_count": len(tokens),
        "distinct_token_count": len(ids),
        "token_lengths": {str(length): sum(len(t) == length for t in tokens) for length in range(1, 5)},
        "token_ids_in_order": ids,
        "pattern": pattern,
        "morse_slash_dot": morse_read(tokens, "/"),
        "morse_backslash_dot": morse_read(tokens, "\\"),
        "scope": "structural checks only; no plaintext uniqueness or threat verdict",
    }
    if candidate is not None:
        result["candidate"] = check_candidate(tokens, candidate)
    if word_lengths is not None:
        result["proposed_segments"] = segments(tokens, word_lengths)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="UTF-8 slash-token file, up to 1 MB")
    parser.add_argument("--candidate", help="lowercase candidate with one letter per token")
    parser.add_argument("--word-lengths", help="analyst-proposed comma-separated word lengths")
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > MAX_BYTES:
            raise ValueError("input exceeds 1 MB")
        tokens = parse_stream(args.input.read_text(encoding="utf-8"))
        lengths = None
        if args.word_lengths is not None:
            if not re.fullmatch(r"[1-9][0-9]*(?:,[1-9][0-9]*)*", args.word_lengths):
                raise ValueError("word lengths must be positive comma-separated integers")
            lengths = [int(value) for value in args.word_lengths.split(",")]
        print(json.dumps(analyze(tokens, args.candidate, lengths), indent=2))
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
