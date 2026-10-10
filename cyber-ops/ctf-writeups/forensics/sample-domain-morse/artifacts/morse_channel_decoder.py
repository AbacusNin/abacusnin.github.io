"""Decode clean sample-domain Morse in a stereo PCM WAV."""

import argparse
from itertools import groupby
from pathlib import Path
import struct
import wave


MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E",
    "..-.": "F", "--.": "G", "....": "H", "..": "I", ".---": "J",
    "-.-": "K", ".-..": "L", "--": "M", "-.": "N", "---": "O",
    ".--.": "P", "--.-": "Q", ".-.": "R", "...": "S", "-": "T",
    "..-": "U", "...-": "V", ".--": "W", "-..-": "X", "-.--": "Y",
    "--..": "Z", "-----": "0", ".----": "1", "..---": "2",
    "...--": "3", "....-": "4", ".....": "5", "-....": "6",
    "--...": "7", "---..": "8", "----.": "9",
}


def read_stereo(path):
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("WAV exceeds the 16 MiB lab limit")
    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 2 or wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
            raise ValueError("Expected uncompressed 16-bit stereo PCM WAV")
        rate = wav.getframerate()
        frames = wav.getnframes()
        raw = wav.readframes(frames)
    if len(raw) != frames * 4:
        raise ValueError("Truncated WAV data")
    samples = list(struct.iter_unpack("<hh", raw))
    return rate, samples


def decode(samples, start, end, payload, reference, threshold, ref_threshold):
    candidates = [i for i in range(start, end)
                  if abs(samples[i][payload]) > threshold
                  and abs(samples[i][reference]) <= ref_threshold]
    if not candidates:
        raise ValueError("No one-channel loud burst in the selected region")
    lo, hi = candidates[0], candidates[-1]
    if any(abs(samples[i][reference]) > ref_threshold for i in range(lo, hi + 1)):
        raise ValueError("Reference channel is loud within the candidate burst")
    bits = [abs(samples[i][payload]) > threshold for i in range(lo, hi + 1)]
    runs = [(int(value), len(list(group))) for value, group in groupby(bits)]
    words, letters, token = [], [], ""

    def finish_letter():
        nonlocal token
        if token not in MORSE:
            raise ValueError(f"Unmapped Morse token: {token!r}")
        letters.append(MORSE[token])
        token = ""

    for value, length in runs:
        if value:
            if length not in (1, 3):
                raise ValueError(f"Unexpected loud run: {length} samples")
            token += "." if length == 1 else "-"
        elif length == 1:
            continue
        elif length in (3, 5):
            finish_letter()
            if length == 5:
                words.append("".join(letters))
                letters.clear()
        else:
            raise ValueError(f"Unexpected quiet run: {length} samples")
    finish_letter()
    words.append("".join(letters))
    message = " ".join(words)
    if sum(map(len, words)) < 3:
        raise ValueError("Fewer than three decoded characters; likely a transient")
    return lo, hi, runs, message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--payload", type=int, choices=(0, 1), default=0)
    parser.add_argument("--reference", type=int, choices=(0, 1), default=1)
    parser.add_argument("--threshold", type=int, default=4000)
    parser.add_argument("--reference-threshold", type=int, default=4000)
    parser.add_argument("--start", type=float, default=0, help="Start time in seconds")
    parser.add_argument("--end", type=float, help="End time in seconds")
    args = parser.parse_args()
    if args.payload == args.reference:
        parser.error("Payload and reference must be different channels")
    if args.threshold < 0 or args.reference_threshold < 0:
        parser.error("Thresholds must be nonnegative")
    try:
        rate, samples = read_stereo(args.wav)
        start = max(0, int(args.start * rate))
        end = len(samples) if args.end is None else min(len(samples), int(args.end * rate))
        if start >= end:
            raise ValueError("Selected time window is empty")
        lo, hi, runs, message = decode(samples, start, end, args.payload, args.reference,
                                       args.threshold, args.reference_threshold)
    except (ValueError, wave.Error) as exc:
        parser.exit(2, f"Rejected: {exc}\n")
    print(f"Burst: {lo}-{hi} samples ({lo / rate:.6f}-{hi / rate:.6f} s)")
    print("Runs: " + " ".join(f"{'mark' if value else 'gap'}:{length}" for value, length in runs))
    print("Text: " + message)


if __name__ == "__main__":
    main()
