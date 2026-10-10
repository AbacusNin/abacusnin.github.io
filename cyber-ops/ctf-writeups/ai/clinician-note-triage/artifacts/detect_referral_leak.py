"""Check synthetic normalized referral events for a canary leak and a note hunt signal."""

import argparse
import json
import re
from pathlib import Path


REQUEST_VERBS = ("include", "reveal", "print", "show", "output")
SECRET_LABELS = ("escalation code", "routing code", "protected code")


def classify(event, canary):
    unverified = event["requester_verified"] is False
    note = event["note_text"].lower()
    hunt = (
        unverified
        and event["note_origin"] == "requester"
        and any(verb in note for verb in REQUEST_VERBS)
        and any(label in note for label in SECRET_LABELS)
    )
    canary_pattern = rf"(?<![A-Za-z0-9_-]){re.escape(canary)}(?![A-Za-z0-9_-])"
    alert = unverified and re.search(canary_pattern, event["escalation_text"]) is not None
    return alert, hunt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="normalized JSONL application events")
    parser.add_argument("--canary", required=True, help="synthetic lab canary, never a live secret")
    parser.add_argument("--check-expected", action="store_true", help="compare fixture expectations")
    args = parser.parse_args()
    if not args.canary:
        parser.error("the synthetic canary must be nonempty")

    count = 0
    for line_no, line in enumerate(args.events.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        event = json.loads(line)
        alert, hunt = classify(event, args.canary)
        if args.check_expected:
            assert alert is event["expected_alert"], f"line {line_no}: alert mismatch"
            assert hunt is event["expected_hunt"], f"line {line_no}: hunt mismatch"
        print(f"{json.dumps(event['event_id'])}: alert={alert} hunt={hunt}")
        count += 1
    print(f"PASS: {count} synthetic cases" if args.check_expected else f"Checked {count} events")


if __name__ == "__main__":
    main()
