"""Rank RGB LSB planes by raw-byte compressibility for manual review."""

import argparse
import json
import math
from pathlib import Path
import zlib

from extract_green_lsb import open_image, plane_values


def entropy(one_fraction):
    if one_fraction in (0, 1):
        return 0.0
    return -one_fraction * math.log2(one_fraction) - (1 - one_fraction) * math.log2(1 - one_fraction)


def analyze(image, bit=0):
    planes = []
    for channel in "RGB":
        values = plane_values(image, channel, bit)
        planes.append({"channel": channel, "bit": bit,
                       "set_fraction": round(sum(values) / len(values), 6),
                       "entropy_bits_per_pixel": round(entropy(sum(values) / len(values)), 6),
                       "zlib_bytes": len(zlib.compress(values, 9))})
    ordered = sorted(planes, key=lambda item: item["zlib_bytes"])
    low, middle = ordered[:2]
    ratio = low["zlib_bytes"] / middle["zlib_bytes"]
    return {"planes": planes, "lowest_channel": low["channel"],
            "lowest_to_next_ratio": round(ratio, 6),
            "review_candidate": low["channel"] if ratio <= 0.25 else None}


def main():
    parser = argparse.ArgumentParser(description="Offline RGB bit-plane triage")
    parser.add_argument("input", type=Path)
    parser.add_argument("--bit", type=int, choices=range(8), default=0)
    args = parser.parse_args()
    image, _ = open_image(args.input)
    try:
        print(json.dumps(analyze(image, args.bit), indent=2))
    finally:
        image.close()


if __name__ == "__main__":
    main()
