# ELF trailer review

Run `python elf_trailer_review.py baseline suspect` on two files you are
authorized to analyze. The script is read-only and emits JSON with whole-file
SHA-256 values, the highest file-backed ELF extent, an exact baseline-prefix
check, and a JFIF header lead. It supports little-endian ELF64 up to 16 MiB.
It rejects extended header counts and malformed offsets rather than guessing.

The structural end is the maximum of the ELF header, program header table,
file-backed segments, section header table, and file-backed sections. SHT_NOBITS
does not consume file bytes. An unmapped tail can be legitimate application
data. A JFIF header is a triage lead, not proof that the JPEG decodes or
contains steganography. A matching prefix supports append-only modification
relative to the supplied baseline; trust in that baseline needs separate
package provenance and integrity checks.

Run `python -m unittest test_elf_trailer_review.py`. The invented tests cover
an appended JFIF lead, an unchanged file, a JPEG-like marker inside a mapped
section after the section table, and a malformed header. No challenge binary,
package signature, YARA engine, steghide extraction, OCR, or production FIM
pipeline was tested.
