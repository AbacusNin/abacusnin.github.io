"""Find repeated failed verification of one token across multiple epochs.

This is a bounded, local proof of concept for normalized application audit logs.
It does not inspect packets, infer key compromise, or replace server-side checks.
"""

import argparse
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys


MAX_BYTES = 10_000_000
MAX_EVENTS = 100_000
WINDOW = timedelta(minutes=10)
MIN_FAILURES = 20
MIN_EPOCHS = 5
REQUIRED = ("TimeGenerated", "EventType", "Result", "TokenHash", "SrcEntity", "DstEntity", "RotationEpoch")


def parse_time(value, line_number):
    if not isinstance(value, str):
        raise ValueError(f"line {line_number}: TimeGenerated must be an ISO 8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"line {line_number}: invalid TimeGenerated") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"line {line_number}: TimeGenerated needs a timezone")
    return parsed.astimezone(timezone.utc)


def read_events(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"input exceeds {MAX_BYTES} bytes")
    events = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if line_number > MAX_EVENTS:
                raise ValueError(f"input exceeds {MAX_EVENTS} lines")
            if not raw.strip():
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_number}: invalid JSON") from exc
            if not isinstance(event, dict):
                raise ValueError(f"line {line_number}: expected an event object")
            if event.get("EventType") != "VerifyResult":
                continue
            for field in REQUIRED:
                if field not in event:
                    raise ValueError(f"line {line_number}: missing {field}")
            if event["Result"] not in ("INVALID", "VALID"):
                raise ValueError(f"line {line_number}: unexpected Result")
            for field in ("TokenHash", "SrcEntity", "DstEntity"):
                if not isinstance(event[field], str) or not event[field]:
                    raise ValueError(f"line {line_number}: invalid {field}")
            if type(event["RotationEpoch"]) is not int or event["RotationEpoch"] < 0:
                raise ValueError(f"line {line_number}: invalid RotationEpoch")
            event["_time"] = parse_time(event["TimeGenerated"], line_number)
            events.append(event)
    return sorted(events, key=lambda event: event["_time"])


def find_oracle_patterns(events):
    windows = defaultdict(deque)
    reported = set()
    findings = []
    for event in events:
        key = (event["TokenHash"], event["SrcEntity"], event["DstEntity"])
        if event["Result"] != "INVALID" or key in reported:
            continue
        window = windows[key]
        window.append(event)
        while window and event["_time"] - window[0]["_time"] > WINDOW:
            window.popleft()
        epochs = {item["RotationEpoch"] for item in window}
        if len(window) >= MIN_FAILURES and len(epochs) >= MIN_EPOCHS:
            findings.append({
                "type": "repeated_invalid_verification_across_epochs",
                "TokenHash": key[0],
                "SrcEntity": key[1],
                "DstEntity": key[2],
                "FirstSeen": window[0]["_time"].isoformat().replace("+00:00", "Z"),
                "LastSeen": event["_time"].isoformat().replace("+00:00", "Z"),
                "Failures": len(window),
                "EpochDiversity": len(epochs),
            })
            reported.add(key)
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="normalized JSONL application audit events")
    args = parser.parse_args()
    try:
        result = find_oracle_patterns(read_events(args.input))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
