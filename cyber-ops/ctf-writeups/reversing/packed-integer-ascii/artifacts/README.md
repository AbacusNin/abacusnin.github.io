# Packed-integer ASCII: decoder and static triage

These files use a synthetic five-integer sample. They contain no original challenge integers, location, time, or flag. The decoder reconstructs text; the scanner gives an analyst a lead when a Python source file contains a literal array of 64-bit integers that unpack to mostly printable ASCII.

## Run the demonstration

From this folder:

```sh
python -B int_unpack_decode.py --file ../fixtures/sample_packed_ints.txt --auto
python -B packed_ascii_triage.py ../fixtures/synthetic_packed_source.py
python -B packed_ascii_triage.py ../fixtures/benign_numeric_source.py
python -B packed_ascii_triage.py ../fixtures/near_miss_utf16_source.py
python -B test_packed_ascii.py
```

The decoder prints both byte orders with ASCII text where decoding succeeds, plus hex bytes. The big-endian view of the sample reads `Sample meeting place and time go here`; the little-endian view is printable but garbled. The scanner reports one candidate in `synthetic_packed_source.py` and none in the benign and UTF-16 near-miss files. The scanner does not choose an endian winner from readability alone.

## Input and output

`int_unpack_decode.py` takes decimal integers as arguments or from `--file`. Defaults: eight bytes per integer, big-endian, truncate at the first null. `--auto` shows both byte orders; `--width` accepts 1-16 and `--keep-null` retains padding. It bounds file size at 1 MB, input count at 4096, and each value to the selected unsigned width. It outputs JSON to standard output and does not execute or modify an input file.

`packed_ascii_triage.py` takes one UTF-8 Python source file up to 2 MB. It uses `ast.parse` to inspect literal lists and tuples of 3-4096 unsigned 64-bit integers. For both byte orders it measures the printable fraction before the first null and reports candidates with at least 16 bytes, at least one letter, and a printable fraction of 0.95 or higher. Its JSON output gives the file name, line, integer count, plausible byte orders, printable ratios, and null presence. It does not emit the decoded plaintext by default. No file is imported or executed.

## Sensor and response context

The sensor is a collected Python source file, such as an attachment or script already acquired for authorized analysis. Required fields are file bytes and path; the analyst should add collection source, hash, timestamp, and case ID in their own evidence system. A candidate is a triage lead. Review how the program uses the array, decode it safely, and decide whether the content matters. If it came from a live endpoint, preserve the file and acquisition context before changing or blocking anything.

This is intentionally narrow. It misses computed arrays, values spread across expressions, alternate widths, UTF-16, compressed or encrypted data, and non-Python carriers. Benign serialization can trigger it. The synthetic fixtures and local tests check code behavior only; no malware corpus, endpoint integration, detection accuracy estimate, YARA validation, or production sensor has been tested.
