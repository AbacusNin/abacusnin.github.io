# Invisible Unicode source review lab

The files in this folder are synthetic defensive proofs of concept. They do not contain the challenge repository, decoded malicious code, destination, XOR values, or flag. The scanner operates on source **bytes** through UTF-8 decoding; it never imports or executes the files it scans.

## Run locally

From this folder:

```sh
python -B unicode_smuggling_scanner.py --show-decoded ../fixtures/sample_carrier.py
python -B unicode_smuggling_scanner.py ../fixtures/clean_source.py ../fixtures/benign_unicode_source.py
python -B unicode_smuggling_scanner.py --show-decoded ../fixtures/benign_emoji_tags.py
python -B test_unicode_smuggling.py
yara invisible_unicode.yar ../fixtures/sample_carrier.py
```

The positive scanner run exits 1 by design and reports 20 Tag characters, which occupy 80 UTF-8 bytes. Its decoded ASCII is the harmless placeholder `print("review only")`. The clean and visible-Unicode files exit 0. The emoji Tag sequence also exits 1: it is an expected benign false positive that requires context. A scan error or oversized file exits 2 so a CI job cannot mistake incomplete coverage for a clean result. The YARA command requires a separate YARA installation; it is not a Python dependency.

## Input, output, and limits

The scanner accepts a file or a directory. Directory mode reviews `.py`, `.js`, `.ts`, `.sh`, and `.md` files, skips common dependency and Git folders, and caps work at 1,000 files and 1 MB per file. It rejects unreadable UTF-8, reports SHA-256, byte size, code-point counts, up to 100 line/column hits, and contiguous printable Tag runs. Decoded text appears only with `--show-decoded`, capped at 500 characters per run. The script reports Tags, zero-width/bidi controls, word joiners/invisible operators, and embedded BOM. `--include-pua` adds private-use characters as a separate review class because font-dependent PUA rendering makes blanket blocking unreliable. A UTF-8 BOM at the start of a file is ignored as an ordinary encoding marker.

The YARA rule matches UTF-8 byte prefixes for the Tags plane and selected common invisible controls. It is a fast triage aid, not a full Unicode parser and not proof of malicious behavior. The Python scanner gives more precise code points and context. The [review checklist](invisible_unicode_review_checklist.md) covers evidence preservation, static decoding, Git attribution, legitimate use, and response. The [STIX bundle](invisible_unicode_behavior.json) shares an analytical attack pattern and a proposed course of action; it deliberately has no Indicator because a filename pattern alone cannot express the invisible characters.

## Operational use

The sensor is the raw repository source at commit or CI time. An implementation should record repository, commit SHA, path, file hash, scan version, and allowlist decision in protected build logs. Review changed files before build and preserve the original bytes. A scanner hit can come from an emoji Tag sequence, a test corpus, localization data, or private-use glyphs. Allowlist narrowly by path and reason after human inspection. A decoded command is content evidence; its presence in a Python comment alone does not prove it ran.

The local tests cover a synthetic Tag payload, clean ASCII, visible accented text, an expected benign emoji Tag match, special Tag code points, and a bidi control. The YARA rule was compiled and checked against the positive, clean, and visible-Unicode fixtures using `yara-python` 4.5.4 in a private local test environment. The STIX file passed local JSON and reference checks, but no full STIX schema validator, TAXII server, real CI runner, endpoint sensor, production telemetry, or detector accuracy study was used. Runtime correlation with decode and network behavior remains a proposal.
