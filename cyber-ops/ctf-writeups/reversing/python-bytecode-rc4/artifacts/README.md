# Defensive proofs of concept for the Python checker case

These files support historical cipher verification and safe first-pass source triage. They contain no challenge key, ciphertext, flag, or executable challenge script.

- [RC4 helper](rc4.py): standard RC4 KSA/PRGA, byte-oriented API, hex CLI, RFC 6229 self-test.
- [Neutral RC4 fixture](../fixtures/rc4_sample.json): repeated-byte plaintext and its expected ciphertext under an RFC test key.
- [Bytecode triage checklist](marshal_bytecode_triage.md): preserve, identify, version-match, and validate embedded code-object analysis.
- [Static swap triage](static_swap_triage.py): parse source with `ast` and count direct `marshal.loads` calls, literal byte lengths, and direct `__code__` assignments without executing or deserializing the source.
- [Synthetic swap cases](../fixtures/swap_cases.json): one direct match, two benign/legitimate near misses, and a string-only near miss.

Run `python rc4.py --selftest`. The expected result is a pass against the first sixteen bytes of the RFC 6229 40-bit-key stream and a repeated-byte round trip. The neutral fixture can also be checked by importing `rc4` and comparing `rc4(key, plaintext)` with its stored ciphertext.

Run `python static_swap_triage.py ../fixtures/swap_cases.json` from this directory. It should print one lead for `synthetic-code-swap` and no lead for the other three cases. The input is a JSON list containing `name`, `source`, and optional `expected_lead`; output is one JSON summary per case. The tool needs only local Python source text. It does not read host telemetry, import the target, call `marshal.loads`, or execute the code. It catches only direct syntax patterns; aliases are supported for ordinary imports, but computed attributes, indirect loader calls, and generated source can evade it. `ast.parse` is still a parser over untrusted data, so the input is capped at 1 MB and 100 cases. A lead is a review queue item, not a malware detection or production accuracy claim.

The source puzzle reportedly passed its original checker. These neutral fixtures validate only the new tools and do not replay the unavailable challenge script. RC4 is an obsolete cipher used here solely for analysis; it should not protect current data.
