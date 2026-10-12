"""Find repeated, similarly sized POSTs in normalized endpoint HTTP events."""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

MAX_INPUT = 1024 * 1024


def parse_time(value):
    moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("time requires a timezone")
    return moment.astimezone(timezone.utc)


def hunt(events, threshold=3, window_seconds=60, size_tolerance=16):
    groups = defaultdict(list)
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("each event must be an object")
        if event.get("method") != "POST" or event.get("approved_service") is True:
            continue
        host, destination, path = (event.get(name) for name in ("host", "destination", "path"))
        if not all(isinstance(item, str) and item for item in (host, destination, path)):
            raise ValueError("POST needs host, destination, and path")
        size = event.get("body_bytes")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0 or size > 256_000:
            raise ValueError("body_bytes outside 0..256000")
        groups[(host, destination, path)].append((parse_time(event["time"]), size))
    findings = []
    for (host, destination, path), rows in groups.items():
        rows.sort()
        for i, (start, _) in enumerate(rows):
            window = [size for timestamp, size in rows[i:] if timestamp - start <= timedelta(seconds=window_seconds)]
            sizes = sorted(window)
            matched = False
            for left in range(len(sizes) - threshold + 1):
                right = left + threshold - 1
                if sizes[right] - sizes[left] <= size_tolerance:
                    while right + 1 < len(sizes) and sizes[right + 1] - sizes[left] <= size_tolerance:
                        right += 1
                    cluster = sizes[left:right + 1]
                    findings.append({"host": host, "destination": destination, "path": path,
                                     "start": start.isoformat(), "post_count": len(cluster),
                                     "min_bytes": cluster[0], "max_bytes": cluster[-1]})
                    matched = True
                    break
            if matched:
                break
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", help="normalized JSONL, at most 1 MiB")
    parser.add_argument("--threshold", type=int, default=3)
    args = parser.parse_args()
    try:
        if not 2 <= args.threshold <= 10_000:
            raise ValueError("threshold outside 2..10000")
        source = Path(args.events)
        if source.stat().st_size > MAX_INPUT:
            raise ValueError("input exceeds 1 MiB")
        events = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
        print(json.dumps({"findings": hunt(events, args.threshold)}, indent=2))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"hunt failed: {exc}\n")


if __name__ == "__main__":
    main()
