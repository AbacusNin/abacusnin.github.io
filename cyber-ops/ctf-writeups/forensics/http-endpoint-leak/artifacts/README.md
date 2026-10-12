# HTTP endpoint discovery lab

These files turn one CTF observation into offline triage and a candidate web-log detection. They are defensive proofs of concept. They do not retrieve a secret or make an authorization decision.

## Capture triage

`http_capture_triage.py` accepts one Ethernet, IPv4/TCP, cleartext-HTTP classic pcap and prints JSON: request/response counts, response codes, Content-Length values, numeric path families, and any `200` request match. Example:

```sh
python -B artifacts/http_capture_triage.py fixtures/sample_http.pcap
```

Compare with [`expected_capture.json`](../fixtures/expected_capture.json). The program reads at most 32 MB and 200,000 frames. It inspects HTTP start lines present in individual packets. It does **not** reassemble TCP, decode TLS/HTTP2, verify checksums, follow redirects, or prove a response body is absent when transfer coding is used. A `declared_empty` result means the parsed response has `Content-Length: 0`, no `Transfer-Encoding`, and no body bytes in that packet. Review the stream with a full dissector before asserting complete payload absence in a new case. URI output can be sensitive; handle reports accordingly.

## Web-log detection

`web_enum_detector.py` accepts timestamp-sorted JSON Lines. Each event needs `ts` (ISO 8601 with timezone), `src_ip`, `host`, `path`, and numeric `status`. `src_ip` must be the real client address after a trusted proxy mapping; `host` must consistently identify the same virtual host. `path` is the path without a query string. The script groups by client, host, and the prefix before a final `_N` numeric suffix. It reports a `200` only when at least 100 **distinct** prior `404` paths in the same family fall within five minutes. Both values can be tuned.

```sh
python -B artifacts/web_enum_detector.py fixtures/web_events.jsonl --threshold 3
python -B artifacts/test_http_lab.py
```

The synthetic fixture has three misses and one success for one client, plus another-client noise. [`expected_detection.json`](../fixtures/expected_detection.json) records expected fields. The tests cover the positive case, wrong client, host, family, old activity, duplicates, success-first order, unsorted input, and malformed pcap. The script is offline and caps input at 10 MB / 50,000 events. It does not resolve shared NATs, normalize hosts or encoded paths, or deduplicate retries beyond distinct path counting. Legitimate scanners may match; a success status does not prove sensitive content was returned. Review account/session, response bytes, route sensitivity, and authorization before labeling an incident.

## SIEM and Sigma candidates

[`detection_queries.md`](detection_queries.md) gives SPL and KQL starting points with their field mapping and time-bin limits. [`sigma_endpoint_discovery.yml`](sigma_endpoint_discovery.yml) uses base events, `value_count`, and `temporal_ordered` correlation. It requires a precomputed `path_family` field and a backend that supports both correlations. The YAML parsed with pySigma; no backend conversion, SIEM execution, production calibration, or real-log accuracy test was performed. Translate the schema and test against local authorized-scan and application traffic before deployment.
