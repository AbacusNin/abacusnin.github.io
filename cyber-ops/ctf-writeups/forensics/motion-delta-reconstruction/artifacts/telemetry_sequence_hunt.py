"""Correlate normalized input-access, file-write, and network events."""

import argparse
import json
from pathlib import Path


KINDS = {"input_open", "telemetry_write", "network_connection"}
MAX_BYTES = 2_000_000
MAX_EVENTS = 10_000


def load_events(path: Path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("event file exceeds the 2 MB review limit")
    events = []
    for number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        if len(events) >= MAX_EVENTS:
            raise ValueError("event count exceeds review limit")
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ValueError(f"line {number}: event must be an object")
        if (event.get("kind") not in KINDS or
                not isinstance(event.get("time_ms"), int) or
                isinstance(event.get("time_ms"), bool) or
                not all(isinstance(event.get(key), str) and event[key] for key in ("host", "process_guid"))):
            raise ValueError(f"line {number}: invalid event identity, time, or kind")
        if event["kind"] == "telemetry_write" and not isinstance(event.get("path"), str):
            raise ValueError(f"line {number}: write needs a path")
        if event["kind"] == "network_connection" and not isinstance(event.get("destination"), str):
            raise ValueError(f"line {number}: connection needs a destination")
        events.append(event)
    return events


def hunt(events, window_ms=300_000):
    by_process = {}
    for event in events:
        by_process.setdefault((event["host"], event["process_guid"]), []).append(event)
    leads = []
    for (host, process_guid), group in by_process.items():
        group.sort(key=lambda event: event["time_ms"])
        inputs = [event for event in group if event["kind"] == "input_open"]
        writes = [event for event in group if event["kind"] == "telemetry_write"]
        connections = [event for event in group if event["kind"] == "network_connection"]
        for write in writes:
            prior = [event for event in inputs
                     if 0 <= write["time_ms"] - event["time_ms"] <= window_ms]
            after = [event for event in connections
                     if 0 <= event["time_ms"] - write["time_ms"] <= window_ms]
            if prior and after:
                leads.append({
                    "host": host,
                    "process_guid": process_guid,
                    "write_time_ms": write["time_ms"],
                    "path": write["path"],
                    "destination": after[0]["destination"],
                    "classification": "review lead; content transfer unproven",
                })
    return leads


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()
    print(json.dumps(hunt(load_events(args.jsonl)), indent=2))


if __name__ == "__main__":
    main()
