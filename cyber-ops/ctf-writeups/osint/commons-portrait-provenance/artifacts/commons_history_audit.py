#!/usr/bin/env python3
"""Review a saved Commons imageinfo response for the oldest visible upload."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

MAX_BYTES = 1_000_000


def review(doc: dict) -> dict:
    if not isinstance(doc, dict) or "error" in doc:
        raise ValueError("API error or invalid response")
    if "continue" in doc or "query-continue" in doc:
        raise ValueError("upload history is incomplete; fetch continuation pages")
    query = doc.get("query")
    pages = query.get("pages") if isinstance(query, dict) else None
    if not isinstance(pages, dict) or len(pages) != 1:
        raise ValueError("expected one file page in query.pages")
    page = next(iter(pages.values()))
    if not isinstance(page, dict) or page.get("missing") is not None:
        raise ValueError("file page is missing")
    title = page.get("title")
    if not isinstance(title, str) or not title.startswith("File:"):
        raise ValueError("expected a File: page title")
    if page.get("imagerepository") not in (None, "local"):
        raise ValueError("file history belongs to another repository")
    entries = page.get("imageinfo")
    if not isinstance(entries, list) or not entries:
        raise ValueError("no upload versions returned")
    versions = []
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("timestamp"), str):
            raise ValueError("upload version lacks a timestamp")
        try:
            moment = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid upload timestamp") from exc
        if moment.tzinfo is None or moment.utcoffset() != timezone.utc.utcoffset(moment):
            raise ValueError("upload timestamp must be UTC")
        user = item.get("user")
        hidden = "userhidden" in item
        if user is not None and not isinstance(user, str):
            raise ValueError("invalid uploader field")
        versions.append((moment, user, hidden))
    versions.sort(key=lambda entry: entry[0])
    first_time = versions[0][0]
    earliest = [entry for entry in versions if entry[0] == first_time]
    unresolved = len(earliest) != 1 or earliest[0][2] or not earliest[0][1]
    return {
        "file": title,
        "visible_versions": len(versions),
        "oldest_visible_timestamp": first_time.isoformat().replace("+00:00", "Z"),
        "oldest_visible_account": None if unresolved else earliest[0][1],
        "status": "unresolved" if unresolved else "account_found",
        "scope": "account on oldest visible version of this file name; identity and earlier transfers unverified",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response", type=Path, help="saved Commons action=query, prop=imageinfo JSON")
    args = parser.parse_args()
    try:
        if args.response.is_symlink() or args.response.stat().st_size > MAX_BYTES:
            raise ValueError("response must be a regular file no larger than 1 MB")
        result = review(json.loads(args.response.read_text(encoding="utf-8")))
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "account_found" else 1
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"review failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
