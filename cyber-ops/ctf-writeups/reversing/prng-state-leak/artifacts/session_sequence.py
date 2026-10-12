#!/usr/bin/env python3
"""Review normalized application operation logs for the case's sequence.

Input is a local JSONL file with ts (ISO 8601 UTC), session_id, source_ip,
and operation. This is a triage aid, not a production detector.
"""

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import sys

STATE_READS = {"getFragment", "getStatus", "getTelemetry"}
MAX_BYTES = 2_000_000
MAX_EVENTS = 20_000


def load_events(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ValueError("Input exceeds 2 MB")
    events = []
    with p.open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if number > MAX_EVENTS:
                raise ValueError("Input exceeds 20,000 lines")
            item = json.loads(line)
            for key in ("ts", "session_id", "source_ip", "operation"):
                if not isinstance(item.get(key), str) or not item[key]:
                    raise ValueError(f"Line {number}: missing {key}")
            stamp = datetime.fromisoformat(item["ts"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError(f"Line {number}: timestamp needs timezone")
            item["stamp"] = stamp.astimezone(timezone.utc)
            events.append(item)
    return events


def review(events, window_seconds=5, min_submissions=4):
    sessions = defaultdict(list)
    for item in events:
        sessions[(item["source_ip"], item["session_id"])].append(item)
    findings = []
    for (source, session), rows in sessions.items():
        rows.sort(key=lambda row: row["stamp"])
        for pos, row in enumerate(rows):
            if row["operation"] not in STATE_READS:
                continue
            later = [
                event for event in rows[pos + 1:]
                if event["operation"].startswith("submit")
                and 0 <= (event["stamp"] - row["stamp"]).total_seconds() <= window_seconds
            ]
            if len(later) >= min_submissions:
                findings.append({
                    "source_ip": source,
                    "session_id": session,
                    "state_read": row["operation"],
                    "submissions": len(later),
                    "window_seconds": window_seconds,
                })
                break
    return findings


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python session_sequence.py events.jsonl")
    print(json.dumps(review(load_events(sys.argv[1])), indent=2))


if __name__ == "__main__":
    main()
