#!/usr/bin/env python3
"""Read-only ELF64 little-endian baseline/trailer review."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

MAX_SIZE = 16 * 1024 * 1024


def u64_elf_extent(data):
    if len(data) < 64 or data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")
    if data[4:6] != b"\x02\x01":
        raise ValueError("only little-endian ELF64 is supported")
    fields = struct.unpack_from("<HHIQQQIHHHHHH", data, 16)
    phoff, shoff = fields[4], fields[5]
    ehsize, phentsize, phnum, shentsize, shnum = fields[7:12]
    if ehsize < 64 or ehsize > len(data):
        raise ValueError("invalid ELF header size")
    if phnum == 0xffff or (shoff and shnum == 0):
        raise ValueError("extended header counts require a full ELF parser")
    end = ehsize
    if phnum:
        if phentsize < 56 or phoff < ehsize or phoff + phentsize * phnum > len(data):
            raise ValueError("invalid program header table")
        end = max(end, phoff + phentsize * phnum)
        for i in range(phnum):
            ph = struct.unpack_from("<IIQQQQQQ", data, phoff + i * phentsize)
            offset, size = ph[2], ph[5]
            if offset + size > len(data):
                raise ValueError("program segment exceeds file")
            end = max(end, offset + size)
    if shnum:
        if shentsize < 64 or shoff < ehsize or shoff + shentsize * shnum > len(data):
            raise ValueError("invalid section header table")
        end = max(end, shoff + shentsize * shnum)
        for i in range(shnum):
            sh = struct.unpack_from("<IIQQQQIIQQ", data, shoff + i * shentsize)
            section_type, offset, size = sh[1], sh[4], sh[5]
            if section_type != 8 and size:
                if offset + size > len(data):
                    raise ValueError("file-backed section exceeds file")
                end = max(end, offset + size)
    return end


def review(baseline, suspect):
    baseline_end = u64_elf_extent(baseline)
    suspect_end = u64_elf_extent(suspect)
    tail = suspect[suspect_end:]
    return {
        "baseline_bytes": len(baseline),
        "suspect_bytes": len(suspect),
        "baseline_sha256": hashlib.sha256(baseline).hexdigest(),
        "suspect_sha256": hashlib.sha256(suspect).hexdigest(),
        "baseline_structural_end": baseline_end,
        "suspect_structural_end": suspect_end,
        "same_baseline_prefix": suspect.startswith(baseline),
        "appended_to_baseline_bytes": max(0, len(suspect) - len(baseline))
        if suspect.startswith(baseline) else 0,
        "suspect_unmapped_tail_bytes": len(tail),
        "tail_starts_jfif": tail.startswith(b"\xff\xd8\xff\xe0")
        and tail[6:10] == b"JFIF",
        "assessment": "review_unmapped_tail" if tail else "no_unmapped_tail",
    }


def read_bounded(path):
    target = Path(path)
    if target.stat().st_size > MAX_SIZE:
        raise ValueError("file exceeds 16 MiB review limit")
    return target.read_bytes()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("suspect")
    args = parser.parse_args()
    try:
        result = review(read_bounded(args.baseline), read_bounded(args.suspect))
    except (OSError, ValueError, struct.error) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
