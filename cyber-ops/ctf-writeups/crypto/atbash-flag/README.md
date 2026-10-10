# Atbash triage sample

This page-local codec is a small proof of concept for checking an Atbash hypothesis against a supplied string. The fixture is fictional. It contains neither the challenge token nor an operational indicator.

| File | Use |
|---|---|
| `atbash_codec.py` | Reflect ASCII Latin letters across the alphabet; pass digits, braces, underscores, and other characters through. |
| `sample_atbash.txt` | Record the separate illustrative ciphertext and plaintext. |
| `representation-flow.svg` | Show the representation decision, an alternate byte-oriented route, and the checks on the Atbash candidate. |

From this directory, run:

```bash
python atbash_codec.py "uozt{zgyzhs_rh_zm_rmelofgrlm}"
```

The expected output is `flag{atbash_is_an_involution}`. Running the codec without an argument uses the same sample. It checks that reflecting the result a second time restores the input. This round trip tests the codec; every input that the codec handles will round-trip, including text that was never Atbash-encoded. Readability and the expected format supported the challenge hypothesis, and the recorded platform acceptance established that solve's outcome.

For an authorized investigation, preserve the raw string and its source context before transforming it. Record where it was found, when it was collected, and which transformation was tested. Keep any decoded result separate from the original evidence. A readable decode may justify more investigation, but this codec alone cannot identify malware, attribute an actor, or produce a reliable detection rule. It does not search for keys, handle non-Latin alphabets as letters, or decide whether Atbash is the correct interpretation of an unknown string.
