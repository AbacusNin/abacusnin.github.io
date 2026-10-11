# PNG XMP hash review tools

These are defensive proofs of concept for reviewing image metadata and demonstrating the cost of a known password grammar. They use Python 3's standard library. The fixtures contain invented passwords and hashes. They do not contain the challenge image, its digests, or recovered passwords.

## File review

`png_xmp_audit.py` accepts one local PNG path. It checks the PNG signature and chunk CRCs, reads Adobe XMP from `iTXt` chunks, and counts 128-character hexadecimal values inside `exif:UserComment`. Its default JSON reports the file SHA-256, chunk and field counts, and whether exactly three values appear in the expected hyphenated form. Exit status is 1 for a review candidate, 0 for no match, and 2 for a read or parse error. Candidate values stay out of the default output. `--show-digests` is an explicit local-analysis option that prints them.

```sh
python artifacts/png_xmp_audit.py authorized-image.png
```

The sensor is file access to PNG uploads, attachments, or stored images. A pipeline could map `sha256`, `candidate_512_bit_values`, and `three_value_pattern` into file-review events, along with its own path, owner, and collection time. The script does not collect those environmental fields or send events. It reads at most 20 MB, 10,000 chunks, and 1 MB of decompressed XMP. A 128-character value is only a **candidate 512-bit value**; the scanner cannot identify a hash algorithm or decide whether the field contains a credential. Other metadata fields, encodings, non-hex strings, and stripped metadata are outside this rule. Legitimate XMP comments can contain long hex strings, so review context and benign producers before alerting. No corpus-based precision or recall has been measured.

## Offline grammar check

`suffix_crack.py` accepts a newline-delimited wordlist and a separate file with one unsalted hexadecimal digest per line, in output order. It tries each alphabetic word with every zero-padded numeric suffix of the selected width. Each candidate digest is compared with all supplied targets in one pass. JSON reports the attempts, cap status, and recovered values in target order. This prints recovered plaintext by design; use it only with authorized synthetic or incident-response material and control the output location.

```sh
python artifacts/suffix_crack.py fixtures/sample_words.txt fixtures/sample_hashes.txt --algorithm blake2b --suffix-width 3
```

Supported algorithms are BLAKE2b, SHA-512, SHA3-512, SHA-256, SHA-384, and BLAKE2s. The default cap is one million candidates; set `--max-candidates` explicitly for larger authorized searches. The script rejects oversized inputs, invalid digest lengths, symbolic links, and unsupported grammar widths. Exit status is 0 when every target is recovered, 1 when a search finishes with unresolved targets, and 2 when the cap is hit or input fails. It does not support salts, KDF parameters, GPU processing, arbitrary password grammar, or a distributed workload. Its runtime was not benchmarked against a full dictionary.

## Local validation

```sh
python -B artifacts/test_tools.py
```

The tests cover three synthetic BLAKE2b matches, an unresolved digest, a candidate cap, uncompressed and compressed XMP, a benign value outside `UserComment`, a 127-character near miss, and a bad PNG CRC. The sample wordlist and hashes correspond to invented `ceremony042`, `vows173`, and `bouquet999`. The tools were also used to count the three 128-character `UserComment` values in the local challenge PNG without publishing those values. The original password recovery and platform submission were reported in the challenge record and were not rerun here.

For an operational trial, collect authorized images from the intended upload path, record known benign XMP producers, label seeded positives and near misses, and measure both missed cases and review load. The [metadata review checklist](metadata_review_checklist.md) gives the follow-up steps. No live pipeline integration or production accuracy claim is made here.
