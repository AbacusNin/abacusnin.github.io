# LLM gateway authorization and audit lab

These files turn the court case into a small defensive proof of concept. The court's four merits were a puzzle rule. A real service should use authenticated identity and server-owned authorization records, with secrets kept outside model context. This lab does not run an LLM or hold a real secret.

## Files and purpose

- `llm-gatekeeper-solve-checklist.md`: reusable assessment record for authorized gatekeeper tests.
- `gateway_policy_demo.py`: an illustrative decision function. It matches an authenticated subject, requested object, release permission, and expiry against trusted server grants. User text is excluded from the decision.
- `gateway_audit_hunt.py`: checks normalized gateway audit events for release after denial, release outside the authorized object, and a state-version change without an approved transition.
- `fixture_events.jsonl`: seven synthetic audit records, including three invariant breaks and four controls.
- `expected_findings.json`: the three expected findings.
- `test_lab.py`: seven local checks of authorization scope, forged-rank text, expiry, malformed grant data, positive audit findings, benign controls, and event validation.

## Run

```sh
python -B -m unittest test_lab.py
python -B gateway_audit_hunt.py fixture_events.jsonl
```

The first command should report seven passing tests. The second should emit exactly the three findings in `expected_findings.json`: `evt-03` release after denial, `evt-04` unapproved state change, and `evt-05` release outside object scope. The four other events are expected controls, including an allowed release, an ordinary denial, and an approved state change.

## Required sensor and event mapping

The audit hunt requires **server-generated** UTF-8 JSON Lines, one decision or release event per line. Each event needs a unique `event_id`; timezone-aware ISO 8601 `timestamp`; `session_id`, authenticated `subject_id`, and requested `object_id`; `authorized_object_id` from the server grant or `null`; `authz_decision` (`allow` or `deny`); Boolean `released` and `approved_transition`; and nonnegative integer `state_version_before` and `state_version_after`. These fields are a proposed normalized schema. Do not derive trusted identity, grant scope, decision, or transition approval from a user prompt or model completion. The reader rejects malformed relevant records and duplicate IDs, and caps input at 5 MB and 50,000 lines. Output is JSON findings with event identifiers and no prompt or protected value.

## Boundaries and tuning

The policy example assumes a trusted identity provider and grant store, but supplies neither. It does not implement grant issuance, revocation, storage, sessions, concurrency, output filtering, or an actual release operation. In particular, finding an `allow` response here does not authorize a production request. The audit hunt assumes logs accurately describe server decisions and releases. A compromised, client-controlled, missing, or delayed log stream can hide an incident or create a false lead. Correlate a finding with authoritative release records before acting.

The synthetic fixture tests local logic only. It does not replay the challenge chat, evaluate model resistance, convert a Sigma/KQL/SPL rule, establish detector precision or recall, or validate a production gateway. In a deployment, first map actual gateway events to this schema, define retention and redaction, baseline legitimate state transitions, test denied and cross-object releases, and tune incident routing. Raw prompts are intentionally unnecessary for the primary invariant checks; a separate prompt-language hunt would need privacy review and measured false positives.
