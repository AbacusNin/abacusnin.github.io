"""Inspect PNG chunk boundaries and carve intact PNG streams after IEND."""

import argparse
import hashlib
import json
import re
import zlib
from pathlib import Path


PNG_SIG = b"\x89PNG\r\n\x1a\n"
IHDR_HEAD = b"\x00\x00\x00\rIHDR"
MAX_BYTES = 16_000_000
MAX_CHUNKS = 10_000
MAX_CANDIDATES = 64


class PngError(ValueError):
    pass


def parse_png(data, start=0, signed=True):
    if signed:
        if data[start:start + 8] != PNG_SIG:
            raise PngError("missing PNG signature")
        pos = start + 8
    else:
        pos = start
    first = True
    seen_idat = False
    width = height = None
    for _ in range(MAX_CHUNKS):
        if pos + 12 > len(data):
            raise PngError("truncated chunk header")
        size = int.from_bytes(data[pos:pos + 4], "big")
        kind = data[pos + 4:pos + 8]
        end = pos + 12 + size
        if end > len(data):
            raise PngError("chunk extends past file")
        if not re.fullmatch(rb"[A-Za-z]{4}", kind):
            raise PngError("invalid chunk type")
        stored_crc = int.from_bytes(data[end - 4:end], "big")
        actual_crc = zlib.crc32(data[pos + 4:end - 4])
        if stored_crc != actual_crc:
            raise PngError("chunk CRC mismatch")
        if first:
            if kind != b"IHDR" or size != 13:
                raise PngError("first chunk is not IHDR")
            width = int.from_bytes(data[pos + 8:pos + 12], "big")
            height = int.from_bytes(data[pos + 12:pos + 16], "big")
            if not width or not height:
                raise PngError("zero image dimension")
            first = False
        elif kind == b"IHDR":
            raise PngError("second IHDR in one PNG stream")
        if kind == b"IDAT":
            seen_idat = True
        if kind == b"IEND":
            if size != 0 or not seen_idat:
                raise PngError("invalid IEND position or length")
            return {"start": start, "end": end, "width": width, "height": height}
        pos = end
    raise PngError("chunk count exceeds limit")


def printable_runs(data, base):
    runs = []
    for match in re.finditer(rb"[\x20-\x7e]{6,}", data):
        runs.append({"offset": base + match.start(), "length": len(match.group()),
                     "preview": match.group()[:80].decode("ascii")})
        if len(runs) == 8:
            break
    return runs


def inspect(data):
    if len(data) > MAX_BYTES:
        raise PngError(f"input exceeds {MAX_BYTES} bytes")
    carrier = parse_png(data)
    trailer = data[carrier["end"]:]
    starts = []
    for pattern, signed in ((PNG_SIG, True), (IHDR_HEAD, False)):
        pos = data.find(pattern, carrier["end"])
        while pos >= 0:
            starts.append((pos, signed))
            if len(starts) > MAX_CANDIDATES:
                raise PngError("too many PNG candidates after IEND")
            pos = data.find(pattern, pos + 1)
    carves = []
    covered = 0
    for start, signed in sorted(starts):
        if start < covered:
            continue
        try:
            parsed = parse_png(data, start, signed)
        except PngError:
            continue
        payload = (b"" if signed else PNG_SIG) + data[start:parsed["end"]]
        carves.append({"offset": start, "length": len(payload),
                       "signature_repaired": not signed,
                       "width": parsed["width"], "height": parsed["height"],
                       "sha256": hashlib.sha256(payload).hexdigest(), "bytes": payload})
        covered = parsed["end"]
    return {"carrier_end": carrier["end"], "trailing_bytes": len(trailer),
            "printable_runs": printable_runs(trailer, carrier["end"]), "carves": carves}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--out", type=Path, help="directory for carved PNGs")
    args = parser.parse_args()
    with args.file.open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    result = inspect(data)
    if args.out and result["carves"]:
        args.out.mkdir(parents=True, exist_ok=True)
    for number, carve in enumerate(result["carves"], 1):
        payload = carve.pop("bytes")
        if args.out:
            destination = args.out / f"recovered_{number}.png"
            with destination.open("xb") as handle:
                handle.write(payload)
            carve["saved_as"] = str(destination)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
