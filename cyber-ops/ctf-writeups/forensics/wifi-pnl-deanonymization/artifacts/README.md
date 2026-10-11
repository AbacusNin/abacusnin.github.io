# Probe-log PNL triage

[`pnl_leak_triage.py`](pnl_leak_triage.py) reads a local SQLite probe log and ranks universally administered source addresses by distinct, nonempty SSIDs. It prints the observed names for each displayed address in first-seen collection order. This gives an analyst candidates to inspect. The address bit cannot establish whether a device was randomized, and an SSID count cannot identify a person's saved networks on its own.

The default schema is a PineAP-style `log` table with `log_type`, `mac`, `ssid`, and `created_at` columns. Probe events have `log_type = 0`. `mac` is the source address, `ssid` is the probed name, and `created_at` is the collection timestamp; SQLite `rowid` breaks ties. Use `--table`, `--mac-col`, `--ssid-col`, `--time-col`, `--type-col`, and `--probe-type` to map another SQLite export. A blank time column uses `rowid`; a blank type column removes the record-type filter, so the caller must know the input contains only probes. The tool requires text MACs and SSIDs and a regular rowid table. It does not parse raw 802.11 frames or infer where a device traveled.

```bash
python pnl_leak_triage.py ../fixtures/sample-pineap.db --top 5
python pnl_leak_triage.py ../fixtures/stress-pineap.db --top 3
```

The input file is opened in SQLite read-only mode, with `query_only` enabled. Schema names must be simple SQL identifiers; the probe type and source address use bound parameters. The output is JSON. `--top` allows 1 to 50 addresses and `--max-ssids` allows 1 to 1,000 names per address; a `truncated` field marks a shortened list. The query still scans the input capture and holds the ranked address list in memory, so use a controlled workstation for large exports. Output can contain sensitive MACs and network names. Keep it within the authorized investigation.

The [baseline synthetic database](../fixtures/sample-pineap.db) has 300 locally administered addresses and one universally administered address with a six-name list. The tool returns that one review candidate and its names in order. The [stress database](../fixtures/stress-pineap.db) has three universally administered addresses. The top-ranked one has eight machine-like SSIDs and is an intentional false lead. The second has six coherent generic names. A local address with seven names stays out of the ranked list; a non-probe record does not enter the list. The [fixture generator](../fixtures/make_fixture.py) builds the stress case at a new path and refuses to overwrite an existing file.

These are local fixture checks. No wireless sensor, SIEM backend, live stream, or production alert was tested. A proposed operational hunt would need a sensor that preserves source MAC, directed SSID, probe timestamp, and event type. It would also need a window, thresholds, a managed-device allowlist, and human review of candidate names. Devices using universally administered addresses for legitimate reasons will appear. Local addresses can be stable or spoofed, and address values alone cannot prove hardware identity. A monitor that sees only broadcast probes cannot support this PNL review.
