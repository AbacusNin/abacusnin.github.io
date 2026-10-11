# Comparison-oracle lab files

The supplied `comparison_oracle_search.py` and `../fixtures/mock_oracle.py` demonstrate the challenge method on a synthetic secret. They do not connect to the kiosk. The separate `oracle_bisection_hunt.py` is a defensive proof of concept for application request logs.

## Run

From this folder:

```sh
python -B comparison_oracle_search.py
python -B ../fixtures/mock_oracle.py
python -B oracle_bisection_hunt.py oracle_events.jsonl
python -B test_oracle_bisection_hunt.py
```

The hunt's output for the included fixture should match `expected_findings.json`: one finding for `case-positive`; no findings for `case-benign` or `case-near-miss`. Use `--minimum` and `--max-gap-seconds` to change the local triage threshold. The default is five consecutive midpoint responses with no gap over 300 seconds.

## Input contract

One UTF-8 JSON object per line with `timestamp` (ISO 8601 with timezone), `actor`, `endpoint`, `candidate` (`PREFIX-XXXX`, uppercase hex), and `response` (`AFTER`, `BEFORE`, `MATCH`, or `DENY`). The script reads a local file, parses all events, groups by actor and endpoint, and sorts by time. It prints actor, endpoint, count, and first/last time for each run; it omits candidate values from findings.

Map these fields from the real application before use. The endpoint must expose its response class to the trusted logging pipeline even if unauthorized clients receive a uniform public response. Use an authenticated actor or server-side session key where possible. A shared IP can merge unrelated users. If suffixes are sensitive, restrict access, minimize retention, and keep them out of general-purpose logs; this proof of concept needs numeric candidate order to evaluate midpoint behavior.

## Scope and tuning

The detector recognizes the exact floor-midpoint strategy over a 16-bit fixed-width uppercase hex space. It starts each run at `0x7FFF`, then narrows bounds from truthful `AFTER` and `BEFORE` events. Other midpoint conventions, unknown starting windows, multiple target secrets, changed collation, omitted events, or interleaved sessions may evade it. A legitimate binary-search feature or a test harness can produce the same pattern. Triage the endpoint's intended behavior and actor context before alerting an incident team.

The fixture is synthetic. Local execution checks code behavior only. No SIEM backend conversion, production sensor, precision/recall study, or live response-channel test has been performed. The primary remediation is to remove ordering information from unauthorized responses and enforce record-level authorization. The hunt is a way to look for prior use while that fix is planned.
