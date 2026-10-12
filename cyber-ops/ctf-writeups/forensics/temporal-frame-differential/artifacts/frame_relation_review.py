#!/usr/bin/env python3
"""Offline triage of decoded 8-bit luma frames for repeated frame relations."""

import argparse
import json
from pathlib import Path
import numpy as np


def scan(raw_path: Path, width: int, height: int, frames: int, sample: int = 4096,
         max_lag: int = 12, sigma: float = 6.0) -> dict:
    if not (1 <= width <= 1024 and 1 <= height <= 1024 and 3 <= frames <= 3000):
        raise ValueError("geometry exceeds review limits")
    if not (256 <= sample <= width * height and 1 <= max_lag < frames and 1 <= sigma <= 20):
        raise ValueError("invalid scan settings")
    expected = width * height * frames
    if expected > 500_000_000 or raw_path.stat().st_size != expected:
        raise ValueError("raw luma byte count does not match bounded geometry")
    pixels = np.memmap(raw_path, dtype=np.uint8, mode="r", shape=(frames, width * height))
    rng = np.random.default_rng(0)
    selected = rng.choice(width * height, sample, replace=False)
    bits = pixels[:, selected] >= 128
    floor = float(1 / np.sqrt(sample))
    threshold = sigma * floor
    by_lag = []
    for lag in range(1, max_lag + 1):
        hits = []
        for begin in range(0, frames - lag, 128):
            end = min(begin + 128, frames - lag)
            agreement = (bits[begin:end] == bits[begin + lag:end + lag]).mean(axis=1)
            correlation = 2 * agreement - 1
            hits.extend((begin + i, round(float(c), 5)) for i, c in enumerate(correlation)
                        if abs(c) > threshold)
        if hits:
            starts = [i for i, _ in hits]
            spacings = np.diff(starts).tolist()
            period = max(set(spacings), key=spacings.count) if spacings else None
            exact = sum(abs(c) == 1 for _, c in hits)
            by_lag.append({"lag": lag, "hits": len(hits), "exact": exact,
                           "inferred_spacing": period, "first_starts": starts[:10]})
    return {"frames": frames, "sampled_pixels": sample, "null_sd": round(floor, 6),
            "threshold": round(threshold, 6), "by_lag": by_lag,
            "interpretation": "triage only; repeated frames can be legitimate"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path, help="8-bit gray rawvideo in frame order")
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--frames", type=int, required=True)
    parser.add_argument("--sample", type=int, default=4096)
    parser.add_argument("--max-lag", type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(scan(args.raw, args.width, args.height, args.frames,
                          args.sample, args.max_lag), indent=2))


if __name__ == "__main__":
    main()
