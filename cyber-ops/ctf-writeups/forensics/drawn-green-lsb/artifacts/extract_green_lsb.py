"""Inspect a PNG and render one channel's selected bit plane offline."""

import argparse
import json
from pathlib import Path
import zlib

from PIL import Image


SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_FILE = 25 * 1024 * 1024
MAX_PIXELS = 20_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def png_chunks(data):
    if not SIGNATURE == data[:8] or not 8 <= len(data) <= MAX_FILE:
        raise ValueError("input must be a bounded PNG")
    offset = 8
    chunks = []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        size = int.from_bytes(data[offset:offset + 4], "big")
        end = offset + 12 + size
        if end > len(data):
            raise ValueError("PNG chunk exceeds file")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + size]
        expected = int.from_bytes(data[offset + 8 + size:end], "big")
        actual = zlib.crc32(kind + payload) & 0xFFFFFFFF
        if actual != expected:
            raise ValueError("PNG chunk CRC mismatch")
        try:
            name = kind.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError("invalid PNG chunk type") from exc
        chunks.append({"type": name, "length": size, "offset": offset})
        offset = end
        if name == "IEND":
            if size != 0 or offset != len(data):
                raise ValueError("data follows PNG IEND")
            break
    if not chunks or chunks[0]["type"] != "IHDR" or chunks[-1]["type"] != "IEND":
        raise ValueError("missing IHDR or IEND")
    return chunks


def open_image(path):
    if path.stat().st_size > MAX_FILE:
        raise ValueError("PNG exceeds 25 MiB")
    chunks = png_chunks(path.read_bytes())
    image = Image.open(path)
    if image.mode not in ("RGB", "RGBA") or image.width * image.height > MAX_PIXELS:
        image.close()
        raise ValueError("only bounded 8-bit RGB/RGBA PNGs are supported")
    image.load()
    return image, chunks


def plane_values(image, channel, bit):
    if channel not in image.getbands() or not 0 <= bit <= 7:
        raise ValueError("channel or bit is unavailable")
    return image.getchannel(channel).point(lambda value: (value >> bit) & 1).tobytes()


def render(image, channel="G", bit=0):
    values = plane_values(image, channel, bit)
    visible = bytes(255 if value else 0 for value in values)
    return Image.frombytes("L", image.size, visible), sum(values)


def main():
    parser = argparse.ArgumentParser(description="Inspect and render one PNG bit plane")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--channel", choices=["r", "g", "b", "a"], default="g")
    parser.add_argument("--bit", type=int, choices=range(8), default=0)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a new path")
    image, chunks = open_image(args.input)
    try:
        output, count = render(image, args.channel.upper(), args.bit)
        with args.output.open("xb") as stream:
            output.save(stream, format="PNG")
        output.close()
        print(json.dumps({"size": list(image.size), "mode": image.mode,
                          "chunks": [item["type"] for item in chunks],
                          "trailing_bytes": 0, "channel": args.channel.upper(),
                          "bit": args.bit, "set_pixels": count, "output": str(args.output)}))
    finally:
        image.close()


if __name__ == "__main__":
    main()
