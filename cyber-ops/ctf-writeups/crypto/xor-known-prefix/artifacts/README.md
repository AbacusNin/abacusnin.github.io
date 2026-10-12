# Known-prefix XOR and encoded-string review

`xor_anchor_scan.py` is an offline proof of concept for analyzing authorized samples. It does not execute the sample or contact the network. It exposes three reusable functions: strict hex decoding, known-prefix one-byte key recovery, and scanning for one-byte XOR copies of analyst-supplied ASCII anchors. The [invented hex fixture](synthetic_cipher.hex) decodes to `FLAG{XOR_EXAMPLE}` with key `0x42`; it is not challenge evidence or a real indicator.

```sh
python -m unittest test_xor_anchor_scan.py
python xor_anchor_scan.py authorized_sample.bin --anchor lab-control.example
```

The scanner prints byte offsets, key candidates, and the anchor supplied by the analyst. It accepts local files up to 20 MB, at most 16 anchors of 6-128 bytes, and returns at most 100 matches. Review real anchors before sharing output. It excludes key zero so a plaintext match does not count as obfuscation. A match can come from benign test data, copied documentation, or an embedded string unrelated to execution. Require sample provenance and corroborating behavior before assigning an actor, C2 role, or incident severity.

The tests cover a known-prefix recovery, encoded marker positive, benign sample, one-byte near miss, wrong prefix, and malformed hex. They do not validate production accuracy. Scanning for a known anchor cannot discover unknown strings, and a sample can use a varying key or a different transform. File format, section context, and sandbox observations remain separate evidence.
