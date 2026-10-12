# Positional-shift review

This offline proof of concept reads one printable ASCII ciphertext line, at
most 4,096 bytes, and tests all 26 shift steps with two index bases. It
reports candidates whose decoded text starts with the supplied crib. It has
no network or SIEM input. It makes no maliciousness or attribution decision.

Run:

```text
python progressive_shift_review.py synthetic_ciphertext.txt --crib "flag{Pos"
python -m unittest test_progressive_shift_review.py
```

The fixture is invented text, unrelated to the challenge ciphertext. The
expected positive is absolute basis, step 1, with the printable example
`flag{Positional_Shift_Cipher_Example_Text}`. A short `flag{` crib also
matches the wrong letter-only basis, an expected false positive. The other
tests cover a benign nonmatch, a wrong-basis near miss, and invalid input.

The script prints candidate plaintext. Treat real output as sensitive and run
it in a controlled local review. A crib match is a hypothesis; check the
whole plaintext, format, and any independent result before accepting it. The
tests are synthetic logic checks, not a run against the hidden challenge
ciphertext or a production detection stream.
