"""Keep common non-public IPv4 values out of external IOC enrichment."""

import ipaddress
import sys
from pathlib import Path


MAX_BYTES = 1_000_000
MAX_LINES = 10_000
NETWORKS = (
    ("192.0.2.0/24", "documentation", "do_not_enrich"),
    ("198.51.100.0/24", "documentation", "do_not_enrich"),
    ("203.0.113.0/24", "documentation", "do_not_enrich"),
    ("198.18.0.0/15", "benchmark", "do_not_enrich"),
    ("10.0.0.0/8", "private", "local_context_only"),
    ("172.16.0.0/12", "private", "local_context_only"),
    ("192.168.0.0/16", "private", "local_context_only"),
    ("100.64.0.0/10", "shared", "local_context_only"),
    ("169.254.0.0/16", "link_local", "local_context_only"),
    ("127.0.0.0/8", "loopback", "local_context_only"),
)
RULES = tuple((ipaddress.ip_network(cidr), kind, action) for cidr, kind, action in NETWORKS)


def classify(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return "", "invalid", "check_source"
    if not isinstance(address, ipaddress.IPv4Address):
        return "", "not_ipv4", "check_source"
    for network, kind, action in RULES:
        if address in network:
            return str(address), kind, action
    return str(address), "unclassified", "review_before_enrichment"


def triage(data):
    lines = data.decode("utf-8-sig").splitlines()
    if len(lines) > MAX_LINES:
        raise ValueError(f"more than {MAX_LINES} input lines")
    rows = []
    for number, raw in enumerate(lines, 1):
        if len(raw) > 256:
            raise ValueError(f"line {number} exceeds 256 characters")
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        rows.append((number, *classify(value)))
    return rows


def main():
    if len(sys.argv) > 2:
        raise SystemExit("usage: reserved_ip_filter.py [file|-]")
    source = sys.argv[1] if len(sys.argv) == 2 else "-"
    if source == "-":
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
    else:
        with Path(source).open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"input exceeds {MAX_BYTES} bytes")
    try:
        rows = triage(data)
    except (UnicodeError, ValueError) as exc:
        raise SystemExit(f"invalid input: {exc}") from exc
    print("line\taddress\tclass\taction")
    for row in rows:
        print("\t".join(map(str, row)))


if __name__ == "__main__":
    main()
