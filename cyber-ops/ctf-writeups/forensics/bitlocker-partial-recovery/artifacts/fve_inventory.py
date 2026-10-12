"""Read-only, content-hidden inventory of a BitLocker FVE volume header."""

import argparse
import json
import struct
import uuid
from pathlib import Path

SHARED_BITLOCKER_GUID = uuid.UUID("4967d63b-2e29-4ad8-8399-f6a339e3d001")
METHODS = {0x8002: "AES-CBC 128", 0x8003: "AES-CBC 256", 0x8004: "AES-XTS 128", 0x8005: "AES-XTS 256"}
PROTECTORS = {0x0000: "clear key", 0x0100: "TPM", 0x0200: "startup key", 0x0500: "TPM+PIN", 0x0800: "recovery password", 0x2000: "user password"}
MAX_BLOCK = 1024 * 1024


def read_exact(handle, offset, size, file_size):
    if offset < 0 or size < 0 or offset + size > file_size:
        raise ValueError("metadata points outside image")
    handle.seek(offset)
    data = handle.read(size)
    if len(data) != size:
        raise ValueError("short image read")
    return data


def walk_entries(block, start, end):
    pos = start
    while pos + 8 <= end:
        size, entry_type, value_type, version = struct.unpack_from("<HHHH", block, pos)
        if size == 0 and not any(block[pos:end]):
            return
        if size < 8 or pos + size > end:
            raise ValueError("invalid FVE entry length")
        yield pos, size, entry_type, value_type
        pos += size
    if any(block[pos:end]):
        raise ValueError("nonzero trailing FVE bytes")


def inspect(path):
    image = Path(path)
    file_size = image.stat().st_size
    if file_size < 512:
        raise ValueError("image is shorter than a volume header")
    with image.open("rb") as handle:
        header = read_exact(handle, 0, 512, file_size)
        if header[3:11] != b"-FVE-FS-":
            raise ValueError("missing FVE volume signature")
        identifier = uuid.UUID(bytes_le=header[0xA0:0xB0])
        if identifier != SHARED_BITLOCKER_GUID:
            raise ValueError("unrecognized BitLocker identifier")
        offsets = struct.unpack_from("<QQQ", header, 0xB0)
        if not all(offsets) or len(set(offsets)) != 3:
            raise ValueError("expected three distinct metadata offsets")
        blocks = []
        for offset in offsets:
            preface = read_exact(handle, offset + 0x40, 48, file_size)
            size, version, header_size, size_copy = struct.unpack_from("<IIII", preface)
            if not (48 <= header_size <= size <= MAX_BLOCK):
                raise ValueError("invalid metadata bounds")
            block = read_exact(handle, offset + 0x40, size, file_size)
            method_raw = struct.unpack_from("<I", block, 0x24)[0]
            method = method_raw & 0xFFFF
            protector_info = []
            description = False
            for pos, entry_size, entry_type, value_type in walk_entries(block, header_size, size):
                if entry_type == 0x0007 and value_type == 0x0002:
                    description = True
                if entry_type != 0x0002 or value_type != 0x0008:
                    continue
                if entry_size < 36:
                    raise ValueError("short VMK entry")
                protection = struct.unpack_from("<H", block, pos + 8 + 26)[0]
                property_types = {
                    sub_value
                    for _, _, _, sub_value in walk_entries(block, pos + 8 + 28, pos + entry_size)
                }
                protector_info.append({
                    "type": PROTECTORS.get(protection, f"unknown 0x{protection:04x}"),
                    "stretch_key_property": 0x0003 in property_types,
                    "aes_ccm_property": 0x0005 in property_types,
                })
            blocks.append({
                "offset": f"0x{offset:x}",
                "version": version,
                "encryption_method": METHODS.get(method, f"unknown 0x{method:04x}"),
                "encryption_method_raw": f"0x{method_raw:08x}",
                "description_entry": description,
                "protectors": protector_info,
            })
    fingerprints = [(b["version"], b["encryption_method"], b["protectors"]) for b in blocks]
    return {
        "image_bytes": file_size,
        "fve_signature": True,
        "shared_bitlocker_identifier": True,
        "metadata_blocks": blocks,
        "metadata_agree_on_method_and_protectors": len(set(map(repr, fingerprints))) == 1,
        "note": "The shared GUID does not identify BitLocker To Go by itself; use removable-media context.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", help="local raw volume image; never uploaded")
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.image), indent=2))
    except (OSError, ValueError, struct.error) as exc:
        parser.exit(2, f"inventory failed: {exc}\n")


if __name__ == "__main__":
    main()
