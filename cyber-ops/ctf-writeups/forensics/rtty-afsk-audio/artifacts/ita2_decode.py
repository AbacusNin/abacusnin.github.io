#!/usr/bin/env python3
"""Decode already recovered RTTY symbol bits with and without shift tracking."""

import argparse
from pathlib import Path


LETTERS = (None, "E", "\n", "A", " ", "S", "I", "U", "\r", "D", "R", "J", "N", "F", "C", "K",
           "T", "Z", "L", "W", "H", "Y", "P", "Q", "O", "B", "G", None, "M", "X", "V", None)
FIGURES = (None, "3", "\n", "-", " ", "'", "8", "7", "\r", "+", "4", None, ",", None, ":", "(",
           "5", '"', ")", "2", "#", "6", "0", "1", "9", "?", "&", None, ".", "/", None, None)


def decode(bits, mode="track"):
    if mode not in {"track", "letters", "figures"} or any(bit not in (0, 1) for bit in bits):
        raise ValueError("mode or bitstream invalid")
    output = []
    shifts = []
    state = "L"
    frames = 0
    i = 0
    while i + 6 < len(bits):
        if bits[i] != 0:
            i += 1
            continue
        if bits[i + 6] != 1:
            i += 1
            continue
        value = sum(bits[i + 1 + j] << j for j in range(5))
        frames += 1
        if value in (27, 31):
            state = "F" if value == 27 else "L"
            shifts.append((frames, state))
        else:
            table = LETTERS if (mode == "letters" or (mode == "track" and state == "L")) else FIGURES
            character = table[value]
            if character and character != "\r":
                output.append(character)
        i += 7
        while i < len(bits) and bits[i] == 1:
            i += 1
    return {"text": "".join(output), "frames": frames, "shifts": shifts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bits", type=Path, help="UTF-8 text containing 0/1 symbol bits")
    args = parser.parse_args()
    try:
        raw = args.bits.read_text(encoding="utf-8")
        if len(raw) > 1_000_000:
            parser.error("bitstream exceeds 1 million characters")
        stripped = "".join(raw.split())
        if set(stripped) - {"0", "1"}:
            parser.error("bitstream must contain only 0 and 1")
        bits = [int(bit) for bit in stripped]
        for mode in ("track", "letters"):
            result = decode(bits, mode)
            print(f"{mode}: {result['text']!r}; frames={result['frames']}; shifts={result['shifts']}")
    except OSError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
