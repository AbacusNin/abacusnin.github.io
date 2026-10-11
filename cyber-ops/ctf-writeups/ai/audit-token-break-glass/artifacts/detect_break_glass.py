"""Review normalized emergency-access decisions without reading record identifiers."""

import argparse
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys


MAX_BYTES = 2_000_000
MAX_LINES = 20_000
WINDOW = timedelta(minutes=15)


def validate_event(event, line_no):
    if not isinstance(event, dict):
        raise ValueError(f"line {line_no}: expected an object")
    for field in ("ts", "session_id", "event_type", "result"):
        if not isinstance(event.get(field), str) or not event[field]:
            raise ValueError(f"line {line_no}: invalid {field}")
    try:
        stamp = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"line {line_no}: invalid ts") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError(f"line {line_no}: ts needs a timezone")
    if event["event_type"] == "authority_assertion" and type(event.get("auth_code_presented")) is not bool:
        raise ValueError(f"line {line_no}: authority event needs auth_code_presented")
    if event["event_type"] == "break_glass_attempt" and event["result"] == "deny":
        if not isinstance(event.get("deny_reason"), str) or not event["deny_reason"]:
            raise ValueError(f"line {line_no}: denial needs deny_reason")
    return stamp, line_no, event


def load_events(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("input exceeds 2 MB")
    events = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, 1):
            if line_no > MAX_LINES:
                raise ValueError("input exceeds 20,000 lines")
            if not raw.strip():
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {line_no}: invalid JSON") from exc
            events.append(validate_event(event, line_no))
    return sorted(events, key=lambda item: (item[0], item[1]))


def analyze(events):
    failures = defaultdict(deque)
    threshold_reported = set()
    findings = []
    reviews = []
    for stamp, line_no, event in events:
        session = event["session_id"]
        kind = event["event_type"]
        result = event["result"]
        if kind == "authority_assertion" and event["auth_code_presented"] is False:
            findings.append({"session_id": session, "signal": "authority_without_credential", "line": line_no})
        if kind == "mrn_disclosure_attempt" and result == "refuse":
            findings.append({"session_id": session, "signal": "identifier_disclosure_probe", "line": line_no})
        if kind == "break_glass_attempt" and result == "deny" and event["deny_reason"] == "MRN mismatch":
            recent = failures[session]
            while recent and stamp - recent[0] > WINDOW:
                recent.popleft()
            recent.append(stamp)
            if len(recent) >= 3 and session not in threshold_reported:
                findings.append({"session_id": session, "signal": "three_identifier_denials_15m", "line": line_no})
                threshold_reported.add(session)
        if kind == "break_glass_grant" and result == "audit_token_issued":
            reviews.append({"session_id": session, "review": "emergency_access_record", "line": line_no})
    return {"findings": findings, "reviews": reviews}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="trusted normalized JSONL events")
    args = parser.parse_args()
    try:
        report = analyze(load_events(args.events))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
