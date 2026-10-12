"""Triage the six-value registry pattern in an offline regxml SOFTWARE export."""

import argparse
import base64
import json
from pathlib import Path
import xml.etree.ElementTree as ET


MAX_BYTES = 160 * 1024 * 1024
PATTERN = {
    ("microsoft", "sqmclient"): {"Token", "ConfigPath", "CacheMap", "SessionMap"},
    ("microsoft", "wbem"): {"SessionId"},
    ("classes", "installer"): {"Upload"},
}


def target_for(parts):
    tail = tuple(part.casefold() for part in parts[-2:])
    return tail if tail in PATTERN else None


def decoded_length(name, text):
    if name not in {"Token", "Upload"}:
        return None
    try:
        return len(base64.b64decode(text.strip(), validate=True))
    except (ValueError, base64.binascii.Error):
        return None


def review(path):
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Input must be a local XML file of at most 160 MiB")

    # The regxml format here is UTF-8 without a DTD. Reject entity definitions
    # before ElementTree has a chance to expand them.
    with path.open("rb") as stream:
        tail = b""
        while chunk := stream.read(1024 * 1024):
            block = (tail + chunk).upper()
            if b"\x00" in block or b"<!DOCTYPE" in block or b"<!ENTITY" in block:
                raise ValueError("Only UTF-8 regxml without DTD or entities is supported")
            tail = block[-16:]

    states = []
    elements = []
    found = {"/".join(key): [] for key in PATTERN}
    for event, elem in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            elements.append(elem)
            if elem.tag == "node":
                if len(states) >= 64:
                    raise ValueError("Registry nesting exceeds 64 nodes")
                parent = states[-1]["parts"] if states else ()
                states.append({"parts": parent + (elem.get("name", ""),), "values": {}})
            continue

        if elem.tag == "value" and states:
            state = states[-1]
            if target_for(state["parts"]):
                if len(state["values"]) >= 256:
                    raise ValueError("Target key has more than 256 values")
                name = elem.get("key", "")
                raw = elem.get("value", "")
                if len(raw) > 8192:
                    raise ValueError("Target value exceeds 8192 characters")
                state["values"][name] = {
                    "type": elem.get("type", ""),
                    "decoded_bytes": decoded_length(name, raw),
                }
        elif elem.tag == "node":
            state = states.pop()
            target = target_for(state["parts"])
            if target:
                found["/".join(target)].append(state["values"])

        if len(elements) > 1:
            elements[-2].remove(elem)
        elem.clear()
        elements.pop()

    details = []
    complete = True
    for target, names in PATTERN.items():
        snapshots = found["/".join(target)]
        best = max(snapshots, key=lambda row: len(names & row.keys()), default={})
        present = sorted(names & best.keys())
        details.append({
            "key_suffix": "\\".join(target),
            "matched_names": present,
            "missing_names": sorted(names - best.keys()),
            "types_and_lengths": {name: best[name] for name in present},
        })
        complete &= names <= best.keys()
    return {
        "complete_case_pattern": bool(complete),
        "keys": details,
        "meaning": "Triage lead only; confirm with a trusted baseline and endpoint context.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=Path, help="Offline regxml SOFTWARE export")
    args = parser.parse_args()
    try:
        print(json.dumps(review(args.xml), indent=2))
    except (OSError, ValueError, ET.ParseError) as exc:
        parser.exit(2, f"Cannot review XML: {exc}\n")


if __name__ == "__main__":
    main()
