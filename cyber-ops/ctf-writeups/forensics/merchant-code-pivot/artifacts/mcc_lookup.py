"""Search a small, cited MCC reference excerpt; it is not a full code catalog."""

import argparse
import csv
from pathlib import Path

REFERENCE = Path(__file__).with_name("mcc_reference.csv")


def lookup(query):
    with REFERENCE.open(encoding="utf-8", newline="") as handle:
        entries = list(csv.DictReader(handle))
    term = query.casefold()
    return [row for row in entries if term in row["mcc"] or term in row["description"].casefold()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="four-digit code or category text")
    args = parser.parse_args()
    matches = lookup(args.query)
    for row in matches:
        print(f'{row["mcc"]}: {row["description"]} ({row["reference_note"]})')
    if not matches:
        print("No entry in this limited reference excerpt")


if __name__ == "__main__":
    main()
