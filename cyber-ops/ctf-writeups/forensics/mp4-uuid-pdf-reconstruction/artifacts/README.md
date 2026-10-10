# MP4 uuid and PDF reconstruction lab

The scanner reads top-level ISO-BMFF boxes and reports each `uuid` extension payload. The guided reassembler extracts those payloads, uses an analyst-supplied order for readable PDF fragments, tries bounded permutations of compressed-stream fragments, then checks the stored stream length, zlib checksum, classic PDF cross-reference offsets, and `startxref`. The required data source is complete media-file bytes. A DLP or repository pipeline would need to retain those bytes; filenames or traffic metadata alone cannot provide this check.

Run with Python 3 from this folder:

```sh
python make_fixture.py demo-carriers
python mp4_uuid_pdf_reassemble.py scan demo-carriers
python mp4_uuid_pdf_reassemble.py reassemble demo-carriers/manifest.json demo-carriers/restored.pdf
python mp4_uuid_pdf_reassemble.py reassemble demo-carriers/wrong_order.json demo-carriers/wrong.pdf
```

The generator requires a new or empty directory. It makes fifteen small ISO-BMFF test containers holding one neutral PDF in split `uuid` payloads, plus one benign metadata carrier. These test containers are not playable video and contain no challenge media. One payload uses an extended box size; the benign box uses the to-end size form. The generated manifest records the manually established order of readable fragments and leaves three opaque stream fragments for the tool to permute.

Expected and observed local results:

| Case | Result |
|---|---|
| Scanner on sixteen test files | Sixteen `uuid` payloads; one contains `%PDF-`. The other fourteen PDF fragments lack the header signature; the benign metadata carrier is also header-free. |
| Guided reconstruction | One stream order passes zlib, stored `/Length`, xref, and `startxref` checks. The 627-byte output has SHA-256 `26db50075c6324217909e2ef22a55a9555ac5f8163e38634ada6c21240a9b11e`. It rendered as one page with `Neutral container demo`. |
| Wrong structural order | Rejected with zero valid stream orders; no output PDF is written. |

This is a forensic proof of concept and a proposed content-inspection component. A `uuid` box is a parsing lead, not an exfiltration finding. Legitimate vendor metadata can use extension boxes. Only one split fragment may carry a document header, as the fixture demonstrates. A real triage rule would need related-file grouping, a benign media baseline, and checks for other encodings. No production sensitivity or false-positive rate was measured.

The reassembler expects exactly one trailing `uuid` box per carrier, one PDF with a direct `/Length`, one LF-delimited zlib `FlateDecode` stream, and a classic single-section xref table. It does not infer readable-fragment order, parse nested boxes, support incremental PDFs or xref streams, or inspect actual video/audio. Input is bounded to 64 files of 2 MiB each for scanning; reconstruction caps combined payloads at 8 MiB, inflated content at 1 MiB, and opaque fragments at seven. These synthetic tests do not establish behavior on the fifteen playable challenge videos.
