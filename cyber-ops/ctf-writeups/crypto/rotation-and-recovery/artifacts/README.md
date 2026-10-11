# Protocol verification oracle hunt: defensive proof of concept

This local lab turns the article's verification-oracle hunting idea into a reproducible check over normalized application audit events. It is an operational extrapolation from the CTF behavior. The challenge's protocol traffic and server logs are not included, and this tool has not been run against a production sensor.

## Files

- `protocol_oracle_hunt.py`: bounded JSONL reader and ten-minute sliding-window correlator.
- `make_fixture.py`: deterministic synthetic event generator. It refuses to overwrite an existing output.
- `fixture_events.jsonl`: 62 generated events with one positive, a one-epoch retry burst, a 19-failure near miss, one late failure, a valid result, and an unrelated rotation event.
- `expected_findings.json`: expected output for the included fixture.
- `test_protocol_oracle_hunt.py`: positive, benign, near-miss, timestamp, and sliding-window boundary checks.

## Run and result

```sh
python protocol_oracle_hunt.py fixture_events.jsonl > observed.json
python -m json.tool observed.json
```

The expected result is one finding for `synthetic-oracle-token`: 20 invalid verifications across five epochs from 00:00:10 through 00:06:30 UTC. The one-epoch stale-client burst and 19-failure near miss remain clear. A later twentieth near-miss event falls outside the ten-minute window. To rebuild the fixture at a new path, run `python make_fixture.py new_fixture.jsonl`.

Run `python -m unittest test_protocol_oracle_hunt.py` to compare actual output with `expected_findings.json` and exercise the benign and near-miss cases independently.

## Required telemetry and mapping

Input is UTF-8 JSON Lines. `EventType=VerifyResult` records require `TimeGenerated` (timezone-aware ISO 8601), `Result` (`VALID` or `INVALID`), `TokenHash` (a stable nonsecret token identifier), `SrcEntity`, `DstEntity`, and nonnegative integer `RotationEpoch`. An unrelated event type is ignored. Hash/token identifiers must be stable across epochs, and the source and destination should be normalized to the same direction. Preserve a separate audit trail for ingestion errors. The tool caps input at 10 MB and 100,000 lines, rejects malformed relevant events, and emits JSON to standard output.

## Scope, tuning, and limits

The rule reports one lead per token/source/destination when at least 20 invalid verifications span at least five epochs in any trailing ten minutes. Both thresholds come from the article's illustrative KQL/SPL, not a measured baseline. Choose thresholds from normal traffic and approved test windows; delayed delivery, client version skew, protocol migration, and load testing can resemble probing. A real deployment needs reliable clock synchronization, stable token identifiers, retention, access controls, and incident triage. This code does not detect network mutation directly, correlate ACK suppression, prove an attacker held an adversary-in-the-middle position, or establish key recovery. The local fixture check proves only that this logic distinguishes its three designed cases; it says nothing about production precision, recall, or SIEM backend conversion.
