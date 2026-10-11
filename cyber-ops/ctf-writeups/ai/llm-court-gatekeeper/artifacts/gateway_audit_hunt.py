"""Check trusted gateway audit events for release and state-change invariants."""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys


MAX_BYTES = 5_000_000
MAX_LINES = 50_000
STRING_FIELDS = ("event_id", "timestamp", "session_id", "subject_id", "object_id")
BOOLEAN_FIELDS = ("released", "approved_transition")
VERSION_FIELDS = ("state_version_before", "state_version_after")


def check_event(event, line_number):
    if not isinstance(event, dict):
        raise ValueError(f"line {line_number}: expected an event object")
    for field in STRING_FIELDS:
        if not isinstance(event.get(field), str) or not event[field]:
            raise ValueError(f"line {line_number}: invalid {field}")
    try:
        stamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"line {line_number}: invalid timestamp") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError(f"line {line_number}: timestamp needs a timezone")
    if event.get("authz_decision") not in ("allow", "deny"):
        raise ValueError(f"line {line_number}: invalid authz_decision")
    if "authorized_object_id" not in event:
        raise ValueError(f"line {line_number}: missing authorized_object_id")
    scoped_object = event["authorized_object_id"]
    if scoped_object is not None and (not isinstance(scoped_object, str) or not scoped_object):
        raise ValueError(f"line {line_number}: invalid authorized_object_id")
    for field in BOOLEAN_FIELDS:
        if type(event.get(field)) is not bool:
            raise ValueError(f"line {line_number}: invalid {field}")
    for field in VERSION_FIELDS:
        if type(event.get(field)) is not int or event[field] < 0:
            raise ValueError(f"line {line_number}: invalid {field}")
    return event


def read_events(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"input exceeds {MAX_BYTES} bytes")
    events = []
    seen_ids = set()
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if line_number > MAX_LINES:
                raise ValueError(f"input exceeds {MAX_LINES} lines")
            if not raw.strip():
                continue
            try:
                event = check_event(json.loads(raw), line_number)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number}: invalid JSON") from exc
            if event["event_id"] in seen_ids:
                raise ValueError(f"line {line_number}: duplicate event_id")
            seen_ids.add(event["event_id"])
            events.append(event)
    return events


def find_invariant_breaks(events):
    findings = []
    for event in events:
        common = {field: event[field] for field in STRING_FIELDS}
        if event["released"] and event["authz_decision"] != "allow":
            findings.append({**common, "finding": "release_after_denial"})
        if event["released"] and event.get("authorized_object_id") != event["object_id"]:
            findings.append({**common, "finding": "released_outside_object_scope"})
        if (event["state_version_before"] != event["state_version_after"]
                and not event["approved_transition"]):
            findings.append({**common, "finding": "unapproved_state_change"})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="normalized trusted gateway audit JSONL")
    args = parser.parse_args()
    try:
        findings = find_invariant_breaks(read_events(args.input))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(findings, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
