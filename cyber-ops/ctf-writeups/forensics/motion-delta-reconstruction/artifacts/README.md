# Motion telemetry review lab

These offline proofs of concept turn the motion-trail lesson into two review tasks. They contain invented fixtures only. The challenge CSV and recovered message are not in this folder.

`motion_delta_review.py` takes a UTF-8 CSV with the exact columns `time_ms,dx,dy,pen_down`. It checks a 2 MB input and 100,000-row ceiling, strict time order, finite bounded deltas, and binary pen state. By default it prints row count, active count, stroke count, numeric bounds, and median interval without showing the drawing. An analyst can opt into `--svg result.svg --axis math` or `--axis screen` to write a content-bearing vector image. Treat that SVG as sensitive. The parser reconstructs relative positions under the assumption that the rows are complete, ordered deltas in one coordinate frame. It cannot prove a device's origin, recover lost samples, or decide whether a shape is a flag.

`telemetry_sequence_hunt.py` takes normalized JSONL events with `time_ms`, `host`, `process_guid`, and `kind`. The three kinds are `input_open`, `telemetry_write` with `path`, and `network_connection` with `destination`. It produces review leads only when those events occur in order for the same host and stable process identity, with each step no more than five minutes from the prior step. The output does not establish that the network connection transferred the written file. Legitimate diagnostic software can satisfy the full sequence.

The event adapter is intentionally outside this lab. A real input-open event needs direct, authorized HID or sensor-access telemetry from an endpoint sensor or appropriate OS audit. A DLL image-load event, including `hid.dll` or `user32.dll`, cannot stand in for API use. File creation can come from Sysmon Event 11 or an EDR file event; network connection can come from Sysmon Event 3 or an EDR network event. Those events need reliable process identity and clock normalization. Destination policy, signed-client identity, approved device services, file content, and actual upload bytes remain analyst checks. Sysmon Event 7 by itself records module loading, not a device subscription.

Run the invented cases with:

```sh
python -B -m unittest test_pocs.py
python -B motion_delta_review.py fixture_motion.csv
python -B telemetry_sequence_hunt.py fixture_events.jsonl
```

The five tests cover stroke gating and both axis choices, invalid state/time/nonfinite values, a positive three-event lead, a benign two-event case, a process-identity near miss, time-order/window misses, and an expected false positive from a legitimate full sequence. They check local logic only. No SIEM backend, endpoint sensor, real upload, production false-positive rate, or original challenge acceptance was tested with these files.
