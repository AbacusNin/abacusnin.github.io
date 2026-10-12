"""Local proof of concept for triaging process creation JSONL. No execution or network I/O."""

import base64
import json
import re
import sys
from pathlib import Path
from typing import Iterator

ENC_ARG = re.compile(r"(?i)(?:^|\s)-(?:e|enc|encodedcommand)\s+([A-Za-z0-9+/]+={0,2})(?=\s|$)")
MAX_LINE = 32768


def inspect(event: dict) -> dict | None:
    image = str(event.get("image", "")).replace("/", "\\").lower().rsplit("\\", 1)[-1]
    command = str(event.get("command_line", ""))
    if image not in {"powershell.exe", "pwsh.exe"} or len(command) > 8192:
        return None
    match = ENC_ARG.search(command)
    if not match:
        return None
    token = match.group(1)
    if len(token) > 4096 or len(token) % 4:
        return None
    try:
        raw = base64.b64decode(token, validate=True)
        decoded = raw.decode("utf-16le")
    except (ValueError, UnicodeError):
        return None
    # Avoid exporting the command or decoded text as an alert field.
    return {
        "event_id": event.get("event_id"),
        "image": image,
        "encoded_command": True,
        "decoded_chars": len(decoded),
        "review_required": True,
    }


def scan(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            if len(line) > MAX_LINE:
                raise ValueError(f"line {number} exceeds size limit")
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError(f"line {number} is not an object")
            result = inspect(event)
            if result:
                yield result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python process_hunt.py process-events.jsonl")
    for item in scan(Path(sys.argv[1])):
        print(json.dumps(item, sort_keys=True))
