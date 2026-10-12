"""Bounded exact-hash triage for repeated asset files or fixed-size byte streams."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class ScanError(Exception):
    pass


def _record(data, location, counts, locations, max_distinct):
    digest = hashlib.sha256(data).hexdigest()
    if digest not in counts and len(counts) >= max_distinct:
        raise ScanError("distinct-hash limit reached")
    counts[digest] += 1
    if len(locations[digest]) < 5:
        locations[digest].append(location)


def _report(mode, files, total_bytes, counts, locations, min_repeat):
    histogram = Counter(counts.values())
    rare = [
        {"sha256": digest, "count": count, "locations": locations[digest]}
        for digest, count in counts.items() if count < min_repeat
    ]
    rare.sort(key=lambda item: (item["count"], item["sha256"]))
    return {
        "mode": mode, "files": files, "bytes": total_bytes,
        "distinct_hashes": len(counts), "minimum_repeat": min_repeat,
        "frequency_histogram": {str(k): v for k, v in sorted(histogram.items())},
        "rare_candidates": rare,
        "assessment": "review_candidates" if rare else "no_rare_candidates",
    }


def scan_directory(root, *, max_files, max_bytes, max_file_bytes,
                   max_distinct, min_repeat, suffix):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ScanError("root must be a real directory")
    counts, locations = Counter(), {}
    files = total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ScanError(f"symlink in scan: {path}")
        if not path.is_file() or (suffix and path.suffix.lower() != suffix.lower()):
            continue
        files += 1
        if files > max_files:
            raise ScanError("file-count limit reached")
        size = path.stat().st_size
        if size <= 0 or size > max_file_bytes or total + size > max_bytes:
            raise ScanError(f"file size or total-byte limit reached: {path}")
        data = path.read_bytes()
        if len(data) != size or not data.startswith(PNG_MAGIC):
            raise ScanError(f"changed file or missing PNG signature: {path}")
        total += size
        digest = hashlib.sha256(data).hexdigest()
        locations.setdefault(digest, [])
        _record(data, str(path.relative_to(root)).replace("\\", "/"),
                counts, locations, max_distinct)
    if not files:
        raise ScanError("no matching files")
    return _report("directory", files, total, counts, locations, min_repeat)


def _read_exact(stream, size):
    parts, remaining = [], size
    while remaining:
        part = stream.read(remaining)
        if not part:
            break
        parts.append(part)
        remaining -= len(part)
    return b"".join(parts)


def scan_stream(stream, *, file_size, expected_count, max_bytes,
                max_distinct, min_repeat):
    if file_size < len(PNG_MAGIC) or expected_count < 1:
        raise ScanError("positive file size and count are required")
    if file_size * expected_count > max_bytes:
        raise ScanError("expected output exceeds byte limit")
    counts, locations = Counter(), {}
    for ordinal in range(expected_count):
        data = _read_exact(stream, file_size)
        if len(data) != file_size:
            raise ScanError(f"short output at record {ordinal}")
        if not data.startswith(PNG_MAGIC):
            raise ScanError(f"missing PNG signature at record {ordinal}")
        digest = hashlib.sha256(data).hexdigest()
        locations.setdefault(digest, [])
        _record(data, ordinal, counts, locations, max_distinct)
    if stream.read(1):
        raise ScanError("extra output after expected records")
    return _report("fixed_size_stream", expected_count,
                   file_size * expected_count, counts, locations, min_repeat)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("directory", "stream"))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--file-size", type=int)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--max-files", type=int, default=1100000)
    parser.add_argument("--max-bytes", type=int, default=16 * 1024**3)
    parser.add_argument("--max-file-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--max-distinct", type=int, default=200000)
    parser.add_argument("--min-repeat", type=int, default=3)
    parser.add_argument("--suffix", default=".png")
    args = parser.parse_args(argv)
    if args.min_repeat < 2 or min(args.max_bytes, args.max_distinct) < 1:
        parser.error("limits must be positive and min-repeat must be at least 2")
    try:
        if args.mode == "directory":
            if args.root is None:
                parser.error("directory mode requires --root")
            result = scan_directory(
                args.root, max_files=args.max_files, max_bytes=args.max_bytes,
                max_file_bytes=args.max_file_bytes,
                max_distinct=args.max_distinct, min_repeat=args.min_repeat,
                suffix=args.suffix)
        else:
            if args.file_size is None or args.expected_count is None:
                parser.error("stream mode requires --file-size and --expected-count")
            result = scan_stream(
                sys.stdin.buffer, file_size=args.file_size,
                expected_count=args.expected_count, max_bytes=args.max_bytes,
                max_distinct=args.max_distinct, min_repeat=args.min_repeat)
    except (OSError, ScanError) as exc:
        parser.exit(2, f"scan failed: {exc}\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
