# Server-side composite gate

For a real disclosure interface, the protected unit needs to exist in the authorization policy. A model's promise to read only one field per request does not enforce a rule about the union of fields disclosed over time.

Before serving a field, the gateway should identify the authenticated caller, tenant, record, requested field, and action. It should check ordinary field permission and any composite grant. It then reads a durable disclosure ledger for that caller and record. If the new field would complete a protected component set for a caller without a grant, the gateway denies the read before obtaining or returning the field value. A verification endpoint separately checks the caller's right to use the composite and receive the result.

```text
authorize_field(caller, tenant, record, field):
    require ordinary field permission
    begin atomic transaction on caller + tenant + record disclosure ledger
    prior = successful disclosures within the policy lifetime
    if any protected component set is completed by prior + field
       and caller lacks that composite grant for this record:
        record denial and stop before reading the field value
    record the successful field disclosure and commit
    return the field value

verify_code(caller, tenant, record, candidate):
    require an independent composite grant for this caller and record
    then compare or validate the candidate and decide what result may be returned
```

The ledger and release must be coordinated so two concurrent requests cannot each pass a stale check. Its lifetime must match the actual disclosure policy; a session-only ledger lets the same caller start another session. The policy must define exceptions for legitimate multi-field work, expiration, reauthorization, and record ownership. Minimize retained data by storing field IDs and decisions rather than field values.

An authorized purple-team check should exercise the following outcomes with synthetic records:

| Test | Expected gateway result |
|---|---|
| Unauthorized caller reads two components | Both reads allowed if ordinary field policy permits them. |
| Same caller requests the final component | Denied before the value leaves the gateway. |
| Same caller presents an assembled candidate to the verifier | Verification and protected result denied. |
| Caller with a valid composite grant reads and verifies | Allowed for the authorized record. |
| Two concurrent requests would together complete the set | At most one completes; the other sees the updated ledger and is denied. |
| Caller changes sessions but keeps the same record | Prior disclosures still count for the defined policy lifetime. |

This is a design sketch, not a deployed control or a claim about the puzzle's internal implementation. The adjacent Python checker observes normalized events after a gateway decision. It cannot enforce these pre-release checks.
