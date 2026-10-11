#!/usr/bin/env python3
"""Triage ordered lookup responses for a sustained midpoint-search pattern.

This is a synthetic application-log proof of concept, not a production rule.
It does not contact an endpoint or attempt to recover a secret.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HEX_ID = re.compile(r"^[A-Z]+-([0-9A-F]{4})$")
RESPONSES = {"AFTER", "BEFORE"}


def parse_event(line: str, number: int) -> dict:
    event = json.loads(line)
    required = ("timestamp", "actor", "endpoint", "candidate", "response")
    if not isinstance(event, dict) or any(key not in event for key in required):
        raise ValueError(f"line {number}: required event field missing")
    for key in required:
        if not isinstance(event[key], str) or not event[key]:
            raise ValueError(f"line {number}: {key} must be a nonempty string")
    try:
        event["parsed_time"] = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"line {number}: invalid timestamp") from exc
    if event["parsed_time"].tzinfo is None:
        raise ValueError(f"line {number}: timestamp must include a timezone")
    match = HEX_ID.fullmatch(event["candidate"])
    if match is None:
        raise ValueError(f"line {number}: candidate must be PREFIX-XXXX uppercase hex")
    event["suffix"] = int(match.group(1), 16)
    if event["response"] not in RESPONSES | {"MATCH", "DENY"}:
        raise ValueError(f"line {number}: unknown response class")
    return event


def find_runs(events: list[dict], minimum: int = 5, max_gap_seconds: int = 300) -> list[dict]:
    if minimum < 2 or max_gap_seconds < 1:
        raise ValueError("minimum must be >= 2 and max gap must be >= 1")
    groups = defaultdict(list)
    for event in events:
        groups[(event["actor"], event["endpoint"])].append(event)

    findings = []
    for (actor, endpoint), group in groups.items():
        group.sort(key=lambda item: item["parsed_time"])
        low, high = 0, 0xFFFF
        run = []
        previous = None

        def close_run() -> None:
            if len(run) >= minimum:
                findings.append({
                    "actor": actor,
                    "endpoint": endpoint,
                    "midpoint_queries": len(run),
                    "first_seen": run[0]["timestamp"],
                    "last_seen": run[-1]["timestamp"],
                    "status": "synthetic_midpoint_pattern",
                })

        for event in group:
            gap = None if previous is None else (event["parsed_time"] - previous["parsed_time"]).total_seconds()
            expected = (low + high) // 2
            follows = (
                event["response"] in RESPONSES
                and event["suffix"] == expected
                and low <= high
                and (gap is None or 0 <= gap <= max_gap_seconds)
            )
            if not follows:
                close_run()
                run = []
                low, high = 0, 0xFFFF
                # A new run can begin at the full-space midpoint on this event.
                follows = event["response"] in RESPONSES and event["suffix"] == 0x7FFF
            if follows:
                run.append(event)
                if event["response"] == "AFTER":
                    low = event["suffix"] + 1
                else:
                    high = event["suffix"] - 1
            previous = event
        close_run()
    return sorted(findings, key=lambda item: (item["actor"], item["first_seen"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="JSONL application request events")
    parser.add_argument("--minimum", type=int, default=5, help="minimum consecutive midpoint responses")
    parser.add_argument("--max-gap-seconds", type=int, default=300)
    args = parser.parse_args()
    events = [parse_event(line, number) for number, line in enumerate(args.events.read_text(encoding="utf-8").splitlines(), 1) if line.strip()]
    print(json.dumps(find_runs(events, args.minimum, args.max_gap_seconds), indent=2))


if __name__ == "__main__":
    main()
