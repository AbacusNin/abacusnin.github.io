# Records-custodian defensive files

The writeup's challenge actions were conversational. These files adapt its emergency-access decisions to a small audit review lab. The sample identifiers are synthetic. No challenge daemon, model, health record, credential, or production audit pipeline is included.

| File | Use |
|---|---|
| [`ai-agent-authz-triage.md`](ai-agent-authz-triage.md) | Follow the authorized procedure, separate tier change from the audited action, and record decoys. |
| [`break-glass-abuse-detection.md`](break-glass-abuse-detection.md) | Sensor fields, Sigma and SPL scope, investigation steps, false positives, and validation limits. |
| [`break-glass-denials.sigma.yml`](break-glass-denials.sigma.yml) | Proposed Sigma base rule and fifteen-minute count correlation. |
| [`detect_break_glass.py`](detect_break_glass.py) | Read normalized server audit JSONL and emit findings plus routine emergency-access reviews. |
| [`fixtures/custodian-audit-sample.jsonl`](fixtures/custodian-audit-sample.jsonl) | Synthetic custodian audit sequence with one benign and one suspicious session. |
| [`fixtures/edge-cases.jsonl`](fixtures/edge-cases.jsonl) | Added benign, near-miss, and exact-window cases. |
| [`expected-results.json`](expected-results.json) | Expected findings and review queue for both fixtures. |
| [`test_detector.py`](test_detector.py) | Local behavior and malformed-record checks. |
| [`decision-path.svg`](decision-path.svg) | The full procedure, refused paths, identifier loop, and audit-token outcome. |

Run from this folder:

```sh
python -B -m unittest test_detector.py
python -B detect_break_glass.py fixtures/custodian-audit-sample.jsonl
python -B detect_break_glass.py fixtures/edge-cases.jsonl
```

The checker caps each input at 2 MB and 20,000 lines. Its output contains session IDs, signal names, and source line numbers; it omits record identifiers, credentials, and prompt text. The event schema is illustrative. Before using it on another system, map actual trusted event names and results, establish log integrity and retention, and test with legitimate emergency workflows.
