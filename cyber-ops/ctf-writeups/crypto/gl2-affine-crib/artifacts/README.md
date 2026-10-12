# GL2(F67) affine probe

This is a defensive proof of concept for reviewing a custom matrix cipher. It models the source design's 11-symbol key, upper triangular matrix schedule, 12 adjacent-product rounds, 67-symbol alphabet, and per-symbol encryption. The included key and plaintext are invented. No challenge ciphertext or secret is included.

## Run

From this folder, with Python 3.8 or newer:

```sh
python -B gl2_affine_probe.py
python -B -m unittest -v test_gl2_affine_probe.py
```

The demo reads [`../fixtures/synthetic_case.json`](../fixtures/synthetic_case.json) and prints a JSON report. Eleven independent known positions recover the invented key. Seven independent positions leave four free key symbols and `67^4 = 20,151,121` algebraically compatible keys. The demo constructs two different candidates that both re-encrypt to the same ciphertext. Tests cover the full-rank result, this ambiguity, a conflicting crib, and malformed inputs.

## Inputs and outputs

`encrypt(key, plaintext)` and `decrypt(key, ciphertext)` accept printable symbols `<` through `~`; the key is exactly 11 symbols. `affine_model(count)` returns the fixed diagonal, zero-key addend, and 11 unit-probe columns. `crib_system(ciphertext, known)` accepts a mapping of zero-based positions to one-character known plaintext and returns a particular key, nullspace basis, and rank. `independent_positions(rows, count)` selects independent synthetic test positions. Inputs are bounded to 256 symbols to keep local resource use predictable. The script makes no network calls and needs only the Python standard library.

## Evidence boundary

The model was read from the Haskell challenge implementation and checked on the invented fixture. The original Haskell interpreter, target ciphertext, original Python solver, wordlist, and platform result are unavailable here; this tool cannot replay the historical solve. It does not implement the source-reported trigram ranking or enumerate all 20 million residual candidates. Re-encryption checks that a key/plaintext pair is internally consistent. Because each symbol transform is bijective, that check cannot select the intended key from an underdetermined family. A longer independent crib, a separate challenge constraint, or a platform result would be needed for that conclusion.

For use on an actual codebase, see the [review checklist](affine_cipher_review.md). This is a source-review aid; it consumes no production logs and provides no runtime detector or accuracy claim.
