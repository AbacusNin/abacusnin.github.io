# ECDSA timing review lab

This folder separates a challenge replay from a defensive signing test. The challenge trace, public key, ciphertext, recovered scalar, and plaintext are absent. The public files contain only code, invented timing fixtures, and a generic technique description.

| File | Purpose |
|---|---|
| [hnp_replay.py](hnp_replay.py) | Replay six-signature P-256 lattice recovery with local inputs. It checks the recovered scalar against the supplied public key and reports ciphertext shape without printing the scalar or plaintext. |
| [latency_leak_check.py](latency_leak_check.py) | Measure latency correlation with nonce width in a controlled signing benchmark. |
| [fixtures/leaky.csv](fixtures/leaky.csv) | Invented positive benchmark with a 250 ns-per-bit slope. |
| [fixtures/flat.csv](fixtures/flat.csv) | Invented equal-latency benchmark across nonce widths. |
| [fixtures/sparse.csv](fixtures/sparse.csv) | Invented insufficient sample for rejection testing. |
| [test_lab.py](test_lab.py) | Positive, negative, and insufficient-data tests for the benchmark reviewer. |
| [technique_bundle.json](technique_bundle.json) | Illustrative STIX 2.1 attack pattern, course of action, and mitigation relationship. No product, campaign, or IOC claim. |

From this directory, Python 3.10 or later is sufficient for the controlled timing test:

```sh
python -m unittest -v test_lab.py
python latency_leak_check.py fixtures/leaky.csv
python latency_leak_check.py fixtures/flat.csv
```

Expected results: the invented leaky fixture has a 250 ns-per-bit slope and is marked for review; the flat fixture has zero slope and stays clear; four sparse measurements fail input validation. The tool reads at most 1 MB and 10,000 rows. The `review_leak` flag is an instructional threshold, not a constant-time certification or production detector. A flat result can arise from too little precision, poor experimental control, or inadequate statistical power. Repeat controlled measurements on the actual signing implementation, across CPU states and nonce widths, with a cryptography engineer reviewing the method.

To replay the challenge analysis against locally held artifacts, install a maintained PyCryptodome build and run:

```sh
python hnp_replay.py trace.csv public_key.txt --ciphertext wrapped-flag.hex
```

The ciphertext argument expects ASCII hex representing 35 bytes. The script uses the six shortest signing times, the case-specific 133662 ns intercept, 250 ns-per-bit step, and four-bit safety pad. It uses bounded local input reads and a pure-Python LLL routine capped at 150,000 iterations, then accepts a candidate only if multiplication by the P-256 base point exactly equals the supplied public key. The private scalar and decrypted bytes are never printed. The code is a transparent case replay, not a general noisy-HNP solver; different leakage may need per-signature bounds, more samples, or a stronger lattice library. Keep source traces and recovered keys in authorized storage.

The defensive fixture schema is `nonce_bits,elapsed_ns`. A test harness must know or control the nonce width in an isolated development build. Most production signers should not log nonce values or widths; observing only client request times does not provide this fixture's ground truth. The signer should be assessed for a secret-independent execution path, including scalar multiplication. RFC 6979 addresses nonce generation and does not by itself make that path constant time. A validated module designation or deterministic signature is not a substitute for this test.

The STIX file was parsed as JSON and checked for valid UUIDv4 identifiers and internal relationship references. It has not been exchanged over TAXII or validated by a full STIX schema implementation. Before sharing, add a real affected product/version, evidence, scope, producer identity, and handling markings as required by the recipient.
