# Embedded Python bytecode triage

This is a defensive analysis procedure for a Python source file that appears to load serialized code objects and assign `__code__`. It is based on the checker case, where one callable acquired three different bodies. The challenge script and its embedded values are not included here.

1. Preserve the original source and record its hash and Python version claim. Work on a copy. Do not import or execute an unknown script to obtain a literal.
2. Parse the source as text or with `ast` to identify a literal byte blob, delimiters, `marshal.loads` calls, and assignments to `function.__code__`. The companion [static triage tool](static_swap_triage.py) provides a bounded, non-executing example of this first pass.
3. Save the serialized segments in their original order. Count all bytes, including duplicates. Record each segment's length and the code-object marker without printing embedded secrets publicly.
4. Treat `marshal` data as untrusted. Python's [documentation](https://docs.python.org/3/library/marshal.html) warns against loading untrusted data. If code-object inspection is necessary, use an isolated analysis environment with no network or credentials and the appropriate CPython build. Deserialization is not execution, but it is not a safe parser boundary.
5. Inspect constants, names, and locals, then disassemble under the CPython minor version that produced coherent instructions. A readable constant pool does not establish that the opcode listing is correct. Record versions tried and rejected.
6. Trace operand roles from instructions. For a comparison such as `RC4(key, input) == ciphertext`, preserve the key and ciphertext byte order and test the inversion and round trip. Check earlier format gates and, if authorized, the original checker in isolation.
7. Keep the outcome bounded: static triage, native-version disassembly, and end-to-end checker acceptance are different levels of evidence. Do not infer a malware incident, IOC, or production detection from a local puzzle.

The [RC4 helper](rc4.py) checks the standard primitive against RFC 6229. The [neutral fixture](../fixtures/rc4_sample.json) retains repeated plaintext bytes so accidental deduplication is visible. Neither asset reproduces the withheld challenge key or flag. The static triage tool can miss indirect imports, computed attribute names, and runtime-generated source; a hit is a review lead, not a malicious verdict.
