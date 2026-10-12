"""Review JSONL signing records for repeated ECDSA r under one key and curve.

This is a review lead generator, not a signature verifier or key-recovery tool.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

MAX_BYTES = 5_000_000
MAX_EVENTS = 50_000


def audit_records(stream):
    seen = {}
    leads = []
    for number, line in enumerate(stream, 1):
        if number > MAX_EVENTS:
            raise ValueError("input exceeds 50,000 event limit")
        if not line.strip():
            continue
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError(f"line {number}: event must be an object")
        if event.get("event_type") != "Signed":
            continue
        for field in ("time", "key_id", "curve", "r", "s", "message_hash", "artifact_id"):
            if not isinstance(event.get(field), str) or not event[field]:
                raise ValueError(f"line {number}: missing or invalid {field}")
        try:
            stamp = datetime.fromisoformat(event["time"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"line {number}: invalid time") from exc
        if stamp.tzinfo is None:
            raise ValueError(f"line {number}: time needs an offset")
        if event["curve"] not in ("secp256k1", "P-256"):
            raise ValueError(f"line {number}: unsupported curve")
        for field in ("r", "s", "message_hash"):
            raw = event[field].lower().removeprefix("0x")
            if len(raw) != 64 or any(c not in "0123456789abcdef" for c in raw):
                raise ValueError(f"line {number}: {field} must be 32-byte hex")
            event[field] = raw
        bucket = (event["key_id"], event["curve"], event["r"])
        previous = seen.get(bucket)
        if previous is None:
            seen[bucket] = (event["message_hash"], event["s"], event["artifact_id"], event["time"], number)
            continue
        old_hash, old_s, old_artifact, old_time, old_line = previous
        if old_hash == event["message_hash"] and old_s == event["s"]:
            continue  # Duplicate log entry or repeat signing of identical digest.
        leads.append({
            "key_id": event["key_id"], "curve": event["curve"],
            "r": event["r"], "first_line": old_line, "second_line": number,
            "first_artifact": old_artifact, "second_artifact": event["artifact_id"],
            "first_time": old_time, "second_time": event["time"],
            "different_message_hash": old_hash != event["message_hash"],
            "assessment": "urgent_review" if old_hash != event["message_hash"] else "review_same_digest",
        })
    return leads


def audit(path: Path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("input exceeds 5 MB limit")
    with path.open("r", encoding="utf-8") as stream:
        return audit_records(stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    args = parser.parse_args()
    print(json.dumps({"leads": audit(args.events)}, indent=2))


if __name__ == "__main__":
    main()
