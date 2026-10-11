"""Rank universally administered probe senders for human PNL review."""

import argparse
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path


IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def column(name: str) -> str:
    if not IDENTIFIER.fullmatch(name):
        raise ValueError(f"invalid SQL identifier: {name!r}")
    return f'"{name}"'


def address_class(mac: str) -> str:
    if not isinstance(mac, str):
        return "invalid"
    parts = mac.split(":")
    if len(parts) != 6 or any(len(part) != 2 or not re.fullmatch(r"[0-9A-Fa-f]{2}", part) for part in parts):
        return "invalid"
    first = int(parts[0], 16)
    if first & 1:
        return "group_address"
    return "locally_administered" if first & 2 else "universally_administered"


def triage(db: Path, table: str, mac: str, ssid: str, time: str, kind: str, probe_type: int, top: int, max_ssids: int) -> dict:
    if not db.is_file():
        raise ValueError(f"capture not found: {db}")
    if not 1 <= top <= 50:
        raise ValueError("--top must be between 1 and 50")
    if not 1 <= max_ssids <= 1000:
        raise ValueError("--max-ssids must be between 1 and 1000")

    table, mac, ssid = map(column, (table, mac, ssid))
    order = f"{column(time)}, rowid" if time else "rowid"
    kind = column(kind) if kind else ""
    where = f"WHERE {kind} = ?" if kind else ""
    params = (probe_type,) if kind else ()

    uri = db.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as con:
        con.execute("PRAGMA query_only = ON")
        rows = con.execute(
            f"SELECT {mac}, COUNT(DISTINCT CASE WHEN {ssid} <> '' THEN {ssid} END), COUNT(*) "
            f"FROM {table} {where} GROUP BY {mac}",
            params,
        )
        counts = {key: 0 for key in ("universally_administered", "locally_administered", "group_address", "invalid")}
        ranked = []
        for source, distinct, probes in rows:
            category = address_class(source)
            counts[category] += 1
            if category == "universally_administered":
                ranked.append((source, distinct, probes))
        ranked.sort(key=lambda row: (-row[1], -row[2], row[0]))

        candidates = []
        for source, distinct, probes in ranked[:top]:
            filter_sql = f" AND {kind} = ?" if kind else ""
            values = (source, probe_type) if kind else (source,)
            names = con.execute(
                f"SELECT {ssid} FROM {table} WHERE {mac} = ?{filter_sql} "
                f"AND {ssid} <> '' ORDER BY {order}",
                values,
            )
            seen = set()
            ordered = []
            for (name,) in names:
                if name not in seen:
                    seen.add(name)
                    ordered.append(name)
                    if len(ordered) == max_ssids:
                        break
            candidates.append({
                "mac": source,
                "distinct_ssids": distinct,
                "probe_rows": probes,
                "observed_ssids": ordered,
                "truncated": len(ordered) < distinct,
            })

    return {"address_counts": counts, "candidates": candidates}


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only triage of directed probe names in a SQLite capture")
    parser.add_argument("db", type=Path)
    parser.add_argument("--table", default="log")
    parser.add_argument("--mac-col", default="mac")
    parser.add_argument("--ssid-col", default="ssid")
    parser.add_argument("--time-col", default="created_at", help="blank uses rowid")
    parser.add_argument("--type-col", default="log_type", help="blank disables probe-type filtering")
    parser.add_argument("--probe-type", type=int, default=0)
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--max-ssids", type=int, default=100)
    args = parser.parse_args()
    try:
        result = triage(args.db, args.table, args.mac_col, args.ssid_col, args.time_col, args.type_col, args.probe_type, args.top, args.max_ssids)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
