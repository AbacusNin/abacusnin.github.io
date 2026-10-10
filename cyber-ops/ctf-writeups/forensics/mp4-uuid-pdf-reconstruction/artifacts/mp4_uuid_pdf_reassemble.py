"""Inspect top-level MP4 uuid boxes and validate a guided PDF reconstruction."""

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import struct
import zlib


MAX_FILE = 2 * 1024 * 1024
MAX_PDF = 8 * 1024 * 1024
MAX_INFLATED = 1024 * 1024


def read_small(path, limit=MAX_FILE):
    if path.stat().st_size > limit:
        raise ValueError(f"File exceeds {limit} bytes: {path.name}")
    return path.read_bytes()


def boxes(data):
    offset = 0
    while offset < len(data):
        if len(data) - offset < 8:
            raise ValueError("Truncated MP4 box header")
        size, kind = struct.unpack_from(">I4s", data, offset)
        header = 8
        if size == 1:
            if len(data) - offset < 16:
                raise ValueError("Truncated extended-size box")
            size = struct.unpack_from(">Q", data, offset + 8)[0]
            header = 16
        elif size == 0:
            size = len(data) - offset
        if size < header or offset + size > len(data):
            raise ValueError("MP4 box extends beyond its file")
        if kind == b"uuid" and size < header + 16:
            raise ValueError("uuid box lacks its 16-byte user identifier")
        yield kind, offset, size, header
        offset += size


def inspect(path):
    data = read_small(path)
    parsed = list(boxes(data))
    if not parsed or parsed[0][0] != b"ftyp":
        raise ValueError(f"No initial ftyp box: {path.name}")
    payloads = [data[offset + header + 16:offset + size]
                for kind, offset, size, header in parsed if kind == b"uuid"]
    return [kind.decode("ascii", errors="replace") for kind, *_ in parsed], payloads


def carrier(root, name):
    if not isinstance(name, str) or not name or Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError(f"Manifest entry must be a filename: {name!r}")
    path = (root / name).resolve()
    if path.parent != root.resolve() or path.suffix.lower() != ".mp4":
        raise ValueError(f"Carrier leaves the selected directory: {name!r}")
    kinds, payloads = inspect(path)
    if len(payloads) != 1 or kinds[-1] != "uuid":
        raise ValueError(f"Expected one trailing uuid box: {name}")
    return payloads[0]


def validate_pdf(pdf):
    if len(pdf) > MAX_PDF or not pdf.startswith(b"%PDF-"):
        raise ValueError("Missing PDF header or PDF exceeds lab size limit")
    marker = b"\nstream\n"
    if pdf.count(marker) != 1:
        raise ValueError("Expected one LF-delimited content stream")
    start = pdf.index(marker) + len(marker)
    lengths = re.findall(rb"/Length\s+(\d+)\b", pdf[:start])
    if len(lengths) != 1:
        raise ValueError("Expected one direct stream /Length")
    encoded_length = int(lengths[0])
    if encoded_length > MAX_FILE or pdf[start + encoded_length:start + encoded_length + 10] != b"\nendstream":
        raise ValueError("/Length does not match stored stream bytes")
    encoded = pdf[start:start + encoded_length]
    inflater = zlib.decompressobj()
    content = inflater.decompress(encoded, MAX_INFLATED + 1)
    if len(content) > MAX_INFLATED or not inflater.eof or inflater.unused_data:
        raise ValueError("Stream is truncated, oversized, or has trailing compressed data")

    match = re.search(rb"startxref\s+(\d+)\s+%%EOF\s*$", pdf)
    if not match:
        raise ValueError("Missing startxref or EOF marker")
    xref = int(match[1])
    if xref >= len(pdf) or not pdf[xref:].startswith(b"xref\n"):
        raise ValueError("startxref points away from the xref table")
    lines = pdf[xref:].split(b"\n")
    section = re.fullmatch(rb"0\s+(\d+)", lines[1]) if len(lines) > 1 else None
    if not section or not (2 <= int(section[1]) <= 1000):
        raise ValueError("Expected one classic xref section starting at object zero")
    count = int(section[1])
    if len(lines) < count + 2:
        raise ValueError("Truncated xref entries")
    for object_no in range(1, count):
        entry = re.fullmatch(rb"(\d{10})\s+(\d{5})\s+n\s*", lines[object_no + 2])
        if not entry or pdf[int(entry[1]):].startswith(f"{object_no} 0 obj".encode()) is False:
            raise ValueError(f"xref entry {object_no} does not point to its object")
    return len(content), count - 1


def scan(root):
    files = sorted(path for path in root.iterdir() if path.is_file() and path.suffix.lower() == ".mp4")
    if not files or len(files) > 64:
        raise ValueError("Expected 1-64 MP4 files")
    header_hits = 0
    for path in files:
        kinds, payloads = inspect(path)
        hits = sum(b"%PDF-" in payload for payload in payloads)
        header_hits += hits
        print(f"{path.name}: boxes={','.join(kinds)} uuid={len(payloads)} pdf_headers={hits}")
    print(f"Scanned {len(files)} files; PDF-header-bearing uuid payloads: {header_hits}")


def reassemble(manifest_path, output):
    manifest = json.loads(read_small(manifest_path, 16384))
    root = manifest_path.resolve().parent
    names = [manifest.get(part) for part in ("prefix", "body", "suffix")]
    if any(not isinstance(group, list) or not group for group in names):
        raise ValueError("Manifest needs nonempty prefix, body, and suffix lists")
    prefix_names, body_names, suffix_names = names
    all_names = prefix_names + body_names + suffix_names
    if len(all_names) > 32 or len(set(all_names)) != len(all_names) or len(body_names) > 7:
        raise ValueError("Duplicate carriers, over 32 carriers, or over 7 body fragments")
    payload = {name: carrier(root, name) for name in all_names}
    if sum(map(len, payload.values())) > MAX_PDF:
        raise ValueError("Combined fragments exceed the 8 MiB lab limit")
    prefix = b"".join(payload[name] for name in prefix_names)
    suffix = b"".join(payload[name] for name in suffix_names)
    solutions = []
    for order in itertools.permutations(body_names):
        pdf = prefix + b"".join(payload[name] for name in order) + suffix
        try:
            inflated, objects = validate_pdf(pdf)
        except (ValueError, zlib.error):
            continue
        solutions.append((order, pdf, inflated, objects))
        if len(solutions) > 1:
            break
    if len(solutions) != 1:
        raise ValueError(f"Expected one valid stream order; found {len(solutions)}")
    order, pdf, inflated, objects = solutions[0]
    output.write_bytes(pdf)
    print("Body order:", ", ".join(order))
    print(f"Validated PDF: {len(pdf)} bytes, {objects} objects, {inflated} inflated content bytes")
    print("SHA-256:", hashlib.sha256(pdf).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    scan_parser = sub.add_parser("scan", help="List top-level boxes and uuid payload hints")
    scan_parser.add_argument("directory", type=Path)
    rebuild_parser = sub.add_parser("reassemble", help="Test body orders from an analyst-supplied manifest")
    rebuild_parser.add_argument("manifest", type=Path)
    rebuild_parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.action == "scan":
            scan(args.directory)
        else:
            reassemble(args.manifest, args.output)
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, zlib.error) as exc:
        parser.exit(2, f"Rejected: {exc}\n")


if __name__ == "__main__":
    main()
