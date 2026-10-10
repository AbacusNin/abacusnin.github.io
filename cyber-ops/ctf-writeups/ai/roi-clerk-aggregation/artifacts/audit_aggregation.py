"""Find synthetic cumulative disclosures in a time-ordered gateway event export."""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def audit(events, composites):
    state = defaultdict(lambda: {"schema_seen": False, "fields": defaultdict(set), "reported": set()})
    findings = []
    last_time = None

    for event in events:
        event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
        if last_time and event_time < last_time:
            raise ValueError("events must be ordered by timestamp")
        last_time = event_time
        key = (event["tenant_id"], event["caller_id"], event["record_id"], event["session_id"])
        session = state[key]
        action = event["action"]
        grants = set(event["composite_grants"])

        if action == "schema_enumeration" and event["decision"] == "allowed":
            session["schema_seen"] = True
        elif action == "field_disclosure" and event["decision"] == "allowed":
            field = event["field_id"]
            for composite_id, required in composites.items():
                if field not in required or composite_id in grants:
                    continue
                seen = session["fields"][composite_id]
                seen.add(field)
                if required <= seen and composite_id not in session["reported"]:
                    findings.append({
                        "event_id": event["event_id"],
                        "finding": "cumulative_disclosure",
                        "composite_id": composite_id,
                        "schema_seen": session["schema_seen"],
                    })
                    session["reported"].add(composite_id)
        elif action == "verification" and event["decision"] == "allowed":
            composite_id = event["composite_id"]
            if composite_id in composites and composite_id not in grants:
                findings.append({
                    "event_id": event["event_id"],
                    "finding": "unauthorized_verification",
                    "composite_id": composite_id,
                    "schema_seen": session["schema_seen"],
                })
        elif action not in {"schema_enumeration", "field_disclosure", "verification"}:
            raise ValueError(f"unknown action at event {event['event_id']}")

    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("--expected", type=Path, help="compare with synthetic fixture expectations")
    args = parser.parse_args()

    events = [json.loads(line) for line in args.events.read_text(encoding="utf-8").splitlines() if line.strip()]
    policy = json.loads(args.policy.read_text(encoding="utf-8"))
    composites = {item["id"]: set(item["component_fields"]) for item in policy["composites"]}
    findings = audit(events, composites)
    for finding in findings:
        print(json.dumps(finding, sort_keys=True))
    if args.expected:
        expected = json.loads(args.expected.read_text(encoding="utf-8"))
        if findings != expected:
            raise SystemExit("FAIL: findings differ from fixture expectations")
        print(f"PASS: {len(events)} synthetic events, {len(findings)} expected findings")


if __name__ == "__main__":
    main()
