# Spoken PGP word-list verification lab

These files are synthetic defensive proofs of concept for checking a voice-transmitted byte stream. They do not contain the challenge voicemail, private key, passphrase, ciphertext, or flag. The tools perform no speech recognition, secret-key operation, network request, or message execution.

## Files and use

- `pgp_word_decoder.py` maps ordered tokens through an external 256-row `hex<TAB>even<TAB>odd` word table. It checks table completeness, duplicate words, and even/odd parity. The default output is lowercase hex; `--format ascii` prints decoded ASCII armor if every byte is ASCII. Input is a token file with one word per line or stdin. Exit 0 means decoded, exit 2 means input or parity error.
- `armor_crc_check.py` checks a legacy `PGP MESSAGE` ASCII armor wrapper, strict Base64, 64-character line wrapping, and CRC-24 if present. It prints JSON with packet byte count, SHA-256, and checksum status. Exit 0 means structurally accepted, exit 1 means CRC mismatch, exit 2 means malformed or unreadable input. Missing CRC is reported as `null`, not a pass.
- `voice_transmission_review.md` is a proposed human evidence and key-handling checklist.
- `test_tools.py` exercises the positive, parity-negative, known-vector, duplicate-table, CRC-negative, and malformed cases.

The PGP Word List itself is not bundled. Obtain and verify a complete table from the [published word list](https://philzimmermann.com/docs/PGP_word_list.pdf) before using the decoder on a real recording. The local `fixtures/synthetic_wordlist.tsv` contains artificial `even000` and `odd000` style entries for mechanics testing. The published vectors `topmost Istanbul = E582` and `miser travesty = 82E5` are checked in the tests with their real entries and synthetic filler elsewhere.

From the page folder:

```sh
python -B artifacts/pgp_word_decoder.py --wordlist fixtures/synthetic_wordlist.tsv --tokens fixtures/synthetic_words.txt
python -B artifacts/armor_crc_check.py fixtures/sample_armor.asc
python -B artifacts/armor_crc_check.py fixtures/bad_crc_armor.asc
python -B artifacts/test_tools.py
```

The first command prints `4849` (`HI`). The valid armor-shaped fixture reports eleven decoded bytes and a matching CRC. The altered fixture exits 1. Both armor fixtures contain `REVIEW ONLY` as synthetic bytes; they are **not valid OpenPGP packet streams** and cannot be decrypted. This separation keeps the wrapper check honest.

## Scope and limits

The input for the decoder is a human-reviewed word sequence and a complete trusted table, not raw audio. The input for the armor checker is a local file. The tools cap table size at 100 KB, token input at 2 MB and 100,000 words, and armor at 1 MB. They emit no network traffic. The checker does not parse OpenPGP packets, prove cryptographic integrity, verify signatures, or establish who spoke. CRC-24 is an error-detection check. A GnuPG `GOODMDC` result from a separately authorized decryption can establish message integrity for the legacy encrypted packet, but it cannot authenticate the sender.

Local validation covered six synthetic/known-vector tests. The decoder was also compared privately with a preserved 417-word corrected transcript and recovered armor. The armor checker was compared privately with the 253-byte recovered packet and its CRC-24. Those checks do not test a new speech recognizer, production audio collection, accuracy under noise, or platform acceptance.
