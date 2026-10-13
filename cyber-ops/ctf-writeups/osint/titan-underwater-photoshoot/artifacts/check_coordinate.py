#!/usr/bin/env python3
"""Check coordinate syntax and optional search bounds without validating a place."""

import argparse
from decimal import Decimal, InvalidOperation


def coordinate(value, limit):
    try:
        number = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid coordinate: {value}") from exc
    if not number.is_finite() or abs(number) > limit:
        raise ValueError(f"coordinate outside +/-{limit}: {value}")
    decimals = max(0, -number.as_tuple().exponent)
    if decimals > 6:
        raise ValueError("more than six decimals; recheck the pin before rounding")
    return number


def check(lat_text, lon_text, bounds=None, wrapper="scriptCTF"):
    lat = coordinate(lat_text, 90)
    lon = coordinate(lon_text, 180)
    if not wrapper.isascii() or not wrapper.isalnum():
        raise ValueError("wrapper must be ASCII letters or digits")
    in_bounds = None
    if bounds is not None:
        south, north, west, east = bounds
        if not (-90 <= south <= north <= 90 and -180 <= west <= east <= 180):
            raise ValueError("invalid bounds")
        in_bounds = south <= lat <= north and west <= lon <= east
    return {
        "flag": f"{wrapper}{{{lat:.6f}_{lon:.6f}}}",
        "in_bounds": in_bounds,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("latitude")
    parser.add_argument("longitude")
    parser.add_argument("--wrapper", default="scriptCTF")
    parser.add_argument("--bounds", nargs=4, metavar=("S", "N", "W", "E"))
    args = parser.parse_args()
    try:
        bounds = None if args.bounds is None else tuple(Decimal(x) for x in args.bounds)
        result = check(args.latitude, args.longitude, bounds, args.wrapper)
    except (ValueError, InvalidOperation) as exc:
        parser.error(str(exc))
    print(result["flag"])
    if result["in_bounds"] is False:
        print("Outside the analyst's search bound. Recheck the bound and the pin; do not discard automatically.")
    elif result["in_bounds"] is True:
        print("Inside the analyst's search bound. This does not verify the place or physical accuracy.")


if __name__ == "__main__":
    main()
