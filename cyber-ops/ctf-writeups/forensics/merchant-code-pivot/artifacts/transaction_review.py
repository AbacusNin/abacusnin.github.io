"""Offline review of a bounded transaction CSV with explicit MCC pivots."""

import argparse
import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_BYTES = 10_000_000
MAX_ROWS = 100_000
REQUIRED = {"timestamp", "merchant", "mcc", "amount"}


def load_rows(path: Path):
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("CSV missing or larger than 10 MB")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return parse_rows(handle)


def parse_rows(handle):
    rows = []
    reader = csv.DictReader(handle)
    if not reader.fieldnames or not REQUIRED <= set(reader.fieldnames):
        raise ValueError("required columns: timestamp, merchant, mcc, amount")
    for index, row in enumerate(reader, 1):
        if index > MAX_ROWS:
            raise ValueError("more than 100,000 rows")
        try:
            code = row["mcc"].strip()
            amount = Decimal(row["amount"].strip())
            if len(code) != 4 or not code.isdigit() or not amount.is_finite() or amount < 0:
                raise ValueError
        except (AttributeError, InvalidOperation, ValueError):
            raise ValueError(f"invalid MCC or amount on data row {index}") from None
        rows.append({"timestamp": row["timestamp"], "merchant": row["merchant"],
                     "mcc": code, "amount": amount})
    return rows


def review(rows, entity_mcc, category_mcc, spend_mcc, threshold, name_hint=""):
    counts = Counter(row["mcc"] for row in rows)
    category_names = sorted({row["merchant"] for row in rows if row["mcc"] == category_mcc})
    spend = sum((row["amount"] for row in rows if row["mcc"] == spend_mcc), Decimal("0"))
    name_hits = sum(name_hint.casefold() in row["merchant"].casefold() for row in rows) if name_hint else None
    return {
        "rows": len(rows),
        "q1_entity_code_count": counts[entity_mcc],
        "q1_name_hits": name_hits,
        "q2_category_merchants": category_names,
        "q2_unique_merchant": category_names[0] if len(category_names) == 1 else None,
        "q3_dominant_codes": sorted(code for code, n in counts.items() if n == max(counts.values(), default=0)),
        "q4_spend_total": str(spend.quantize(Decimal("0.01"))),
        "q5_above_threshold_count": sum(row["amount"] > threshold for row in rows),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--entity-mcc", required=True)
    parser.add_argument("--category-mcc", required=True)
    parser.add_argument("--spend-mcc", required=True)
    parser.add_argument("--threshold", type=Decimal, required=True)
    parser.add_argument("--name-hint", default="")
    args = parser.parse_args()
    for code in (args.entity_mcc, args.category_mcc, args.spend_mcc):
        if len(code) != 4 or not code.isdigit():
            parser.error("MCC arguments must be four digits")
    if not args.threshold.is_finite() or args.threshold < 0:
        parser.error("threshold must be a finite nonnegative number")
    try:
        result = review(load_rows(args.csv_file), args.entity_mcc, args.category_mcc,
                        args.spend_mcc, args.threshold, args.name_hint)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
