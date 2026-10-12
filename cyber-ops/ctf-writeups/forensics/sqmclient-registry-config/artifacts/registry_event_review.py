"""Group normalized registry-value writes by host for SQMClient case review."""

import argparse
import json
from pathlib import Path


MAX_BYTES = 2 * 1024 * 1024
MAX_EVENTS = 20_000
PATTERN = {
    "software\\microsoft\\sqmclient": {"token", "configpath", "cachemap", "sessionmap"},
    "software\\microsoft\\wbem": {"sessionid"},
    "software\\classes\\installer": {"upload"},
}


def classify(target):
    parts = target.replace("/", "\\").casefold().split("\\")
    if len(parts) < 4 or parts[0] not in {"hklm", "hkey_local_machine"}:
        return None
    key, name = "\\".join(parts[1:-1]), parts[-1]
    return (key, name) if name in PATTERN.get(key, set()) else None


def review(path):
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Input must be a local JSONL file of at most 2 MiB")
    hosts = {}
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line_number > MAX_EVENTS:
                raise ValueError("Input has more than 20,000 events")
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError(f"Line {line_number} is not an event object")
            if event.get("event_id") != 13:
                continue
            match = classify(str(event.get("target_object", "")))
            if not match:
                continue
            host = str(event.get("host", ""))
            if not host:
                raise ValueError(f"Line {line_number} has no host")
            matched = hosts.setdefault(host, {key: set() for key in PATTERN})
            matched[match[0]].add(match[1])

    reports = []
    for host, matched in sorted(hosts.items()):
        reports.append({
            "host": host,
            "complete_case_pattern": all(names <= matched[key] for key, names in PATTERN.items()),
            "matched_value_names": {key: sorted(names) for key, names in matched.items() if names},
        })
    return {
        "hosts": reports,
        "meaning": "Value-name lead only. Missing writes do not exclude old state; a hit needs baseline and process review.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, help="Normalized registry write events")
    args = parser.parse_args()
    try:
        print(json.dumps(review(args.jsonl), indent=2))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Cannot review events: {exc}\n")


if __name__ == "__main__":
    main()
