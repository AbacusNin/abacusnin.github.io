"""Flag game-port flows from assets without an approved game-use exception."""

import argparse
import ipaddress
import json
from datetime import datetime
from pathlib import Path


MAX_BYTES = 10_000_000
MAX_LINES = 50_000
DEFAULT_PORT = 25565


def evaluate(rows, port=DEFAULT_PORT):
    if not 1 <= port <= 65535:
        raise ValueError("invalid port")
    findings = []
    for index, row in enumerate(rows, 1):
        if index > MAX_LINES:
            raise ValueError("too many events")
        timestamp = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("timestamp needs a timezone")
        src = str(ipaddress.ip_address(row["src_ip"]))
        dst = str(ipaddress.ip_address(row["dst_ip"]))
        dst_port = int(row["dst_port"])
        if type(row["approved_game_use"]) is not bool:
            raise ValueError("approved_game_use must be a boolean from asset policy")
        verified = row.get("game_handshake_verified")
        if verified is not None and type(verified) is not bool:
            raise ValueError("game_handshake_verified must be true, false, or absent")
        if (row["protocol"].lower() != "tcp" or row["action"].lower() != "allow"
                or dst_port != port or row["approved_game_use"]):
            continue
        findings.append({"ts": timestamp.isoformat(), "src_ip": src, "dst_ip": dst,
                         "dst_port": dst_port, "asset_role": str(row["asset_role"]),
                         "handshake": "verified" if verified is True else "unverified",
                         "disposition": "review_egress_policy_and_protocol"})
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path, help="normalized JSONL network flows")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    with args.events.open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit("input too large")
    rows = [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
    print(json.dumps({"findings": evaluate(rows, args.port)}, indent=2))


if __name__ == "__main__":
    main()
