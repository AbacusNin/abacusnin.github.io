"""Bounded offline inventory of embedded ELF/BPF objects in a Linux ELF.

Reports structure and review leads. Does not execute the host or BPF object,
attach a tracepoint, decode rodata, or emit a recovered secret.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import struct

MAX_FILE = 32 * 1024 * 1024
MAX_CANDIDATES = 128
MAX_SECTIONS = 128
ELF_MAGIC = b"\x7fELF"


def inspect_elf(blob, base=0):
    data = memoryview(blob)[base:]
    if len(data) < 64 or bytes(data[:6]) != b"\x7fELF\x02\x01":
        return None
    machine = struct.unpack_from("<H", data, 18)[0]
    shoff = struct.unpack_from("<Q", data, 40)[0]
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 58)
    if shentsize != 64 or not 1 <= shnum <= MAX_SECTIONS or shstrndx >= shnum:
        return None
    if shoff < 64 or shoff + shnum * shentsize > len(data):
        return None
    headers = [struct.unpack_from("<IIQQQQIIQQ", data, shoff + i * shentsize)
               for i in range(shnum)]
    string_hdr = headers[shstrndx]
    if string_hdr[1] != 3 or string_hdr[4] + string_hdr[5] > len(data):
        return None
    names = bytes(data[string_hdr[4]:string_hdr[4] + string_hdr[5]])
    sections = {}
    end = shoff + shnum * shentsize
    for header in headers:
        name_off, section_type, _, _, offset, size, _, _, _, _ = header
        if name_off >= len(names):
            return None
        stop = names.find(b"\0", name_off)
        if stop < 0:
            return None
        try:
            name = names[name_off:stop].decode("ascii")
        except UnicodeDecodeError:
            return None
        if section_type != 8:  # SHT_NOBITS occupies no file bytes
            if offset + size > len(data):
                return None
            end = max(end, offset + size)
        if name:
            sections[name] = {"offset": offset, "size": size}
    return {"machine": machine, "minimum_elf_bytes": end, "sections": sections}


def review(path, allow_sha256=()):
    if path.stat().st_size > MAX_FILE:
        raise ValueError("host exceeds 32 MiB limit")
    blob = path.read_bytes()
    host = inspect_elf(blob)
    if host is None:
        raise ValueError("expected ELF64 little-endian host with section table")
    digest = sha256(blob).hexdigest()
    objects = []
    pos = 4
    attempts = 0
    while (pos := blob.find(ELF_MAGIC, pos)) >= 0:
        attempts += 1
        if attempts > MAX_CANDIDATES:
            raise ValueError("too many embedded ELF candidates")
        inner = inspect_elf(blob, pos)
        if inner and inner["machine"] == 247:  # EM_BPF
            names = inner["sections"]
            tracepoints = sorted(n for n in names if n.startswith("tracepoint/"))
            objects.append({
                "file_offset": pos,
                "minimum_elf_bytes": inner["minimum_elf_bytes"],
                "rodata_bytes": names.get(".rodata", {}).get("size", 0),
                "tracepoint_sections": tracepoints,
                "has_btf": ".BTF" in names,
                "syscall_tracepoint": any(
                    n in ("tracepoint/raw_syscalls/sys_enter",
                          "tracepoint/raw_syscalls/sys_exit") for n in tracepoints),
            })
        pos += 4
    approved = digest.lower() in {value.lower() for value in allow_sha256}
    return {
        "event_type": "embedded_bpf_inventory",
        "host_sha256": digest,
        "host_machine": host["machine"],
        "approved_hash": approved,
        "embedded_bpf_count": len(objects),
        "embedded_bpf_objects": objects,
        "review_lead": not approved and any(x["syscall_tracepoint"] for x in objects),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", type=Path)
    parser.add_argument("--allow-sha256", action="append", default=[],
                        help="Known approved host digest; repeat for multiple values")
    args = parser.parse_args()
    if any(not re.fullmatch(r"[0-9a-fA-F]{64}", x) for x in args.allow_sha256):
        parser.error("--allow-sha256 expects a 64-character hex digest")
    print(json.dumps(review(args.host, args.allow_sha256), indent=2))


if __name__ == "__main__":
    main()
