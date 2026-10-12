"""Synthetic signing-service audit detector. JSONL input, review leads as output."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must have an offset")
    return parsed.astimezone(timezone.utc)


def analyze(events: list[dict], *, window_minutes: int = 10, small_count: int = 3) -> list[dict]:
    leads: list[dict] = []
    recent: dict[tuple[str, str], list[datetime]] = defaultdict(list)
    for event in sorted(events, key=lambda item: parse_time(item["time"])):
        when = parse_time(event["time"])
        kind = event.get("kind")
        client = str(event.get("client_id", ""))
        key = str(event.get("key_id", ""))
        if not client or not key:
            raise ValueError("client_id and key_id required")
        if kind == "fault_validation_failed":
            leads.append({"time": event["time"], "client_id": client, "key_id": key, "reason": "output-fault"})
        elif kind == "sign_request":
            bits = event.get("message_bits")
            if not isinstance(bits, int) or bits < 0:
                raise ValueError("sign_request needs nonnegative message_bits")
            if bits <= 3:
                bucket = recent[(client, key)]
                bucket[:] = [item for item in bucket if when - timedelta(minutes=window_minutes) < item <= when]
                bucket.append(when)
                if len(bucket) == small_count:
                    leads.append({"time": event["time"], "client_id": client, "key_id": key, "reason": "small-message-probes"})
        else:
            raise ValueError(f"unsupported kind: {kind}")
    return leads


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()
    events = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    for finding in analyze(events):
        print(json.dumps(finding, sort_keys=True))


if __name__ == "__main__":
    main()
