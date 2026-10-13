# PBES2 and RSA local review tools

These are bounded proofs of concept for local keys you are authorized to inspect. The challenge key, ciphertext, wordlist, passphrase, flag, and fixture are not included here. The tests generate a throwaway RSA key at run time; they are not a replay of the challenge.

`key-recovery-flow.svg` is the static Section 13 diagram. It shows the two-stage dependency and the result boundary without requiring a Mermaid renderer.

`crack_pkcs8.py` checks up to 10,000 supplied wordlist lines by default. It reports the matching line and key type without printing the passphrase unless `--reveal` is requested. `decrypt_rsa.py` prompts for that passphrase, tries PKCS#1 v1.5 and two OAEP choices, and writes the one result matching a supplied known plaintext prefix to a new file. A padding API can return synthetic bytes for an invalid PKCS#1 v1.5 block, so a return value alone does not identify the right scheme. The prefix check is a clue, not platform verification. Read the output file as sensitive data and remove it when no longer needed.

```sh
python test_recovery.py
python crack_pkcs8.py key.pem wordlist.txt --limit 10000
python decrypt_rsa.py --key key.pem --in ciphertext.bin --out recovered.bin --expect-prefix 'FLAG{'
```

The `cryptography` package is required. The tests cover a wordlist hit, a bounded miss, PKCS#1 v1.5, OAEP-SHA256, and a block-length error. No source-specific PBKDF2 cost, production throughput, or real private key was tested. A successful encrypted-key load establishes that the password yields a parseable key; PBES2 with AES-CBC has no authentication tag.
