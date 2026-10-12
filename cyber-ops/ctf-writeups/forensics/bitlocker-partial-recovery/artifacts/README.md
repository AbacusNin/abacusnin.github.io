# Recovery material and activity lab

These are defensive proofs of concept derived from the partial-recovery case. No challenge image, recovery password, extracted BitCracker hash, decrypted volume, or personal key material is included. The [sample note](../fixtures/sample_note.txt) and [event stream](../fixtures/sample_events.jsonl) are invented.

| File | Purpose | Input and output |
|---|---|---|
| [fve_inventory.py](fve_inventory.py) | Bounded, read-only FVE metadata inventory | Local image path to a JSON summary of signature, metadata locations, algorithm and protector types; never prints encrypted key blobs |
| [recovery_structure.py](recovery_structure.py) | Identify plausible full or 7-group-plus-partial recovery-key shapes | UTF-8 document up to 1 MiB to counts only; does not print matched strings |
| [recovery_events.py](recovery_events.py) | Triage unusual normalized recovery activity | JSONL up to 1 MiB to findings with actor, time and count only |
| [recovery_unlock_sigma.yml](recovery_unlock_sigma.yml) | Windows process creation candidate for recovery unlock commands | EDR/Sysmon/4688 process data; requires tuning, redaction, and approved-case enrichment |
| [detection_queries.md](detection_queries.md) | KQL and SPL starting points | Normalized events with the exact fields documented there |
| [test_recovery_lab.py](test_recovery_lab.py) | Positive, benign, near-miss and malformed cases | Local synthetic fixtures to assertions |
| [key_paths.svg](key_paths.svg) | Visual map of both protector routes and defender telemetry | Static diagram for the article |

Run with Python 3.10+ from this directory:

```sh
python -m unittest test_recovery_lab.py
python recovery_structure.py ../fixtures/sample_note.txt
python recovery_events.py ../fixtures/sample_events.jsonl
python fve_inventory.py /path/to/authorized-image.img
```

The event tool expects `time` (timezone-aware ISO 8601), `kind` (`recovery_unlock` or `ad_recovery_read`), `actor`, plus `target_id` and `attribute_name` for directory reads. `approved_case=true` marks activity linked to an independently verified helpdesk or IR workflow. It has no raw command line or password field. It reports a read spike for at least three distinct target IDs in a rolling 15-minute window, and each unapproved recovery-unlock event. It does not prove an unlock succeeded. This threshold is a lab value to tune, not a production baseline.

Real AD read detection needs Directory Service Access auditing, a SACL on the relevant attribute, schema GUID resolution, and access to domain controller logs. Endpoint process detection needs command-line telemetry. Those command lines may contain recovery secrets, so protect and redact them before forwarding to dashboards or tickets. No backend SIEM conversion, production telemetry run, or false-positive-rate measurement was performed.
