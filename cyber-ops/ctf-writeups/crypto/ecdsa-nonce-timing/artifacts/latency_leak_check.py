#!/usr/bin/env python3
"""Check a controlled signing benchmark for nonce-width-dependent latency.

Input columns: nonce_bits, elapsed_ns. This is a lab screening statistic.
"""

import csv
import io
import json
from math import isfinite, sqrt
from pathlib import Path
import sys


MAX_BYTES = 1_000_000
MAX_ROWS = 10_000


def analyze(path):
    source = Path(path)
    if source.stat().st_size > MAX_BYTES:
        raise ValueError("Input exceeds 1 MB")
    data = source.read_text(encoding="utf-8")
    rows = list(csv.DictReader(io.StringIO(data)))
    if len(rows) > MAX_ROWS:
        raise ValueError("Too many rows")
    if len(rows) < 20:
        raise ValueError("At least 20 controlled measurements are required")
    bits = []
    durations = []
    for row in rows:
        width = int(row["nonce_bits"])
        elapsed = float(row["elapsed_ns"])
        if not 1 <= width <= 256 or not isfinite(elapsed) or elapsed <= 0:
            raise ValueError("Invalid nonce width or duration")
        bits.append(width)
        durations.append(elapsed)
    if len(set(bits)) < 4:
        raise ValueError("At least four nonce widths are required")
    mean_bits = sum(bits) / len(bits)
    mean_duration = sum(durations) / len(durations)
    centered_bits = [x - mean_bits for x in bits]
    centered_duration = [y - mean_duration for y in durations]
    ss_bits = sum(x * x for x in centered_bits)
    ss_duration = sum(y * y for y in centered_duration)
    cross = sum(x * y for x, y in zip(centered_bits, centered_duration))
    slope = cross / ss_bits
    correlation = cross / sqrt(ss_bits * ss_duration) if ss_duration else 0.0
    return {
        "measurements": len(rows),
        "distinct_widths": len(set(bits)),
        "slope_ns_per_bit": round(slope, 2),
        "pearson_r": round(correlation, 4),
        "review_leak": slope > 0 and correlation >= 0.7,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python latency_leak_check.py controlled.csv")
    print(json.dumps(analyze(sys.argv[1]), indent=2))
