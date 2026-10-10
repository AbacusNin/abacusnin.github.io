# Composite disclosure lab

This small lab turns the ROI clerk's field-by-field disclosure pattern into a gateway-log check. It uses fictional IDs and field names. It contains no patient information, custodian code values, or challenge transcript. The checker does not call an LLM or a disclosure service.

## Files

| File | Use |
|---|---|
| `audit_aggregation.py` | Correlate successful field disclosures by tenant, caller, record, and session; flag a completed protected field set and an allowed verification without a grant. |
| `fixtures/composites.json` | Define a fictional protected composite and its component field IDs. |
| `fixtures/gateway-events.jsonl` | Supply 26 synthetic gateway events covering positive and negative paths. |
| `fixtures/expected-findings.json` | Hold the four findings expected from the fixture. |
| `policy-gate-sketch.md` | Describe the server-side prevention check and purple-team acceptance tests. |
| `roi-flow.svg` | Show the refused recipe, catalog pivot, three separate reads, offline assembly, and verifier. |

Run the fixture with Python 3 and the standard library:

```bash
python audit_aggregation.py fixtures/gateway-events.jsonl fixtures/composites.json --expected fixtures/expected-findings.json
```

The local check emits four findings and `PASS: 26 synthetic events, 4 expected findings`. Its positive path covers the three component reads and the allowed verification without a composite grant. A second positive path shows that catalog enumeration raises context but is not required to detect complete disclosure. Negative paths cover an authorized staff flow, two of three fields, fields split across records, fields split across sessions, and a denied final read. The `missing-grant` path is an expected operational false positive: if a legitimate staff grant is absent from the event, the checker cannot distinguish that workflow from unauthorized collection.

## Required event contract

The input is a time-ordered JSONL export from a disclosure gateway, one event per line. Each event needs `event_id`, ISO 8601 `timestamp`, `tenant_id`, `caller_id`, `record_id`, `session_id`, `action`, `decision`, and `composite_grants`. A `field_disclosure` event also needs `field_id`; a `verification` event needs `composite_id`. Actions are `schema_enumeration`, `field_disclosure`, or `verification`. Decisions are `allowed` or `denied`. A granted composite ID means the authorization service allowed that caller to obtain that composite for this record at the time of the request.

These identity and grant fields must come from trusted authentication and authorization records. Do not derive them from the caller's prompt or the model's text. Map a real gateway's event names and field IDs before using the checker. The policy file must list each sensitive composite's actual component set. Those sets are application policy, not values inferred from the logs.

The checker prints only event IDs, composite IDs, and finding types. It does not need field values, chart text, code segments, or model output. A real alert pipeline still needs protected log storage, access limits, and retention appropriate to the data.

## Limits

This is a synthetic logic check, not a production SIEM rule or measured detector. It processes a small, ordered export in memory. A split across sessions is deliberately outside its correlation key; durable caller-and-record accounting may be needed to close that gap. Missing grant tags, legitimate multi-field workflows, changed field definitions, late events, and shared identities need site-specific handling. A fixed 15-minute window can miss slow collection; this example tracks the supplied session without a time cutoff. Detection is a backstop. The trusted gateway must enforce the composite policy before releasing the final component or confirming a code.
