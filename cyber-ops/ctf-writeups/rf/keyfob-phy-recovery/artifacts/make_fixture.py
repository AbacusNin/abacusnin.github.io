"""Generate invented multi-emitter IQ for the local reviewer test."""

import argparse
from pathlib import Path

import numpy as np


FS = 200_000
TUNE_HZ = 433_920_000


def create(kind="positive"):
    if kind not in {"positive", "beacon-only", "ask-near-miss"}:
        raise ValueError("Unknown fixture kind")
    rng = np.random.default_rng(77)
    iq = (rng.normal(0, 0.001, 140_000) + 1j * rng.normal(0, 0.001, 140_000)).astype("<c8")

    def event(start_s, offset_hz, widths_us, gaps_us, amplitude=1):
        cursor = round(start_s * FS)
        for i, width in enumerate(widths_us):
            count = round(width * FS / 1e6)
            index = np.arange(count)
            level = amplitude * (0.43 if kind == "ask-near-miss" and offset_hz == 0 and i % 2 else 1)
            iq[cursor:cursor + count] += level * np.exp(2j * np.pi * offset_hz * index / FS)
            cursor += count + round(gaps_us[i % len(gaps_us)] * FS / 1e6)

    event(0.02, 40_000, [250] * 5, [750])
    event(0.39, 40_000, [250] * 5, [750])
    event(0.35, -80_000, [750, 1250] * 7, [750, 1250])
    if kind != "beacon-only":
        pattern = [500, 1000] * 14
        event(0.08, 0, pattern, [500, 1000])
        event(0.55, 0, pattern, [500, 1000])
    return iq


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--kind", choices=("positive", "beacon-only", "ask-near-miss"), default="positive")
    args = parser.parse_args()
    args.output.write_bytes(create(args.kind).tobytes())
    print(f"Wrote invented {args.kind} IQ: {args.output} ({FS} samples/s, tune {TUNE_HZ} Hz)")


if __name__ == "__main__":
    main()
