# Screenshot translation review record

Use one row per claim that affects the answer. Preserve the original image separately with a hash and acquisition note. Do not replace the image with a translated transcript.

| Image hash and capture order | Visible time | Original-language excerpt | Literal translation | Working interpretation | Confidence and reviewer | Gap or conflict |
|---|---|---|---|---|---|---|
| SHA-256 and screenshot number | Local time plus known timezone, if any | Exact visible text or a restricted reference | Keep uncertainty visible | Claimed entity, city, or preference | Who checked and how | Missing bubble, cropped text, timestamp conflict |

Decision check:

1. Sort by in-image timestamps. Record the timezone only if the source provides it.
2. Separate what a speaker said from what the analyst infers. A stated target is evidence of intent, not proof of an attempted attack.
3. Mark gaps between captures. Do not supply dialogue for them.
4. Check any extracted IP against a current address registry before public enrichment. Keep the source mention even when the IP is a documentation example.
5. Have a second reader review answer-bearing text when the language or image is ambiguous. Record disagreement rather than silently choosing a translation.
