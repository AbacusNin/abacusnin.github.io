# Booking-client behavior lab

These files are defensive proofs of concept for adapting the booking-log case to a real service. The public code and tests use invented `/availability` and `/reserve` paths. No challenge access log or raw source IPs are published here.

| File | Purpose and input | Output and status |
|---|---|---|
| [booking_hunt.py](booking_hunt.py) | Offline Apache Combined log, exact availability GET path, exact reservation POST path | JSON candidate sources with a regular poll session and a same-second POST pair; executed against the exercise log and invented tests |
| [test_booking_hunt.py](test_booking_hunt.py) | Invented in-memory positive, benign, near-miss, disjoint-session, and parser cases | Five local test groups; no production accuracy claim |
| [availability_poll_sigma.yml](availability_poll_sigma.yml) | Webserver events with `cs-method` and `cs-uri-stem` | Informational event selector for downstream correlation, not a standalone bot rule |
| [detection_queries.md](detection_queries.md) | Normalized web events with timestamps, source IP, method, and path | KQL/SPL candidate templates; not executed against a backend |

Run the offline tool with Python 3.10+:

```sh
python -m unittest test_booking_hunt.py
python booking_hunt.py /path/to/authorized/access.log --availability /availability --reserve /reserve
```

The parser accepts Combined Log Format lines with `GET` or `POST`, an Apache timestamp with a numeric zone or an empty zone, a three-digit HTTP status, and quoted referrer and User-Agent. It fails closed on unsupported rows, caps the file at 10 MB and 100,000 lines, and never reads request bodies. Output includes source IPs because this is a local triage tool; treat those results as protected operational data. For an authenticated service, replace source-IP grouping with account identity and keep IP as enrichment.

The detector splits poll sessions after ten idle minutes, then requires at least four polls, a within-session interval coefficient of variation below 0.05, and two reservation POSTs no more than one second apart within five seconds after the last poll. Those values fit the small exercise and are not a deployed policy. A scheduler, partner integration, monitoring client, or an auto-refresh page can look regular. Source IP sharing can merge different people; rotation can split one actor. A returned HTTP 200 does not show whether the booking succeeded.

The local replay of the 1,290-row, 253-source exercise log returned the two challenge-labeled sources and no other source under those parameters. The result measures this synthetic artifact only. The Sigma selector has no cadence or burst semantics. The SIEM examples need schema mapping, local baseline review, and backend execution before operational use.
