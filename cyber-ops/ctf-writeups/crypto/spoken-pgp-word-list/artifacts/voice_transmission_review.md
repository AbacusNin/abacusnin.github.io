# Review a voice-carried OpenPGP message

This checklist is for an authorized transmission that may carry data as spoken PGP Word List entries. The puzzle that motivated it had no attacker or production telemetry. The steps are a proposed operational practice, not a validated detection rule.

1. Keep the original audio and record its hash, duration, and acquisition path. Protect access because spoken contents can include private material.
2. Transcribe with timestamps. Keep raw recognition output and every manual change. Repeated or missing words shift even/odd parity, so mark the first uncertain position.
3. Obtain the complete even/odd word table from a trusted publication. Confirm its provenance and run known vectors before using it on case material.
4. Decode each word at its exact byte offset. Stop on an unknown or wrong-parity word. Resolve it from the audio rather than silently substituting a plausible word.
5. Validate armor boundaries, strict Base64, and CRC-24 where present. CRC-24 detects many transcription errors but does not identify a sender or prove packet validity.
6. Inspect packet structure with a maintained OpenPGP implementation. Decrypt only in an authorized, isolated environment with an appropriate key. Keep key material and passphrases out of transcripts, shell history, and reports.
7. Require successful decryption and the expected integrity status before relying on plaintext. An MDC protects against modification of this packet form; a valid signature, separately verified against a trusted key, would be needed for sender authentication.
8. For a suspected covert channel, document the audio source, access controls, and corroborating activity before labeling it an incident. This exercise alone supplies no actor, IOC, or production detection threshold.

The local decoder and armor checker support steps 3-5. They do not analyze audio, test signatures, decrypt packets, or establish identity.
