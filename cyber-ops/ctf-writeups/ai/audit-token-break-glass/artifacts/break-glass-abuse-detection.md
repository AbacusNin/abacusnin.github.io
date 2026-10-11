# Emergency-access abuse detection pack

This pack starts with the records-custodian exercise. Its [Sigma correlation](break-glass-denials.sigma.yml), [SPL query below](#spl-hunt), and [local checker](detect_break_glass.py) look for repeated identifier mismatch denials. The checker also reports a title claim without a credential and a refused identifier-disclosure request. Those latter signals are review leads. They do not prove malicious intent.

## Sensor and mapping

Collect **server-generated** access decisions and audit entries from the emergency-access service. Normalize a timezone-aware `ts`, `session_id`, `event_type`, and `result`. The case fixture also has `actor_tier`, `reason_code`, `submitted_mrn`, `auth_code_presented`, `asserted_authority`, and `deny_reason`. The checker requires `auth_code_presented` on an `authority_assertion` and `deny_reason` on a denied `break_glass_attempt`. It reads the exact machine-readable reason `MRN mismatch`. Map local reason codes deliberately; free-text matching can miss translated or revised error messages.

Protect the log pipeline. Do not derive identity, tier, authorization, reason approval, or audit completion from a user's prompt or the model's prose. Keep medical record numbers and authorization codes out of the detection output. If correlation across records is necessary, use a controlled tokenization scheme and document who can reverse it. Set access and retention for this data before collection.

## Sigma correlation

The YAML uses a base event rule followed by an `event_count` correlation grouped on `session_id` over `15m`, with `gte: 3`. It follows the [Sigma correlation format](https://sigmahq.io/docs/meta/correlations). A count belongs in a correlation rule, with a referenced base selector. This rule parsed locally. It has not been converted to a SIEM backend or tested on its event mapping. Some converters use fixed buckets, which can miss events across a bucket edge. The executable checker uses an inclusive rolling 15-minute window so that boundary is explicit.

## SPL hunt

For Splunk installations where `records_custodian` is the mapped sourcetype, this query expresses a rolling window after sorting in time order:

```spl
index=ehr sourcetype=records_custodian event_type=break_glass_attempt result=deny deny_reason="MRN mismatch"
| sort 0 _time session_id
| streamstats time_window=15m count AS failures BY session_id
| where failures >= 3
| stats earliest(_time) AS first_threshold, max(failures) AS max_failures BY session_id
```

For a lower-priority hunt, collect refused identifier requests and title claims without a credential, then pivot by session:

```spl
index=ehr sourcetype=records_custodian ((event_type=mrn_disclosure_attempt result=refuse) OR (event_type=authority_assertion auth_code_presented=false))
| stats count AS events values(event_type) AS signals BY session_id
```

Check the installed Splunk version's `streamstats` limits and the field mapping before deployment. A backend conversion and a live SPL execution remain undone. A fixed 15-minute `bin` query could miss three events that straddle a bucket boundary. The local checker covers that near miss and the exact inclusive boundary.

## Review and response

The [synthetic case events](fixtures/custodian-audit-sample.jsonl) produce three review leads for `sess-abuse-07`: title assertion without a credential, refused identifier disclosure, and three mismatch denials. The file has a later `break_glass_attempt` with `result=grant` for that session, but it has **no** `break_glass_grant` or `audit_token_issued` event for it. The checker therefore does not mark that session's audit write as observed. A benign session has an actual `audit_token_issued` event and goes to the review queue without a suspicious finding. The [edge cases](fixtures/edge-cases.jsonl) add a single-mistype emergency, an outside-window near miss, and a threshold hit at exactly 15 minutes. [Expected outputs](expected-results.json) make those outcomes inspectable.

My hunt hypothesis is a session that asserts authority or probes for a record identifier, accumulates several identifier-mismatch denials, and then attempts emergency access. The sequence merits review; a completion event would make the timeline stronger. Investigate by validating the server's decision and audit record, then reviewing the emergency predicate and authorized role under local policy. A genuine clinician can mistype an identifier or retry after a stale integration value. A signature block can mention a senior title without an access attempt. Those cases should be measured before paging a responder. Every completed emergency access can enter a routine human review queue even when no suspicious signal fired. Escalation to an incident needs more than this synthetic pattern.

## Validation status

The standard-library checker passed its local case-fixture, benign, near-miss, boundary, and malformed-record checks. This establishes the fixture logic only. The Sigma file parsed locally, with no backend conversion. The SPL is an illustrative query; it has not run in Splunk. No production audit feed, false-positive rate, detection latency, or audit-integrity control was measured.
