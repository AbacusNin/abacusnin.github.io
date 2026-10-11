"""Create a synthetic probe log where SSID-count rank gives a false lead."""

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path


def make(path: Path) -> None:
    if path.exists():
        raise ValueError(f"refusing to replace {path}")
    with closing(sqlite3.connect(path)) as con:
        con.execute("CREATE TABLE log (log_type INT, mac TEXT, ssid TEXT, dups INT, created_at INT, updated_at INT)")
        rows = []

        def add(mac: str, ssids: list[str], start: int, kind: int = 0) -> None:
            for i, name in enumerate(ssids):
                rows.append((kind, mac, name, 1, start + i, start + i))

        add("10:20:30:40:50:60", [f"{i:08x}" for i in range(8)], 100)
        add("20:30:40:50:60:70", ["HomeLab", "LocalCafe", "TransitHub", "OnboardNet", "WestHotel", "ReturnHub"], 200)
        add("20:30:40:50:60:70", ["LocalCafe", "ReturnHub"], 210)
        add("20:30:40:50:60:70", ["WrongRecordType"], 220, kind=1)
        add("30:40:50:60:70:80", ["CorpWiFi", "CorpWiFi"], 300)
        add("02:11:22:33:44:55", ["HomeLab", "LocalCafe", "TransitHub", "OnboardNet", "WestHotel", "ReturnHub", "Extra"], 400)
        con.executemany("INSERT INTO log VALUES (?, ?, ?, ?, ?, ?)", rows)
        con.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="new SQLite file; existing files are refused")
    args = parser.parse_args()
    try:
        make(args.output)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.error(str(error))
