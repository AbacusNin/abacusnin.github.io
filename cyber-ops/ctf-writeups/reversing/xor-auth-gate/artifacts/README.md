# One-byte XOR gate recovery

This offline helper checks a narrow fact: if a program compares each input byte XORed with one fixed key against a fixed byte table, the table and key recover the required input. The JSON fixture is invented. No challenge credential or binary is included.

## Files and run

- [`xor_recover.py`](xor_recover.py): bounded JSON reader and inverse XOR calculation.
- [`test_xor_recover.py`](test_xor_recover.py): synthetic positive, benign, near-miss, and invalid-input checks.
- [`../fixtures/example_expected.json`](../fixtures/example_expected.json): invented 19-byte gate for `admit the test user`.
- [`static_gate_review.md`](static_gate_review.md): manual review and disclosure checklist for a real binary.

```sh
python xor_recover.py ../fixtures/example_expected.json
python xor_recover.py ../fixtures/example_expected.json --reveal
python -m unittest test_xor_recover.py
```

The default output reports length, printable-ASCII status, and SHA-256. `--reveal` also prints the recovered text, so it can expose a credential in terminal scrollback, screen capture, or redirected logs. Use it only with data you are authorized to handle. The positive fixture recovers `admit the test user`; the benign two-byte table only exercises the math and is not classified as an authentication finding. A fixture whose stated length disagrees with its table is rejected.

## Input and limits

The UTF-8 JSON file must be at most 32 KiB and contain exactly `key` (integer 0-255), `length` (integer equal to the table size), and `expected` (1-4096 integers from 0-255). The helper returns bytes from XOR inversion. It does not parse an ELF, prove that a table is an authentication check, validate a branch, or run a target. The analyst must establish those facts from the binary as described in the checklist. No dependency beyond Python 3 is required.

The tests validate this synthetic logic only. They do not replay the challenge's reported success run, measure false positives in shipped applications, or test a production sensor.
