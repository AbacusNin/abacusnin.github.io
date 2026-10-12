"""Offline camera-path geometry review with optional H3 cell grouping.

The input is an analyst-approved local JSON file. No map or web requests occur.
"""

import argparse
import json
import math
from pathlib import Path

RADIUS_M = 6_371_000.0


def latlon(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("coordinate must be [latitude, longitude]")
    lat, lon = (float(v) for v in value)
    if not all(math.isfinite(v) for v in (lat, lon)) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("coordinate is outside the geographic range")
    return lat, lon


def bearing_deg(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    delta = lon2 - lon1
    y = math.sin(delta) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def distance_m(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    term = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * RADIUS_M * math.asin(min(1.0, math.sqrt(term)))


def angular_delta(bearing, heading):
    """Signed subject position relative to heading: negative is left."""
    return (bearing - heading + 180) % 360 - 180


def evaluate(config, cell_mapper=None):
    start, end, subject = (latlon(config[key]) for key in ("path_start", "path_end", "subject"))
    if abs(start[1] - end[1]) > 180:
        raise ValueError("antimeridian-crossing paths are outside scope")
    heading = float(config["heading_deg"])
    lo, hi = (float(v) for v in config["subject_offset_window_deg"])
    step = float(config.get("step_m", 2.0))
    resolution = int(config.get("h3_resolution", 11))
    aux_lo, aux_hi = (float(v) for v in config.get("aux_path_fraction_window", [0.0, 1.0]))
    if not all(math.isfinite(v) for v in (heading, lo, hi, step, aux_lo, aux_hi)):
        raise ValueError("all numeric inputs must be finite")
    if not (0 <= heading < 360 and -180 <= lo <= hi <= 180 and step > 0 and step <= 1000):
        raise ValueError("invalid heading, angle window, or sampling step")
    if not (0 <= aux_lo <= aux_hi <= 1) or not (0 <= resolution <= 15):
        raise ValueError("invalid auxiliary interval or H3 resolution")
    length = distance_m(start, end)
    if not (0 < length <= 100_000):
        raise ValueError("path length must be over zero and at most 100 km")
    count = math.ceil(length / step)
    if count > 50_000:
        raise ValueError("sampling would exceed 50,000 points")
    rows = []
    for i in range(count + 1):
        fraction = i / count
        point = (start[0] + fraction * (end[0] - start[0]),
                 start[1] + fraction * (end[1] - start[1]))
        angle = angular_delta(bearing_deg(point, subject), heading)
        if lo <= angle <= hi and aux_lo <= fraction <= aux_hi:
            row = {"fraction": round(fraction, 6), "path_offset_m": round(length * fraction, 2),
                   "subject_offset_deg": round(angle, 3),
                   "distance_to_subject_m": round(distance_m(point, subject), 2)}
            if cell_mapper is not None:
                row["h3_cell"] = cell_mapper(*point, resolution)
            rows.append(row)
    cells = list(dict.fromkeys(row["h3_cell"] for row in rows)) if cell_mapper else []
    return {"sampled_points": count + 1, "matching_points": len(rows),
            "candidate_cells": cells, "matches": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    if args.config.stat().st_size > 64_000:
        parser.error("configuration exceeds 64 KB")
    config = json.loads(args.config.read_text(encoding="utf-8"))
    try:
        import h3
    except ImportError:
        parser.error("install h3>=4,<5 to obtain and validate cell IDs")
    result = evaluate(config, h3.latlng_to_cell)
    # Keep the default report compact and avoid publishing precise sample points.
    print(json.dumps({key: result[key] for key in ("sampled_points", "matching_points", "candidate_cells")}, indent=2))


if __name__ == "__main__":
    main()
