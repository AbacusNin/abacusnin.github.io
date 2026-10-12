# Radix content triage

This is an offline defensive proof of concept for a content-inspection workflow. It reviews authorized UTF-8 text exports for lines of ten or more three-digit tokens, proposes radix candidates, and reports whether every decoded character is printable ASCII. It does not output plaintext. The included messages are invented; they are not the challenge fragments.

Run with Python 3.9 or later:

```sh
python -B test_radix_triage.py
python -B radix_triage.py synthetic_messages.txt
```

The expected output is two review leads. The first line has base 9 as its sole printable candidate. The second is ordinary decimal ASCII but also produces a printable base-9 reading, an expected false positive and reminder that a missing digit does not prove a radix. The third line includes a `9` and produces no printable candidate. The tests also check an invalid base-9 token and the Atbash round trip.

Input is a local file from a source with content visibility, such as an approved DLP export, email body, or application content audit. Flow logs and `conn.log` do not contain the body bytes needed here. Map any event to its actual source, sender, destination, time, and authorization context outside this script. It accepts at most 1 MB, 1,000 lines, and 1,000 tokens per matching line. Output JSON contains line numbers, digit sets, the lowest possible radix, printable candidates, and SHA-256 digests of decoded text; a digest is for local correlation, not evidence of safe content or trusted origin.

Treat each result as a triage lead. Numeric telemetry, decimal ASCII, and format-specific identifiers can match. No probability here is a calibrated false-positive rate. Correlate with destination, volume, business context, and policy before raising an alert. The script has no network access, SIEM integration, backend conversion, live telemetry test, or measured production accuracy. It cannot see encrypted bodies unless an authorized upstream system exposes their content.
