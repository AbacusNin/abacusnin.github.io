# Game-protocol capture and egress lab

This folder holds defensive proofs of concept derived from one cleartext game-protocol CTF capture. The public pcap and flow logs are invented. They contain no challenge messages or answer.

## Capture triage

`game_capture_triage.py` accepts one little-endian classic pcap with Ethernet, IPv4, TCP, one bidirectional flow, and unencrypted, uncompressed VarInt-framed application packets. It strictly reassembles TCP without inserting zeroes into gaps, rejects conflicting overlaps, decodes the initial handshake, counts frames, and partially decodes protocol-774 clientbound `0x3F` chat packets. JSON output hides messages and UUIDs by default. `--show-chat` prints text **locally** if an authorized analyst needs to reconstruct a conversation. Treat that output as potentially sensitive.

```sh
python -B artifacts/game_capture_triage.py fixtures/sample_game.pcap
python -B artifacts/game_capture_triage.py fixtures/sample_game.pcap --show-chat
```

Inputs are bounded at 32 MB, 100,000 pcap records, and 2 MiB per application frame. The parser handles no VLAN, IPv6, IP fragmentation, TCP sequence wrap, compressed or encrypted state, multiple simultaneous flows, or full chat trailing-field/NBT validation. It does not establish a player's real identity, server configuration, malicious intent, or exfiltration. Packet ID `0x3F` is version-specific; check the negotiated version and its packet table before applying the chat decoder elsewhere. The case capture was checked with the content-hidden mode, producing the packet/frame/chat counts described in the article. The sample pcap and [expected JSON](../fixtures/expected_capture.json) validate the public method without exposing its content.

## Egress review

`game_egress_triage.py` reads normalized JSON Lines with `ts` (timezone-aware ISO 8601), `src_ip`, `dst_ip`, `dst_port`, `protocol`, `action`, `asset_role`, `approved_game_use` (boolean from an owned policy/asset inventory), and optional `game_handshake_verified` (boolean from a protocol-aware sensor). It flags **allowed** TCP/25565 flows from assets without an approved exception. Missing handshake evidence is labeled `unverified`, not treated as a game-protocol confirmation. The same logic can be moved into the [SPL/KQL templates](detection_queries.md) or [experimental Sigma rule](sigma_unapproved_game_egress.yml) after field mapping.

```sh
python -B artifacts/game_egress_triage.py fixtures/flow_events.jsonl
python -B artifacts/test_game_lab.py
```

The [invented flow events](../fixtures/flow_events.jsonl) include a verified-handshake lead, an approved gaming asset, an unrelated port, and a port-only lead. The [expected findings](../fixtures/expected_flow_findings.json) record the two leads. The detector caps input at 10 MB / 50,000 events. It does not infer game use from port, flow duration from repeated events, or authorization from a username or UUID. A legitimate user, test, or other service on the port may match. Scope alerts with asset ownership, change/test schedules, destination history, and actual protocol evidence.

Six local test groups cover a positive synthetic pcap, opt-in message extraction, malformed pcap and VarInt, TCP gap/conflict, benign and near-miss flow events, and invalid policy input. The Sigma YAML was parsed with pySigma. The SPL/KQL templates were not run in a SIEM; the Sigma rule was not converted for a backend. No production accuracy or false-positive rate has been measured. The [fixture builder](../fixtures/make_sample.py) regenerates the invented pcap byte for byte.
