"""Create neutral ISO-BMFF test containers carrying one split PDF."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib


USER_ID = bytes.fromhex("0123456789abcdeffedcba9876543210")
NAMES = [12, 4, 9, 2, 15, 6, 1, 11, 7, 14, 3, 10, 5, 13, 8]


def box(kind, payload):
    return struct.pack(">I4s", len(payload) + 8, kind) + payload


def pdf_file():
    content = b"BT /F1 14 Tf 72 720 Td (Neutral container demo) Tj ET\n"
    encoded = zlib.compress(content)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(encoded)).encode() + b" /Filter /FlateDecode >>\nstream\n" + encoded + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += str(number).encode() + b" 0 obj\n" + body + b"\nendobj\n"
    xref = len(pdf)
    pdf += b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF\n"
    return pdf


def pieces(data, count):
    if len(data) < count:
        raise ValueError("Too few bytes to split")
    return [data[i * len(data) // count:(i + 1) * len(data) // count] for i in range(count)]


def write_carrier(path, fragment, mode="normal"):
    data = box(b"ftyp", b"isom\x00\x00\x02\x00isom")
    data += box(b"mdat", b"\x00" * 8)
    if mode == "extended":
        data += struct.pack(">I4sQ", 1, b"uuid", 32 + len(fragment)) + USER_ID + fragment
    elif mode == "to-end":
        data += struct.pack(">I4s", 0, b"uuid") + USER_ID + fragment
    else:
        data += box(b"uuid", USER_ID + fragment)
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="New or empty output directory")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if directory.exists() and any(directory.iterdir()):
        parser.error("Output directory must be empty")
    directory.mkdir(parents=True, exist_ok=True)
    pdf = pdf_file()
    start = pdf.index(b"stream\n") + len(b"stream\n")
    end = pdf.index(b"\nendstream", start)
    fragments = pieces(pdf[:start], 6) + pieces(pdf[start:end], 3) + pieces(pdf[end:], 6)
    names = [f"carrier_{number:02d}.mp4" for number in NAMES]
    for position, (name, fragment) in enumerate(zip(names, fragments)):
        write_carrier(directory / name, fragment, "extended" if position == 0 else "normal")
    write_carrier(directory / "benign_metadata.mp4", b"neutral vendor metadata", "to-end")
    manifest = {"prefix": names[:6], "body": list(reversed(names[6:9])), "suffix": names[9:]}
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    bad = {"prefix": names[:6].copy(), "body": list(reversed(names[6:9])), "suffix": names[9:]}
    bad["prefix"][0], bad["prefix"][1] = bad["prefix"][1], bad["prefix"][0]
    (directory / "wrong_order.json").write_text(json.dumps(bad, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Synthetic PDF SHA-256:", hashlib.sha256(pdf).hexdigest())
    print("Created 15 non-playable test carriers and one benign metadata carrier")


if __name__ == "__main__":
    main()
