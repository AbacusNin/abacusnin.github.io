# Two-symbol message audit

This offline proof of concept inventories a message whose tokens contain only `/` and `\`. It is an analysis aid inspired by a CTF cryptogram. The included stream is invented and spells `banana` under one homophonic mapping; it is not challenge evidence.

## Files and run

- [`two_symbol_audit.py`](two_symbol_audit.py): bounded parser and JSON report.
- [`sample_stream.txt`](sample_stream.txt): six synthetic tokens.
- [`test_two_symbol_audit.py`](test_two_symbol_audit.py): positive, ordinary-Morse, conflict, malformed-input, and segmentation checks.

```sh
python two_symbol_audit.py sample_stream.txt --candidate banana --word-lengths 3,3
python -m unittest test_two_symbol_audit.py
```

The sample should report six tokens, four distinct tokens, a consistent candidate, and a local token in the first proposed segment. The tool also shows both Morse polarities and invalid A-Z positions. A valid Morse rendering does not establish that the message was intended as Morse. A consistent candidate does not establish a unique or correct decode.

## Input, output, and limits

Input is a UTF-8 file no larger than 1 MB, with one line of tokens separated by single spaces. Each token has one to four marks. A final newline is allowed. The tool rejects other characters, blank lines, and more than 100,000 tokens. `--candidate` takes one lowercase letter per token, with no spaces. `--word-lengths` takes analyst-proposed positive lengths summing to the token count. Token separators alone do not encode word boundaries.

Output is JSON with counts, token lengths, stable token IDs and their sequence, both Morse readings, optional candidate conflicts, and optional segments with tokens that occur nowhere outside that proposed segment. The consistency rule is one-way: one token cannot map to two letters, while several tokens may map to the same letter.

This tool makes no network calls, reads no logs or sensor feed, and emits no alert. It does not search a dictionary, prove plaintext uniqueness, infer malicious intent, or recover the withheld challenge answer. An operational use would need authorized source data, preserved original bytes and provenance, human review of alternate readings, and a separate security case with its own telemetry. The local synthetic tests do not measure false positives or accuracy on real messages.
