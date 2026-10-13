#!/usr/bin/env python3
"""Review normalized ISO 8583 events without retaining account numbers."""

import argparse
from collections import defaultdict
from datetime import date as calendar_date
import json
from pathlib import Path

ALLOWED_MTI = {"0100", "0110", "0400", "0410", "0800", "0810"}
REQUIRED = {"event_id", "terminal_id", "processing_date", "session_id", "mti", "stan"}
ALLOWED = REQUIRED | {"original_stan", "response_code"}


def review(events):
    seen = set()
    by_key = defaultdict(list)
    sessions = defaultdict(list)
    for event in events:
        if not isinstance(event, dict) or not REQUIRED <= event.keys():
            raise ValueError("event lacks required normalized fields")
        if not event.keys() <= ALLOWED:
            raise ValueError("unexpected field; account and payment data are not accepted")
        if any(not isinstance(event[key], str) or not 1 <= len(event[key]) <= 80 for key in REQUIRED):
            raise ValueError("invalid field type or length")
        if event["mti"] not in ALLOWED_MTI or not (event["stan"].isdigit() and len(event["stan"]) == 6):
            raise ValueError("unsupported MTI or STAN")
        try:
            calendar_date.fromisoformat(event["processing_date"])
        except ValueError as exc:
            raise ValueError("processing_date must be ISO calendar date") from exc
        original = event.get("original_stan")
        if original is not None and (not isinstance(original, str) or len(original) != 6 or not original.isdigit()):
            raise ValueError("original_stan must have six digits")
        if event["event_id"] in seen:
            raise ValueError("duplicate event_id")
        seen.add(event["event_id"])
        key = (event["terminal_id"], event["processing_date"], event["stan"])
        by_key[key].append(event)
        sessions[(event["terminal_id"], event["processing_date"], event["session_id"])].append(event)

    findings = []
    for (terminal, date, stan), group in sorted(by_key.items()):
        requests = [event for event in group if event["mti"] == "0100"]
        if len(requests) > 1:
            finding_type = ("cross_session_repeated_stan" if len({e["session_id"] for e in requests}) > 1
                            else "same_session_retry_or_duplicate")
            findings.append({"type": finding_type, "terminal_id": terminal,
                             "processing_date": date, "stan": stan,
                             "request_count": len(requests),
                             "event_ids": [e["event_id"] for e in requests]})

    for (terminal, date, session), group in sorted(sessions.items()):
        requests = [e for e in group if e["mti"] == "0100"]
        responses = [e for e in group if e["mti"] == "0110"]
        reversals = [e for e in group if e["mti"] == "0400"]
        if len(requests) > len(responses):
            findings.append({"type": "response_not_observed", "terminal_id": terminal,
                             "session_id": session, "request_count": len(requests),
                             "response_count": len(responses),
                             "caution": "capture loss, timeout, retry, and log scope need review"})
        for reversal in reversals:
            original = reversal.get("original_stan")
            if not original:
                state = "reference_unavailable"
            elif any(e["mti"] == "0100" for e in by_key.get((terminal, reversal["processing_date"], original), [])):
                state = "reference_seen_in_input"
            else:
                state = "reference_not_seen_in_input"
            findings.append({"type": "reversal_reference_review", "terminal_id": terminal,
                             "session_id": session, "event_id": reversal["event_id"],
                             "reference_state": state,
                             "caution": "this does not establish gateway approval or settlement"})
    return {"events_reviewed": len(events), "findings": findings}


def load_jsonl(path: Path):
    if path.stat().st_size > 5_000_000:
        raise ValueError("input exceeds 5 MB")
    events = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if len(events) >= 20_000:
                raise ValueError("input exceeds 20,000 events")
            if line.strip():
                events.append(json.loads(line))
    return events


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="normalized, tokenized JSONL events")
    args = parser.parse_args()
    print(json.dumps(review(load_jsonl(args.events)), indent=2))


if __name__ == "__main__":
    main()
