# Signing-log `r` collision review

This defensive proof of concept reads local JSON Lines from a hypothetical firmware signing service. It does not use the challenge log, a real key, or valid ECDSA signatures. The invented fixture exercises event correlation only.

Run with Python 3.9 or later:

```sh
python test_signature_r_audit.py
python signature_r_audit.py synthetic_signing.jsonl
```

Each `Signed` event needs an offset-aware ISO 8601 `time`, `key_id`, `curve` (`secp256k1` or `P-256`), 32-byte hex `r`, `s`, and `message_hash`, and an `artifact_id`. The input is a protected application audit stream from the signing service. Normalize the digest exactly as the signer used it; the key identifier must distinguish unrelated signers. The output is JSON review leads with key, curve, `r`, artifact IDs, event times, source line numbers, and whether the message digests differ. Input is capped at 5 MB and 50,000 lines. No private key is ingested.

An identical tuple repeated under one key is treated as duplicate logging or repeat signing of one digest. A repeated `r` across distinct digests is urgent: preserve the records, independently verify the signatures and public key, then assess key exposure and rotate or revoke under the organization's signing-key process. A same-digest collision with a different `s` is a review lead too. The tool does not prove private-key recovery, validate signatures, account for every ECDSA normalization rule, or measure a production false-positive rate. It also cannot detect nonces that are biased but never repeated. Operationalize only after schema mapping, trusted log collection, signature verification, alert routing, and response testing.

The four local tests cover a distinct-digest collision, an identical retry, a different-key near miss, and malformed hex. The fixture values are synthetic and are not signatures on the recorded messages. No SIEM backend, real signing service, production key, or original challenge artifact was tested.
