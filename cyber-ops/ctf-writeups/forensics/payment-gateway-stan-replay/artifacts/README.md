# Payment-gateway session review proofs of concept

These files let an analyst review a repeated transaction number and nearby reversal **after a trusted ISO 8583 parser has produced structured events**. The challenge capture is not included. All example events are invented and contain no payment account number.

## Inputs and fields

The Python reviewer accepts JSONL events with `event_id`, `terminal_id`, `processing_date` (`YYYY-MM-DD`), `session_id`, `mti`, and six-digit `stan`. A reversal may also have `original_stan`; a response may have `response_code`. The source can be a complete gateway audit log or a partial capture, but the interpretation of missing responses depends on which it is. The tool rejects unexpected fields, including raw PAN. It limits input to 5 MB and 20,000 events.

The Sigma and SPL files assume a separate, authorized parser maps each gateway event to `mti`, `stan`, `terminal_id`, `processing_date`, and `session_id` with a reliable `_time`. The field names are local mapping assumptions, not native ISO 8583 fields supplied automatically by a SIEM. The Sigma correlation groups by terminal, processing day, and STAN; it reports reuse, which can be a legitimate retry. The SPL searches preserve first and last event times and classify cross-session repeats or sessions with observed request/response imbalance. Neither query proves intent, gateway approval, or settlement.

## Run and interpret

```sh
python gateway_session_review.py fixture.jsonl
python test_gateway_session_review.py
```

Expected synthetic output includes a cross-session repeated STAN, an authorization response absent from the second session, and a reversal whose original STAN appears in the input. The test script also checks a same-session retry, a different-terminal/day near miss, and rejection of a raw PAN field. The Python checks passed locally. The Sigma YAML was parsed as two documents and checked for the expected correlation structure. No Sigma backend conversion, Splunk execution, gateway log ingest, or real payment capture replay was performed.

For a real investigation, verify TCP stream reconstruction, parse the gateway's specific ISO 8583 profile including its reversal reference fields, compare complete gateway logs and acknowledgments, and obtain authorization and settlement records. A duplicate STAN, a missing packet response, or a `0410` response alone cannot establish fraud or a control failure. Tune the grouping and time window to the gateway's actual identifier rules, retries, and processing-day rollover. Keep account data out of this analytic and its logs.
