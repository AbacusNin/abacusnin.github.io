"""Create synthetic protocol audit events for the oracle-hunt proof of concept."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path


def make_event(second, token, epoch, result="INVALID"):
    stamp = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=second)
    return {
        "TimeGenerated": stamp.isoformat().replace("+00:00", "Z"),
        "EventType": "VerifyResult",
        "Result": result,
        "TokenHash": token,
        "SrcEntity": "client-a",
        "DstEntity": "verifier-a",
        "RotationEpoch": epoch,
    }


def events():
    rows = []
    # Positive: 20 failures, five epochs, within 10 minutes.
    rows.extend(make_event(10 + i * 20, "synthetic-oracle-token", i % 5) for i in range(20))
    rows.append(make_event(400, "synthetic-oracle-token", 4, "VALID"))
    # Benign control: retry/desynchronization burst in one epoch.
    rows.extend(make_event(20 + i * 20, "synthetic-stale-client", 2) for i in range(20))
    # Near miss: five epochs, only 19 failures in any ten-minute window.
    rows.extend(make_event(30 + i * 20, "synthetic-short-burst", i % 5) for i in range(19))
    rows.append(make_event(1100, "synthetic-short-burst", 4))
    rows.append({"TimeGenerated": "2026-01-01T00:00:00Z", "EventType": "KeyRotationSent"})
    return sorted(rows, key=lambda row: row["TimeGenerated"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8", newline="\n") as handle:
        for row in events():
            handle.write(json.dumps(row, separators=(",", ":")) + "\n")
    print(f"wrote {len(events())} synthetic events to {args.output}")


if __name__ == "__main__":
    main()
