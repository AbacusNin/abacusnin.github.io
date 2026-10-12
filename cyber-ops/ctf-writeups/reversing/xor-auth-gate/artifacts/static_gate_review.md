# Reviewing an embedded authentication gate

Use this checklist on a binary you are authorized to inspect. It is a manual static-review process, not an automatic vulnerability scanner. The companion decoder handles a narrow byte transformation after the analyst has found and verified the gate.

1. Preserve the binary and record its source, size, cryptographic hash, and collection time. Work on a copy in an appropriate analysis environment. Do not execute an unknown binary as a shortcut to proving the gate.
2. Identify the format and architecture. Locate the input routine, any newline or NUL handling, the length check, the byte transform, and the branch that grants access. Record instruction addresses and relevant constants privately.
3. Check the data flow. Confirm that one input byte, one fixed key byte, and one table entry meet at each comparison. A nearby XOR instruction alone does not establish an authentication gate. Verify the loop covers the same number of bytes as the length gate.
4. Invert the table with the [decoder](xor_recover.py), keeping a recovered credential out of issue trackers and routine logs. The default command prints a length and SHA-256 fingerprint. Use `--reveal` only when an authorized analyst needs the text in a private session.
5. Classify the result by context. A test puzzle, checksum, or ordinary lookup table is not a production authentication failure. For a shipped access-control gate, document what resource it protects, whether the same value is shared across installations, and whether a server independently authorizes access.
6. For a confirmed product issue, give the owner enough evidence to reproduce the logic without distributing the credential broadly. Rotate or revoke affected credentials where possible. Move the trusted authorization decision and secret outside the distributed client, and review the release pipeline for reintroduced constants.

The source puzzle provided no production process or network event. This checklist does not yield an IOC, SIEM query, attack attribution, or measured detector accuracy. A build-time scanner would need product-specific data-flow rules and a benign sample set before it could serve as a gate.
