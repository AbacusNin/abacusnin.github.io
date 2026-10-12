# PRNG state and session-sequence lab

This folder contains a challenge client and a separate defensive review aid. The client is for an authorized copy of the word-grouping challenge. The log reviewer uses invented application events to make a detection hypothesis testable. Neither file contains a flag, live target address, production telemetry, or the challenge word database.

| File | Purpose |
|---|---|
| [challenge_solver.py](challenge_solver.py) | Reproduce Java `Random` shuffles, recover the 16 unknown state bits, and group displayed tokens by their original positions. Requires the challenge's `Connections_Data.json` and an authorized service. |
| [session_sequence.py](session_sequence.py) | Find a state-read operation followed by four submissions within five seconds in the same source/session. |
| [fixtures/events.jsonl](fixtures/events.jsonl) | Invented case-like, benign fast-client, and delayed near-miss sessions. |
| [test_lab.py](test_lab.py) | Synthetic state-recovery and sequence checks. |

Run the local checks from this folder with Python 3.10 or later:

```sh
python -m unittest -v test_lab.py
python session_sequence.py fixtures/events.jsonl
```

The expected reviewer output contains `case` and `fast-client`. The second is deliberately benign and demonstrates that speed plus a state read needs context. The `near-miss` session has four submissions six seconds after the read and stays clear. The reviewer expects one JSON object per line with `ts` (ISO 8601 with timezone), `session_id`, `source_ip`, and `operation`. It accepts at most 2 MB and 20,000 lines. It reports source and session identifiers but no payload values. In a real environment, map log fields first and decide how session IDs are scoped and retained. A reverse proxy log without application operation names cannot support this test.

To use the challenge client in an authorized environment, provide the service host, port, and a local copy of the challenge's database:

```sh
python challenge_solver.py <host> <port> <path/to/Connections_Data.json>
```

The solver was reconstructed from the challenge account and checked with a synthetic PRNG fixture and a ten-round in-memory protocol simulation that includes hashed boards. The published copy fills the multiplier constant from the Java source. A Java compiler and reachable live service were unavailable during this page review, so this copy was not exercised end to end against the original server. The account reports 80 successful local replica runs for its solver; that reported result should not be read as a fresh validation of the published copy or as live acceptance.

For white-box reviews of another service, list every client-callable operation and its return values. Track state creation, state advancement, and all downstream uses. Check the data order before and after hashing or encryption. Read the validator's precise comparison logic, including duplicate behavior. Then test predicted state against an observed output before claiming that it can predict future values. Keep any reproduction inside an authorized test service.

The session reviewer is a triage proof of concept. It has no backend query conversion, production baseline, false-positive rate, or incident validation. The SPL and KQL templates in the article require environment-specific field mapping and live validation.
