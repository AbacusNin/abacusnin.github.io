# Hash-verifier review lab

These are defensive proofs of concept for a service that issues short hash targets and exposes diagnostic digests after rejection. They do not connect to the challenge service. The event fixture is invented and contains no candidate plaintext or raw digest.

| File | Purpose | Input and output |
|---|---|---|
| [digest_compare_review.py](digest_compare_review.py) | Triage Python digest-prefix comparisons during code review | One or more local `.py` files to JSON line/kind findings; reads AST only, never executes source |
| [service_hash_review.py](service_hash_review.py) | Check normalized service-audit events for short tags, unkeyed verification, and digest echoes | JSONL event export to JSON review findings, without printing submitted values |
| [audit_queries.md](audit_queries.md) | Translate the service-audit review to Splunk and Sentinel | SPL and KQL starting points using the documented normalized fields; not backend-tested |
| [defense_path.svg](defense_path.svg) | Show the puzzle behavior, review points, and service-side controls | Static visual linked from the article |
| [test_defensive_lab.py](test_defensive_lab.py) | Exercise positive, benign, expected false-positive, near-miss, and malformed cases | Six local test groups |
| [fixtures/service_events.jsonl](fixtures/service_events.jsonl) | Invented example of a weak 24-bit raw-hash service, an HMAC service, and a full-length raw-hash near miss | Input to the service review tool |

Run with Python 3.10+ from this folder:

```sh
python -m unittest test_defensive_lab.py
python service_hash_review.py fixtures/service_events.jsonl --min-tag-bits 128
python digest_compare_review.py /path/to/authorized/service.py
```

The source reviewer catches direct `hashlib` or `hmac` digest calls, a simple assigned hash object, and a simple assigned digest used with `.startswith()` or a prefix slice in a comparison. It can miss aliases, wrappers, interprocedural flow, or a digest prefix stored in another variable. A tested short display-label comparison is an expected false positive. Every result needs a reviewer to establish whether the comparison protects authentication, integrity, or only a display label. The file limit is 1 MB. Parsing never imports or runs the target.

The service review expects `issued` events with `session`, `construction` (`raw_hash` or `hmac`), and integer `tag_bits`; `rejected` events require `session` and boolean `echoed_digest`. The sample also records an algorithm name, but the tool deliberately does not decide safety from that field alone. A local instrumentation layer must produce these fields from the real application's verifier and response path. Do not log candidate plaintext, secret keys, raw digests, or response bodies to make this check work. The JSONL limit is 2 MB and 20,000 events.

The `128`-bit tag floor is an **illustrative local policy**, not a universal NIST requirement. Select a length and construction for the protocol's threat model. A full-length unkeyed hash still does not authenticate an untrusted submitter. A keyed MAC, sound key management, a documented comparison length, and application outcome tests belong in the actual design review. The fixture returns three findings for the weak sample, none for the 128-bit HMAC sample, and one for the full-length unkeyed near miss. Neither tool was run against production source or live service telemetry. No false-positive rate has been measured.
