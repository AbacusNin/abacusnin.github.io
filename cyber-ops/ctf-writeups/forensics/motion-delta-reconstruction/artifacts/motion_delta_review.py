"""Review bounded relative-motion CSVs without printing recovered content."""

import argparse
import csv
import io
import json
import math
from pathlib import Path


MAX_BYTES = 2_000_000
MAX_ROWS = 100_000
HEADER = ["time_ms", "dx", "dy", "pen_down"]


def review(path: Path):
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("CSV exceeds the 2 MB review limit")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if reader.fieldnames != HEADER:
        raise ValueError("expected time_ms,dx,dy,pen_down columns")

    x = y = 0.0
    prev = (x, y)
    last_time = None
    points = [prev]
    segments = []
    active = []
    pen_rows = 0
    intervals = []
    for index, row in enumerate(reader, 1):
        if index > MAX_ROWS:
            raise ValueError("CSV exceeds the row limit")
        if None in row or any(row[key] is None for key in HEADER):
            raise ValueError(f"row {index}: malformed column count")
        try:
            time_ms = int(row["time_ms"])
            dx = float(row["dx"])
            dy = float(row["dy"])
            state = int(row["pen_down"])
        except ValueError as exc:
            raise ValueError(f"row {index}: invalid numeric value") from exc
        if state not in (0, 1) or not all(math.isfinite(v) for v in (dx, dy)):
            raise ValueError(f"row {index}: nonfinite delta or invalid pen state")
        if max(abs(dx), abs(dy)) > 1_000_000:
            raise ValueError(f"row {index}: delta exceeds review bound")
        if last_time is not None:
            if time_ms <= last_time:
                raise ValueError(f"row {index}: time is not increasing")
            intervals.append(time_ms - last_time)
        last_time = time_ms
        x += dx
        y += dy
        current = (x, y)
        if state:
            pen_rows += 1
            if not active:
                active = [prev, current]
            else:
                active.append(current)
        elif active:
            segments.append(active)
            active = []
        points.append(current)
        prev = current
    if active:
        segments.append(active)
    if len(points) == 1:
        raise ValueError("CSV has no data rows")

    summary = {
        "rows": len(points) - 1,
        "pen_down_rows": pen_rows,
        "stroke_segments": len(segments),
        "x_range": [round(min(p[0] for p in points), 3), round(max(p[0] for p in points), 3)],
        "y_range": [round(min(p[1] for p in points), 3), round(max(p[1] for p in points), 3)],
        "median_interval_ms": sorted(intervals)[len(intervals) // 2] if intervals else None,
    }
    return summary, segments


def svg(segments, axis="math"):
    if not segments:
        raise ValueError("no active strokes to render")
    xs = [x for segment in segments for x, _ in segment]
    ys = [y for segment in segments for _, y in segment]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    width = max(1.0, xmax - xmin)
    height = max(1.0, ymax - ymin)
    paths = []
    for segment in segments:
        coords = []
        for x, y in segment:
            mapped_y = ymax - y if axis == "math" else y - ymin
            coords.append(f"{x - xmin:.3f},{mapped_y:.3f}")
        paths.append(f'<polyline points="{" ".join(coords)}" />')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 {width + 2:.3f} {height + 2:.3f}">'
            '<g fill="none" stroke="black" stroke-width="0.25" stroke-linecap="round" stroke-linejoin="round">'
            + "".join(paths) + "</g></svg>\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--svg", type=Path, help="explicitly write content-bearing stroke image")
    parser.add_argument("--axis", choices=("math", "screen"), default="math")
    args = parser.parse_args()
    summary, segments = review(args.csv)
    print(json.dumps(summary, indent=2))
    if args.svg:
        args.svg.write_text(svg(segments, args.axis), encoding="utf-8")


if __name__ == "__main__":
    main()
