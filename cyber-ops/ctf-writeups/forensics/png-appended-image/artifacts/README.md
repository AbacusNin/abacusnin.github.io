# PNG trailing-data lab

`trailing_data_detector.py` reads one local PNG, walks length-prefixed chunks to the first valid `IEND`, checks each chunk CRC, and reports bytes after that boundary. It looks in the trailing region for a complete second PNG with or without its eight-byte signature. A signature-stripped stream is repaired only after its chunks pass the same checks. The tool does not run embedded content or decode pixel data.

From the page directory:

```sh
python artifacts/trailing_data_detector.py fixtures/sample_appended.png --out recovered
python -m unittest -v artifacts/test_trailing_data_detector.py
```

The sample is invented. Its first image is a plain carrier. The second image visibly says `SAMPLE TEXT`; no challenge flag is present. A short ASCII note follows the second image. The expected report is in [`../fixtures/expected_report.json`](../fixtures/expected_report.json). The tests build clean, malformed, and marker-only cases in memory. The scanner uses only Python's standard library. Pillow was used to make and visually verify the sample; it is not a runtime requirement.

Input is capped at 16 MB, 10,000 chunks per stream, and 64 candidate signatures. This is a focused PNG inspection aid, not a complete PNG conformance validator. It checks framing, chunk CRCs, `IHDR` first, at least one `IDAT`, and `IEND` last in each carved stream; it does not decompress every image, enforce all chunk-order constraints, inspect files inside archives, or judge whether trailing data is malicious. Carved files are written only to the requested output directory and existing names are never overwritten. Treat output previews as potentially sensitive when scanning private material.

`png_trailing_data.yar` is a narrow, triage-only candidate for a second, stripped `IHDR` placed immediately after a valid-looking `IEND` byte sequence. It cannot parse PNG chunk boundaries or prove that the candidate decodes. It misses intervening text and intact second signatures. No YARA engine was available for compilation or live validation here; use the Python structural check to verify any match. [The PNG specification](https://www.w3.org/TR/png-3/) defines chunk framing and the terminal `IEND` rule. [YARA's rule guide](https://yara.readthedocs.io/en/latest/writingrules.html) documents indexed match offsets and the `for` form used in the rule.
