# Embedded PNG review proof of concept

`xor_png_review.py` accepts an extracted byte blob, or a binary plus a separately determined `--offset` and `--size`. It reads at most 32 MiB and reviews blobs up to 16 MiB without executing the binary. Use `file`, `nm`, `strings`, and a Mach-O parser such as LIEF to establish the blob range independently; this script does not parse Mach-O symbols or verify that the selected range belongs to `__TEXT.__const`.

For keys of one to 16 bytes, it XORs the first 16 ciphertext bytes with the fixed PNG prefix, tests each periodic key candidate, decodes the selected blob, and checks PNG signature, chunk boundaries, chunk CRCs, IHDR size and dimensions, presence of IDAT and terminal IEND, and a bounded zlib stream. For longer keys, use `--candidate-key-file path` to test a separately inferred key. The program prints key length and a blob SHA-256, never the key bytes or a key hash. The optional `--output recovered.png` writes content only after structural checks and refuses to overwrite a file. Treat decoded content and key files as sensitive.

Example, using a range already confirmed by a Mach-O section and symbol walk:

```sh
python -B xor_png_review.py sample --offset 0x720 --size 0x18B4
python -B xor_png_review.py sample --offset 0x720 --size 0x18B4 --candidate-key-file local.key --output recovered.png
python -B -m unittest test_pocs.py
```

Input sensor: raw file bytes from an authorized collection. Output: a JSON review lead with the key fingerprint, blob fingerprint, candidate method, dimensions, chunk list, and bounded inflated byte count. A production adapter also needs host, path, collection time, signer, original file hash, and an independently verified section/symbol range. No EDR event alone provides the ciphertext bytes. A JPEG, archive, non-PNG payload, nonzero starting offset inside the selected blob, nonrepeating key, or key longer than 16 without a candidate will be missed. Random/compressed bytes can mimic a periodic prefix, although full structural checks reduce that chance. Structural checks do not establish that an image visually renders as expected or that the binary is malicious.

The five local tests generate invented PNG bytes and cover a short-key positive, a 17-byte-key candidate, a benign random blob, a CRC near miss, and a trailing-data rejection. They test local logic only. No challenge binary or recovered image, Mach-O parser, YARA/Sigma engine, SIEM backend, endpoint telemetry, or production false-positive corpus was tested.
