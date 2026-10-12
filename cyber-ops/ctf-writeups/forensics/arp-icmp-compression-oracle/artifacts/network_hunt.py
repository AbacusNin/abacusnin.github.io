#!/usr/bin/env python3
"""Offline triage of normalized ARP, ICMP redirect, and HTTP response events.

Input: JSON Lines with event types arp, icmp, or http. This is a local proof
of concept, not a packet decoder or a production alert rule.
"""
import argparse
import collections
import json
import sys

MAX_BYTES = 1_000_000
MAX_EVENTS = 10_000
MAX_LINE = 4_096


def analyze(events, gateways):
    findings = []
    arp = collections.defaultdict(lambda: collections.defaultdict(set))
    posts = collections.Counter()
    lengths = collections.defaultdict(list)
    for line, event in enumerate(events, 1):
        kind = event.get("type")
        if kind == "arp" and event.get("opcode") == 2:
            arp[event["mac"]][event["ip"]].add(event.get("sensor", "unknown"))
        elif kind == "icmp" and event.get("icmp_type") == 5:
            if event["src"] not in gateways:
                findings.append({"kind": "unauthorized_redirect", "line": line,
                                 "src": event["src"], "gateway": event.get("gateway")})
        elif kind == "http" and event.get("method") == "POST":
            key = (event["src"], event["dst"], event["uri"], int(event["ts"] // 60))
            posts[key] += 1
            if event.get("response_bytes") is not None:
                lengths[key].append(event["response_bytes"])
    for mac, claims in arp.items():
        if len(claims) > 1:
            findings.append({"kind": "multi_ip_arp_claim", "mac": mac,
                             "ips": sorted(claims)})
    for key, count in posts.items():
        if count >= 10:
            findings.append({"kind": "post_burst", "flow": list(key), "count": count})
            sample = lengths[key]
            if len(sample) >= 10 and len(set(sample)) == 2:
                low, high = sorted(set(sample))
                if high - low == 1:
                    findings.append({"kind": "length_oracle_hypothesis",
                                     "flow": list(key), "lengths": [low, high],
                                     "count": len(sample)})
    return findings


def main():
    p = argparse.ArgumentParser()
    p.add_argument("events", help="Normalized JSON Lines file")
    p.add_argument("--gateway", action="append", default=[], help="Authorized redirect sender")
    args = p.parse_args()
    from pathlib import Path
    if Path(args.events).stat().st_size > MAX_BYTES:
        p.error("event file exceeds 1 MB")
    events = []
    with open(args.events, encoding="utf-8") as stream:
        for row in stream:
            if len(row) > MAX_LINE:
                p.error("event line exceeds 4096 characters")
            if row.strip():
                events.append(json.loads(row))
            if len(events) > MAX_EVENTS:
                p.error("event file exceeds 10000 records")
    json.dump(analyze(events, set(args.gateway)), sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
