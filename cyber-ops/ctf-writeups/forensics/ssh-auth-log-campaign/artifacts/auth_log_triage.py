#!/usr/bin/env python3
"""Offline SSH auth-log triage. Prints aggregates, never forwards log content."""

import argparse
import ipaddress
import json
import re
from collections import Counter
from pathlib import Path

HEADER = re.compile(r"^\w{3}\s+\d{1,2}\s+\d\d:\d\d:\d\d\s+\S+\s+([^\s\[:]+)(?:\[\d+\])?:\s*(.*)$")
FAILED = re.compile(r"\bFailed password for (?:invalid user )?(\S+) from (\S+)")
ACCEPTED = re.compile(r"\bAccepted \S+ for (\S+) from (\S+)")
CLOSED = re.compile(r"\bConnection closed by (?:invalid user \S+ )?(\S+)")
HTTP = re.compile(r"Bad protocol version identification ['\"](?:GET|POST|HEAD|CONNECT|PRI)\s")


def valid_ip(value):
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def analyze(path, max_line_bytes=65536):
    services = Counter()
    failed_users = Counter()
    failed_sources = Counter()
    accepted_sources = Counter()
    closed_sources = Counter()
    rejected = Counter()
    malformed = 0
    http_mismatch = 0
    lines = 0
    with Path(path).open("rb") as handle:
        for raw in handle:
            lines += 1
            if len(raw) > max_line_bytes:
                raise ValueError(f"line {lines} exceeds {max_line_bytes} bytes")
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            match = HEADER.match(line)
            if not match:
                malformed += 1
                continue
            service, message = match.groups()
            services[service] += 1
            if service != "sshd":
                continue
            event = FAILED.search(message)
            if event:
                user, source = event.groups()
                failed_users[user] += 1
                source = valid_ip(source)
                if source:
                    failed_sources[source] += 1
                else:
                    rejected["failed_bad_ip"] += 1
            event = ACCEPTED.search(message)
            if event:
                source = valid_ip(event.group(2))
                if source:
                    accepted_sources[source] += 1
                else:
                    rejected["accepted_bad_ip"] += 1
            event = CLOSED.search(message)
            if event:
                source = valid_ip(event.group(1))
                if source:
                    closed_sources[source] += 1
                else:
                    rejected["closed_bad_ip"] += 1
            if HTTP.search(message):
                http_mismatch += 1
    if sum(services.values()) + malformed != lines:
        raise AssertionError("coverage invariant failed")
    return {
        "line_count": lines,
        "service_counts": dict(services.most_common()),
        "unparsed_headers": malformed,
        "failed_users": dict(failed_users.most_common()),
        "failed_sources": dict(failed_sources.most_common()),
        "accepted_sources": dict(accepted_sources.most_common()),
        "closed_sources": dict(closed_sources.most_common()),
        "http_to_ssh_events": http_mismatch,
        "rejected_addresses": dict(rejected),
        "failure_then_success_sources": sorted(set(failed_sources) & set(accepted_sources)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path, help="local syslog file")
    parser.add_argument("--max-line-bytes", type=int, default=65536)
    args = parser.parse_args()
    if args.max_line_bytes < 1:
        parser.error("--max-line-bytes must be positive")
    print(json.dumps(analyze(args.log, args.max_line_bytes), indent=2))


if __name__ == "__main__":
    main()
