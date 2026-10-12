"""Offline triage of Apache Combined logs for regular polling plus booking bursts.

This is a candidate generator, not an account attribution or abuse verdict.
"""

import argparse
import json
import re
import statistics
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


LINE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<time>[^]]+)\] '
    r'"(?P<method>GET|POST) (?P<path>\S+) HTTP/[0-9.]+" '
    r'(?P<status>\d{3}) \S+ "[^"]*" "[^"]*"$'
)
MAX_BYTES = 10_000_000
MAX_LINES = 100_000


def parse_line(line):
    match = LINE.fullmatch(line.rstrip("\r\n"))
    if not match:
        raise ValueError("unsupported or malformed Combined Log Format line")
    record = match.groupdict()
    stamp = record["time"].strip()
    # The exercise log has an empty timezone. Standard Apache offsets work too.
    record["time"] = datetime.strptime(stamp, "%d/%b/%Y:%H:%M:%S %z" if " " in stamp else "%d/%b/%Y:%H:%M:%S")
    return record


def read_log(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("log exceeds 10 MB limit")
    records = []
    with path.open(encoding="utf-8") as source:
        for index, line in enumerate(source, 1):
            if index > MAX_LINES:
                raise ValueError("log exceeds line limit")
            try:
                records.append(parse_line(line))
            except ValueError as error:
                raise ValueError(f"line {index}: {error}") from error
    return records


def sessions(times, gap=600):
    groups = []
    for instant in sorted(times):
        if not groups or (instant - groups[-1][-1]).total_seconds() > gap:
            groups.append([])
        groups[-1].append(instant)
    return groups


def analyze(records, availability, reserve, min_polls=4, cv_limit=0.05):
    by_ip = defaultdict(list)
    for record in records:
        by_ip[record["ip"]].append(record)
    findings = []
    for ip, events in by_ip.items():
        polls = [e["time"] for e in events if e["method"] == "GET" and e["path"] == availability]
        posts = [e["time"] for e in events if e["method"] == "POST" and e["path"] == reserve]
        qualifying = []
        burst_pairs = 0
        for group in sessions(polls):
            if len(group) < min_polls:
                continue
            intervals = [(b - a).total_seconds() for a, b in zip(group, group[1:])]
            if min(intervals) <= 0:
                continue
            mean = statistics.mean(intervals)
            cv = statistics.stdev(intervals) / mean if len(intervals) > 1 else 0
            if cv < cv_limit:
                # Pair must follow this poll session, not merely share an IP on another day.
                nearby = sorted(p for p in posts if group[-1] <= p <= group[-1] + timedelta(seconds=5))
                pairs = sum(0 <= (b - a).total_seconds() <= 1 for a, b in zip(nearby, nearby[1:]))
                if pairs:
                    qualifying.append({"polls": len(group), "mean_seconds": round(mean, 2), "cv": round(cv, 4)})
                    burst_pairs += pairs
        if qualifying and burst_pairs:
            findings.append({"source": ip, "poll_count": len(polls), "post_count": len(posts),
                             "best_session": max(qualifying, key=lambda x: x["polls"]), "burst_pairs": burst_pairs})
    return sorted(findings, key=lambda finding: finding["source"])


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("log", type=Path)
    cli.add_argument("--availability", required=True, help="Exact GET path")
    cli.add_argument("--reserve", required=True, help="Exact POST path")
    args = cli.parse_args()
    records = read_log(args.log)
    result = {"events": len(records), "sources": len({r["ip"] for r in records}),
              "candidates": analyze(records, args.availability, args.reserve)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
