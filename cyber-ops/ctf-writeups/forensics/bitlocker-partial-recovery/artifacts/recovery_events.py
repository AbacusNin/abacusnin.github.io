"""Triage normalized BitLocker recovery activity without emitting secret material."""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

MAX_BYTES = 1024 * 1024
WINDOW = timedelta(minutes=15)


def parse_time(value):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return moment.astimezone(timezone.utc)


def detect(events, threshold=3):
    findings = []
    reads = defaultdict(list)
    for index, event in enumerate(events, 1):
        if not isinstance(event, dict):
            raise ValueError("each event must be a JSON object")
        kind = event.get("kind")
        if kind not in {"recovery_unlock", "ad_recovery_read"}:
            raise ValueError(f"line {index}: unknown event kind")
        moment = parse_time(event["time"])
        actor = event.get("actor")
        if not isinstance(actor, str) or not actor:
            raise ValueError(f"line {index}: missing actor")
        if event.get("approved_case") is True:
            continue
        if kind == "recovery_unlock":
            findings.append({"kind": "unapproved_recovery_unlock", "actor": actor,
                             "time": moment.isoformat()})
        elif event.get("attribute_name") == "ms-FVE-RecoveryPassword":
            target = event.get("target_id")
            if not isinstance(target, str) or not target:
                raise ValueError(f"line {index}: missing target_id")
            reads[actor].append((moment, target))
    for actor, items in reads.items():
        items.sort()
        for i, (moment, _) in enumerate(items):
            window = {target for seen, target in items[i:] if seen - moment <= WINDOW}
            if len(window) >= threshold:
                findings.append({"kind": "recovery_read_spike", "actor": actor,
                                 "time": moment.isoformat(), "distinct_targets": len(window)})
                break
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="normalized event JSONL file, at most 1 MiB")
    parser.add_argument("--threshold", type=int, default=3)
    args = parser.parse_args()
    try:
        if not 2 <= args.threshold <= 1000:
            raise ValueError("threshold must be 2..1000")
        path = Path(args.jsonl)
        if path.stat().st_size > MAX_BYTES:
            raise ValueError("file exceeds 1 MiB")
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(json.dumps({"findings": detect(events, args.threshold)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"triage failed: {exc}\n")


if __name__ == "__main__":
    main()
