# RSA-CRT fault review lab

These are synthetic defensive proofs of concept. They do not use the challenge modulus, signature, ciphertext, flag, or network service.

## Run

Python 3.10 or later, standard library only:

```bash
python test_pocs.py
python rsa_fault_lab.py
python signing_audit.py signing-events.jsonl
```

`rsa_fault_lab.py` uses tiny fixed primes to reproduce the case's math. It returns valid signatures on messages 2 and 5 and one faulted signature on 3. The GCD recovers a nontrivial factor, and the reconstructed private exponent decrypts a synthetic integer. A second branch checks the result before return and raises on the fault. It also includes the prepared multiplicative blinding fallback, with an invertibility check. This is textbook RSA for a controlled lab, never a production signing implementation.

`signing_audit.py` consumes UTF-8 JSON Lines from a hypothetical signing-service audit stream. Each event requires `time` (offset-aware ISO 8601), `client_id`, `key_id`, and `kind`. `sign_request` also needs `message_bits`; `fault_validation_failed` needs no extra field. It prints JSON review leads for three small messages from the same client/key within 10 minutes and for any internal output-validation failure. The source is application telemetry after TLS termination, not Zeek connection metadata. The detector uses counts and bit lengths, not message bodies, signatures, ciphertexts, or private keys. A real deployment would need authorization context, a per-client baseline, bounded state, and an event schema mapped to the actual service.

The tests cover fault recovery, blocking before return, a valid-signature negative, blinding and noninvertible-factor rejection, a positive sequence, a benign health check that produces the same small-message lead, and a near miss outside the time window. Expected and observed: one recovered toy factor; guarded fault rejected; no factor from a valid signature; blinding returns the synthetic plaintext; positive produces two leads; benign produces one false lead; near miss produces none. These are local logic checks only. No challenge replay, SIEM backend conversion, production sensor, or measured detection rate was performed.

Operationally, `output-fault` is the urgent signal. The service must discard a failed output and quarantine the affected key while responders assess exposure. `small-message-probes` is only a triage lead; health checks and normal test clients may trigger it. Raw transport counts cannot reveal whether the messages were small or what the RSA implementation returned.

The [Sigma rule](signing_fault.yml) expresses the same output-fault event for a hypothetical application log mapping. Its YAML parses locally; Sigma schema validation and backend conversion were not performed. Map `kind`, `client_id`, `key_id`, and `time` to the real application's fields before use. A network-only sensor cannot supply this event.
