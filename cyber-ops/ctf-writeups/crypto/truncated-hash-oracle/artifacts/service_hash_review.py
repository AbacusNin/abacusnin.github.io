"""Review normalized service events for weak hash-verifier configuration.

Input is an authorized JSONL export of application audit events, never response bodies.
"""

import argparse
import json
from pathlib import Path

MAX_BYTES = 2_000_000
MAX_EVENTS = 20_000


def read_events(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("event file exceeds 2 MB limit")
    events = []
    with path.open(encoding="utf-8") as source:
        for number, line in enumerate(source, 1):
            if number > MAX_EVENTS:
                raise ValueError("event file exceeds event limit")
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"line {number}: invalid JSON") from error
            if not isinstance(event, dict) or event.get("kind") not in {"issued", "rejected"}:
                raise ValueError(f"line {number}: unsupported event")
            events.append(event)
    return events


def review(events, min_tag_bits=128):
    if min_tag_bits < 1:
        raise ValueError("minimum tag bits must be positive")
    findings = []
    for index, event in enumerate(events, 1):
        kind = event.get("kind")
        session = event.get("session")
        if not isinstance(session, str) or not session:
            raise ValueError(f"event {index}: session ID required")
        if kind == "issued":
            bits = event.get("tag_bits")
            construction = event.get("construction")
            if type(bits) is not int or bits < 1 or construction not in {"raw_hash", "hmac"}:
                raise ValueError(f"event {index}: tag_bits and construction required")
            if bits < min_tag_bits:
                findings.append({"session": session, "kind": "short-comparison", "bits": bits})
            if construction == "raw_hash":
                findings.append({"session": session, "kind": "unkeyed-verifier"})
        elif kind == "rejected":
            if type(event.get("echoed_digest")) is not bool:
                raise ValueError(f"event {index}: echoed_digest boolean required")
            if event["echoed_digest"]:
                findings.append({"session": session, "kind": "diagnostic-echo"})
        else:
            raise ValueError(f"event {index}: unsupported event")
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("--min-tag-bits", type=int, default=128,
                        help="Illustrative local policy floor; choose for the real protocol")
    args = parser.parse_args()
    print(json.dumps(review(read_events(args.events), args.min_tag_bits), indent=2))


if __name__ == "__main__":
    main()
