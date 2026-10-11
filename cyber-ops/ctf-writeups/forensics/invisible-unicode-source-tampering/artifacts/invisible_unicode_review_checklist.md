# Invisible Unicode source review

Use this checklist for a file or commit already in an authorized review scope.

1. Preserve the exact file bytes, hash, source path, commit, and collection time. Inspect a copy.
2. Run the read-only scanner on the changed files. Record its exit status: 0 means no selected characters found, 1 means review findings, 2 means incomplete scanning. A finding is a lead, not a malicious verdict.
3. Compare byte length with code-point count. A Tag character takes four UTF-8 bytes. Review the reported line and nearby code using a code-point view, not only an editor rendering.
4. If Tags encode printable ASCII, decode with `--show-decoded` in an analysis workspace. Keep the original bytes and do not run the recovered text. A decoded command proves content, not execution.
5. Inspect how the file uses those characters. Comments and strings can carry inert data unless another code path decodes or executes it. Check any importer, loader, build step, or runtime read path before claiming downstream execution.
6. Compare the parent and child commits with `git show --format=fuller --stat <commit>` and a byte-aware diff. Commit authorship and signing are provenance leads, not identity proof by themselves.
7. Decide whether the character sequence has a legitimate role, such as an internationalization test or emoji tag sequence. Document a narrow allowlist by path and reason. Do not broadly suppress all non-ASCII text.
8. If the content is malicious, contain the affected branch or artifact, identify downstream builds and consumers, and examine process or network telemetry before claiming exfiltration or second-stage execution.

The scanner is a local proof of concept. Its file-type list, size cap, Unicode ranges, and false-positive handling need review before CI deployment. The YARA rule is a byte-level triage aid and does not replace the code-point-aware scan.
