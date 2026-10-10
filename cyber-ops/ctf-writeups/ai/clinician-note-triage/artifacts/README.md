# Clinician-note data-channel lab

These files turn the referral-note behavior into defensive tests for an authorized, synthetic LLM workflow. They contain no patient data, real escalation code, or production credentials. They were not run against the challenge assistant.

| File | Use |
|---|---|
| `note-as-instruction-template.md` | Parameterize the lower-trust field, business condition, output sink, and harmless canary. |
| `llm-data-channel-injection-checklist.md` | Plan and record direct, embedded, carrier, provenance, and negative-control tests. |
| `fixtures/sample-referral.txt` | Sanitized, fictional input shaped like the recorded qualifying referral. |
| `detect_referral_leak.py` | Lab-only check of normalized application events. It prints event IDs and signal names, not note or response text. |
| `fixtures/normalized-events.jsonl` | Seven synthetic events with expected alert and hunt results. |
| `trust-boundary.svg` | Expanded data-flow view of the input fields, protected value, output sink, and claimed channel gate. |

## Normalized event contract

One JSON object per completed assistant request. The detector requires `event_id` (string), `requester_verified` (boolean from the application authorization layer), `note_origin` (`requester` or `verified_clinician`, also assigned by the application), `note_text` (string), and `escalation_text` (string). The fixture adds `expected_alert` and `expected_hunt` for local checking. In production, the authorization and origin fields must come from trusted session and ingestion metadata, never from text inside a referral. The example uses a canary supplied to the checker; it is not a real secret.

Run the local fixture with Python 3 and the standard library:

```bash
python detect_referral_leak.py fixtures/normalized-events.jsonl --canary LAB-CANARY-42 --check-expected
```

An `ALERT` means an unverified request received the exact lab canary in its Escalation output. A `HUNT` means a requester-authored note contains a simple secret-request phrase; it can occur without disclosure. The seven cases include a leak, a benign expedited referral, a blocked attempt, an authorized response, a leak without a suspicious note, a lookalike canary, and an expected heuristic false positive. The checker reports only these local selections. It does not connect to a model, convert to a SIEM query, measure production accuracy, or prove the challenge response can be reproduced.

## Operational adaptation

The application should enforce authorization before any protected value enters the summarization context. Use a synthetic canary and fictional referrals when testing. If production telemetry is needed, minimize captured clinical text, restrict access, set retention, and avoid copying protected values into alerts. Review false positives from legitimate clinician instructions. The output check is a backstop; neither keyword matching nor model prompt wording is an authorization boundary.
