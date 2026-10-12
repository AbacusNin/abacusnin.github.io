# CAT048 track-integrity lab

These are offline defensive proofs of concept. The CAT048 subset tool makes and decodes a fixed `FD D2` field layout. The hunt checks normalized ingest events against a protected-track registry. Every published identifier and event is invented. Neither tool connects to a radar, sends a packet, or opens a network socket.

## Files and commands

- [`cat048_subset.py`](cat048_subset.py): bounded standard-library builder and decoder for one observed CAT048 layout.
- [`track_integrity_check.py`](track_integrity_check.py): protected-track check over normalized JSONL events.
- [`test_cat048_lab.py`](test_cat048_lab.py): positive, benign, near-miss, missing-provenance, and malformed-input checks.
- [`../fixtures/benign_cat048.hex`](../fixtures/benign_cat048.hex) and [`../fixtures/forged_example.hex`](../fixtures/forged_example.hex): invented 32-byte blocks with one 29-byte record each.
- [`../fixtures/protected_registry.json`](../fixtures/protected_registry.json), [`../fixtures/ingest_events.jsonl`](../fixtures/ingest_events.jsonl), and [`../fixtures/expected_findings.json`](../fixtures/expected_findings.json): invented registry, events, and expected output.

From this folder, with Python 3.8 or newer:

```sh
python -B cat048_subset.py
python -B track_integrity_check.py ../fixtures/protected_registry.json ../fixtures/ingest_events.jsonl
python -B -m unittest -v test_cat048_lab.py
```

The first command prints the decoded synthetic block. The hunt reports one protected-track event with unexpected peer, mismatched aircraft address, and suspicious classification. A second protected event has no authenticated peer and produces a provenance-gap finding. The ordinary authorized event and a same-track-number event under a different SAC/SIC tuple produce no finding. This validates local logic on four invented events. It does not measure live detection quality.

## Input, output, and required data

`cat048_subset.py --decode PATH` reads one local binary capture up to 1 MiB. It requires Category 048, exact block lengths, a 29-byte record, `FD D2` FSPEC, a two-octet target report descriptor, and a one-octet track status. It rejects other UAP layouts and malformed lengths. `build_record` accepts SAC, SIC, track number, Mode-S address, Mode-3/A code, callsign, and SPI. It uses invented values for time, position, and flight level. It is a subset model, not a full EUROCONTROL CAT048 implementation or a service-acceptance test.

The hunt requires two local files no larger than 1 MiB each. The registry JSON contains `protected_tracks`, each with `sac`, `sic`, `track_number`, `expected_mode_s`, and nonempty `allowed_peers`. Each JSONL event contains `event_id`, the same tuple, `mode_s`, `classification`, and an `authenticated_peer` string or null. The tool checks at most 10,000 events and emits JSON findings. An event's `authenticated_peer` must be assigned by a trusted channel or gateway. A value copied from the ASTERIX payload or supplied by an unauthenticated client defeats that check. The classifier names in the sample are local application examples, not CAT048 standard fields.

## Review and tuning

Deploying this idea would require a current protected-track registry, per-source authenticated transport, raw pre-merge records, decision logs, synchronized event times, and a documented maintenance/test window. Compare the raw plot, its authenticated source, the merge decision, and the committed state during triage. A genuine address change, multi-sensor handoff, test replay, or stale registry may create a finding. A same-number plot from a different SAC/SIC tuple is not the same protected track in this model. Missing provenance is a visibility failure, not proof of spoofing.

The local tests do not execute a real ingest, convert a Sigma rule, query a SIEM, prove platform acceptance, or validate a production detection rate. The challenge sample contained four 177-byte blocks with six 29-byte records each. Its binary records carried no TCP peer identity or post-merge state, so the hunt uses invented normalized events.
