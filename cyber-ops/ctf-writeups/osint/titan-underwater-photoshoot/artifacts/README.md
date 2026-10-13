# Titan coordinate review files

The GeoJSON records the case's accepted CTF point. It is a map-pin coordinate, with no claim about where the dive team or boat physically stood. The original pin URL and platform submission receipt were not available for an independent replay.

`check_coordinate.py` is a local, standard-library candidate check. It accepts latitude and longitude as decimal strings, enforces valid ranges and no more than six fractional digits, pads to six places, and assembles the challenge wrapper. Optional bounds are analyst estimates. A miss prints a warning and still returns the candidate. It never queries a map or submits a flag.

```sh
python check_coordinate.py 7.513015 98.323308 --bounds 7.39 7.52 98.25 98.35
python test_coordinate.py
```

The tests cover the recorded point, a just-outside-bound candidate, a southern-hemisphere near miss, swapped coordinates, excessive precision, and nonfinite input. `source_review_template.md` is a reusable provenance form for comparing an event record with a coordinate source. Its blanks are intentional; no new real-world source is fabricated.

For actual use, save the map pin's direct URL or a permitted capture, record its datum and timestamp, and check the event venue separately. This check has no evidence of positional accuracy, platform acceptance, or production performance beyond the local synthetic tests.
