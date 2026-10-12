"""Find numeric-path 404 runs followed by a 200 in normalized web logs."""

import argparse
import ipaddress
import json
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path


MAX_BYTES = 10_000_000
MAX_LINES = 50_000
FAMILY = re.compile(r"^(/[^?#]+_)([0-9]+)$")


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps need a timezone")
    return parsed


def analyze(rows, threshold=100, window_seconds=300):
    if not 1 <= threshold <= 10_000 or not 1 <= window_seconds <= 3600:
        raise ValueError("threshold or window outside supported range")
    groups = defaultdict(deque)
    findings = []
    prior_time = None
    for number, row in enumerate(rows, 1):
        if number > MAX_LINES:
            raise ValueError("too many log events")
        when = timestamp(row["ts"])
        if prior_time is not None and when < prior_time:
            raise ValueError("events must be sorted by timestamp")
        prior_time = when
        source = str(ipaddress.ip_address(row["src_ip"]))
        host = row["host"]
        path = row["path"]
        status = int(row["status"])
        if not isinstance(host, str) or not host or not isinstance(path, str):
            raise ValueError("host and path are required")
        match = FAMILY.fullmatch(path)
        if not match:
            continue
        key = (source, host, match.group(1))
        failures = groups[key]
        cutoff = when - timedelta(seconds=window_seconds)
        while failures and failures[0][0] < cutoff:
            failures.popleft()
        if status == 404:
            failures.append((when, path))
        elif status == 200:
            distinct = len({candidate for _, candidate in failures})
            if distinct >= threshold:
                findings.append({"src_ip": source, "host": host, "path_family": key[2],
                                 "failed_requests": len(failures), "distinct_failed_paths": distinct,
                                 "first_failure": failures[0][0].isoformat(),
                                 "success_time": when.isoformat(), "success_path": path,
                                 "result": "enumeration_then_success"})
            failures.clear()
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="JSONL with ts, src_ip, host, path, status")
    parser.add_argument("--threshold", type=int, default=100)
    parser.add_argument("--window-seconds", type=int, default=300)
    args = parser.parse_args()
    with args.events.open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"input exceeds {MAX_BYTES} bytes")
    rows = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
    print(json.dumps({"findings": analyze(rows, args.threshold, args.window_seconds)}, indent=2))


if __name__ == "__main__":
    main()
