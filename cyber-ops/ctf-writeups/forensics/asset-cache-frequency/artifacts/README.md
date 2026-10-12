# Asset-cache frequency lab

This is a defensive proof of concept for triaging exact-hash rarity in a bulk PNG cache. It is newly written from the case behavior and uses invented images. No acquired head-unit image, challenge archive, hidden message, or grader receipt is included.

| File | Purpose |
|---|---|
| [asset_frequency.py](asset_frequency.py) | Hash a trusted extracted directory or a fixed-size decompressed byte stream, enforce limits and PNG framing, and report rare candidates. |
| [test_asset_frequency.py](test_asset_frequency.py) | Generate valid synthetic PNGs and check a positive, a clean repeated set, a legitimate-update false lead, and malformed streams. |
| [defense-layers.svg](defense-layers.svg) | Show the proposed snapshot-to-review workflow used in Section 13. |

Python 3.10 or newer is enough. From this directory:

```sh
python -m unittest -v test_asset_frequency.py
python asset_frequency.py directory --root /path/to/trusted/extracted/tiles --min-repeat 3
```

For a fixed-size 7z member stream, first confirm member count, size, file types, extraction order, and the extractor's stdout behavior for that archive. The source case reported 12,051-byte PNG files. With an authorized local archive and a shell that supports `pipefail`, an analyst could run:

```sh
set -o pipefail
7z x -so -- /path/to/cache.7z | python asset_frequency.py stream --file-size 12051 --expected-count 1000000 --max-bytes 16000000000
```

The stream mode rejects a short record, a missing PNG signature at any boundary, extra stdout bytes, or a breached count, byte, or distinct-hash limit. It returns **ordinals**, not archive paths. It cannot prove that a separately listed archive path has the same ordinal. Verify a candidate's digest after targeted extraction before assigning a path. Check the extractor's exit status as well as this program's result. The command above was not run against the challenge archive; 7z and the archive were unavailable for this lab.

Input assumptions: trusted local bytes, correct uniform member size and count, PNG signatures at every record, and no non-PNG members in the stdout stream. The directory mode follows no symbolic links and caps each file at 1 MiB by default. Set `--max-files`, `--max-bytes`, and `--max-distinct` for the actual acquisition before a large scan. A large population of unique files can reach the distinct-hash limit. The tool does not parse PNG chunks, scan pixels, authenticate an archive, establish acquisition integrity, or decide maliciousness.

The output is JSON with file and byte counts, a frequency histogram, and up to five example locations for each hash below `--min-repeat`. A singleton is a **review lead**. Legitimate cache warming or a vendor update can create one; an emplaced tile copied many times can escape the rule. Build a reference per device model, firmware revision, map region, and acquisition state before alerting. A full snapshot is preferable to counting file-create events over a time window. No SIEM backend, production sensor, or false-positive rate was tested.

The four local tests passed. The positive invented set has three copies each of two tiles plus one new tile. The clean set has only repeated tiles. The third test deliberately labels a legitimate new tile as a review candidate, showing why the output needs a baseline and an analyst. The malformed cases stop on short, extra, and bad-signature bytes.
