"""Make deterministic invented PNG carriers for the offline LSB lab."""

import argparse
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 600, 160
NAMES = ("fixture_green_lsb.png", "benign_random.png",
         "benign_stripes.png", "near_miss_random_payload.png")


def make(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        if (output_dir / name).exists():
            raise FileExistsError(f"{name} already exists; use a fresh directory")
    rng = random.Random(20261011)
    mask = Image.new("1", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    draw.text((12, 52), "GREEN_LSB_DEMO", fill=1, font=ImageFont.load_default(size=32))
    glyphs = mask.convert("L").tobytes()
    for name in NAMES:
        data = bytearray(WIDTH * HEIGHT * 4)
        for index in range(WIDTH * HEIGHT):
            x, y = index % WIDTH, index // WIDTH
            r = ((x // 3 + rng.randrange(32)) & 0xFE) | rng.randrange(2)
            g = ((y + rng.randrange(32)) & 0xFE) | rng.randrange(2)
            b = (((x + y) // 4 + rng.randrange(32)) & 0xFE) | rng.randrange(2)
            if name == "fixture_green_lsb.png":
                g = (g & 0xFE) | (1 if glyphs[index] else 0)
            elif name == "benign_stripes.png":
                g = (g & 0xFE) | ((x // 24) & 1)
            elif name == "near_miss_random_payload.png":
                g = (g & 0xFE) | rng.randrange(2)
            data[4 * index:4 * index + 4] = bytes((r, g, b, 255))
        Image.frombytes("RGBA", (WIDTH, HEIGHT), bytes(data)).save(output_dir / name)
    return [output_dir / name for name in NAMES]


def main():
    parser = argparse.ArgumentParser(description="Create four synthetic LSB triage cases")
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    for path in make(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
