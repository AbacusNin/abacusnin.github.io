# Modular locale verifier lab

The verifier models one character-driven transform that chooses answer forms with `M1` and carries state with `M2`. It reads a JSON model, a question line per key character, an aligned answer file, and a candidate key. It parses multiword forms using the known field order, checks the candidate's generated answer bytes against the observed bytes, prints both SHA-256 digests, and counts possible characters at each position **while holding the candidate prefix fixed**. A count is not a proof that the earlier prefix is unique.

This is a file-analysis proof of concept. Its data source is the three supplied text/JSON files, not endpoint or network telemetry. The required fields are `mod_form`, `mod_state`, and each named field's `series` and ordered `forms`. Each question line names one or more fields. Answer lines contain their selected forms in the same order, separated by spaces. The form array must contain one entry for every possible index modulo `M1`.

Run the neutral demo with Python 3 from this folder:

```sh
python fixtures/make_fixture.py
python locale_machine_verifier.py
python locale_machine_verifier.py --key BBFCADE
python locale_machine_verifier.py --key ABFBBBB
```

The generator uses the neutral key `ABFCADE` and writes `fixtures/demo_answers.txt`. The expected and observed demo result is `Transcript parity: True` with matching digests. Its first three positions admit 2, 1, and 2 letters from `ABCDEF` along that candidate path. At position 4, the state is zero and all six letters fit each remaining line. `BBFCADE` changes the informative prefix and is rejected. `ABFBBBB` changes only the tail and still reproduces the answer bytes. That last check demonstrates the specific ambiguity created by the absorbing state.

For a different transform, replace the JSON form table, both moduli, field series values, question and answer files, and alphabet with values read from that program. Use `--model`, `--questions`, `--answers`, `--alphabet`, and `--key-file`. A literal `--key` is also supported for neutral demos; command-line arguments may be retained in shell history or process listings. The verifier bounds each input to 1 MiB, supports at most 5,000 positions, rejects unknown fields and ambiguous form parses, and uses no external packages.

The lab does not analyze Haskell source, discover form tables, search all possible prefix paths, or determine a secret's true tail. Its parity and profile checks validate only this synthetic model. A real application review would need the actual transform and its collected outputs; no production weakness or detection accuracy is claimed here.
