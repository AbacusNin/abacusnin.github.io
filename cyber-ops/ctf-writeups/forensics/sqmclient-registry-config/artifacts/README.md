# Registry configuration review lab

This lab turns the case's three-key registry pattern into reviewable checks. It does not contain the challenge hive, implant binary, C2 domain, key, or decrypted configuration. All fixture values and host names are invented.

| File | Purpose |
|---|---|
| [regxml_review.py](regxml_review.py) | Stream a local regxml SOFTWARE export and report the six case value names, declared types, and safe decoded lengths. It withholds value data and fails on incomplete XML. |
| [registry_event_review.py](registry_event_review.py) | Group normalized Sysmon Event ID 13 value writes by host. It reports candidate names and whether all six appeared in the supplied event window. |
| [registry_value_candidate.yml](registry_value_candidate.yml) | Experimental Sigma selector for each exact key and value-name pair. A single match is a triage lead. |
| [hunt_queries.md](hunt_queries.md) | KQL and SPL templates for registry write hunting, with required fields and collection limits. |
| [defense_path.svg](defense_path.svg) | Case and defender-review diagram linked from the article. |
| [test_registry_lab.py](test_registry_lab.py) | Seven local test groups for positive, benign, near-miss, malformed, and DTD inputs. |
| [fixtures/case.xml](fixtures/case.xml) | Invented complete six-value regxml pattern. |
| [fixtures/benign.xml](fixtures/benign.xml) | Invented ordinary value names at the same keys. |
| [fixtures/near_miss.xml](fixtures/near_miss.xml) | Invented single `Token` value, insufficient for the full case pattern. |
| [fixtures/events.jsonl](fixtures/events.jsonl) | Invented positive, benign, and near-miss registry write events. |
| [fixtures/truncated.xml](fixtures/truncated.xml) | Malformed XML to check that partial snapshots fail closed. |
| [fixtures/doctype.xml](fixtures/doctype.xml) | XML entity declaration to check parser rejection. |
| [fixtures/malformed.jsonl](fixtures/malformed.jsonl) | Malformed event input for error handling. |

Run locally with Python 3.10 or later:

```sh
python -m unittest test_registry_lab.py
python regxml_review.py fixtures/case.xml
python registry_event_review.py fixtures/events.jsonl
```

The snapshot parser expects UTF-8 nested regxml `node` elements with `name` attributes and `value` elements with `key`, `type`, and `value` attributes. It accepts a local XML file up to 160 MiB, at most 64 nested nodes, 256 values per target key, and 8,192 characters per target value. It rejects DTD/entity declarations, removes processed XML elements while streaming, and never fetches external resources. It does not execute data, emit raw registry values, or infer the cipher from length alone. A complete parse is required before it emits a report. The case pattern requires `Token`, `ConfigPath`, `CacheMap`, and `SessionMap` under `Microsoft\SQMClient`, plus `SessionId` under `Microsoft\Wbem` and `Upload` under `Classes\Installer`. Exact value-name matching is a case-specific lead, not a Windows-wide registry schema.

The event reviewer expects one JSON object per line with `host`, integer `event_id`, and `target_object` in an `HKLM\SOFTWARE\...\ValueName` shape. Normalize product-specific exports into that schema first. It accepts at most 2 MiB and 20,000 events. Its six-value result is per host across the supplied file. It does not prove the writes came from one process or that they occurred in a meaningful order. Missing events do not exclude values that were written before retention began. It emits host names and value names, but no registry data.

Sysmon Event ID 13 is the intended live sensor for the Sigma selector and SPL example. The KQL example uses Microsoft Defender's `DeviceRegistryEvents`. Both require an actual collection policy covering the keys. Security Event 4657 needs a `Set Value` SACL on the audited key as well as the audit policy. The rule and query templates require field mapping, backend conversion, and local false-positive review. PySigma parsed the Sigma file; no backend query, live stream, production host, or fleet false-positive rate was tested.

Seven local tests passed: the full synthetic snapshot produced one complete case pattern with 32 and 34 decoded bytes; the benign snapshot produced none; a lone `Token` stayed a near miss; truncated XML and a DTD failed; the event tool distinguished positive, benign, and near-miss hosts; and malformed JSONL failed. A legitimate enterprise product could use one of these names. Verify any hit against approved host baselines, writer identity, file provenance, and the rest of the three-key state before escalating.
