# Service-audit hunts for a short hash verifier

These templates look for verifier configuration and response behavior, rather than a high connection rate. The challenge's local search followed by one submission would be easy to miss with a network rate rule. Neither query has been run in Splunk or Sentinel.

Map these normalized application fields first: `kind` (`issued` or `rejected`), `session` (opaque session ID), `construction` (`raw_hash` or `hmac`), numeric `tag_bits`, and boolean `echoed_digest`. The application should emit the last field as a boolean after constructing a response. Do not ship candidate plaintext, raw digest, secret key, or response body into the audit stream.

The `128`-bit floor below is an illustrative local policy. Set it from the protocol's security goal and approved design. A full-length raw hash still does not authenticate an untrusted caller.

## Splunk SPL

```spl
index=app sourcetype=hash_verifier_audit
| where (kind=="issued" AND (tag_bits<128 OR construction=="raw_hash")) OR (kind=="rejected" AND echoed_digest=="true")
| eval finding=case(kind=="issued" AND tag_bits<128,"short-comparison",kind=="issued" AND construction=="raw_hash","unkeyed-verifier",kind=="rejected" AND echoed_digest=="true","diagnostic-echo")
| table _time session kind construction tag_bits echoed_digest finding
```

One event can have two issues. This simple `case()` expression emits only its first matching label. Review all matching fields, or expand one event into separate findings in the pipeline. The [offline reviewer](service_hash_review.py) emits both.

## Microsoft Sentinel KQL

```kusto
HashVerifierAudit
| where (kind == "issued" and (tag_bits < 128 or construction == "raw_hash"))
    or (kind == "rejected" and echoed_digest == true)
| extend finding = case(
    kind == "issued" and tag_bits < 128, "short-comparison",
    kind == "issued" and construction == "raw_hash", "unkeyed-verifier",
    kind == "rejected" and echoed_digest == true, "diagnostic-echo",
    "review")
| project TimeGenerated, session, kind, construction, tag_bits, echoed_digest, finding
```

The same first-match limitation applies to the KQL `case()` result. The queries are review feeds, not attack attribution. Pair findings with code ownership, key management, the actual comparator, and an application test of accepted and rejected inputs. Restrict audit-log access because opaque session IDs can still be sensitive in context.
