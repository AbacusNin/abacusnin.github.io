# Game-protocol egress query templates

These are review queries for a **normalized** network-flow table, not drop-in queries for a named vendor product. Map the fields from your firewall or endpoint network telemetry first. `ApprovedGameUse` must come from an owned exception list or asset inventory. It is not an inference from the port. `GameHandshakeVerified` is optional enrichment from a protocol-aware sensor. A destination port alone does not prove the traffic is a game protocol, and a verified game handshake does not prove command and control.

## KQL

Assumed table `GameEgress_CL`: `TimeGenerated`, `SrcIP`, `DstIP`, `DstPort`, `Protocol`, `Action`, `AssetRole`, `ApprovedGameUse`, `GameHandshakeVerified`. Every row is one allowed or denied flow. Rename the table and fields to the actual source before running.

```kql
GameEgress_CL
| where toint(DstPort) == 25565
| where tolower(tostring(Protocol)) == "tcp" and tolower(tostring(Action)) == "allow"
| where tobool(ApprovedGameUse) == false
| project TimeGenerated, SrcIP, DstIP, DstPort, AssetRole,
          GameHandshakeVerified,
          Evidence = iff(tobool(GameHandshakeVerified), "verified handshake", "port only")
```

## SPL

Assumed sourcetype `normalized_game_egress` with `src_ip`, `dst_ip`, `dst_port`, `protocol`, `action`, `asset_role`, `approved_game_use`, `game_handshake_verified`. Normalize boolean values to literal `true` or `false` during ingestion.

```spl
index=network sourcetype=normalized_game_egress dst_port=25565 protocol=tcp action=allow approved_game_use=false
| eval evidence=if(game_handshake_verified="true", "verified handshake", "port only")
| table _time src_ip dst_ip dst_port asset_role evidence
```

The [Sigma candidate](sigma_unapproved_game_egress.yml) expresses the same low-confidence port-and-policy lead. The [offline flow checker](game_egress_triage.py) tests that logic on normalized JSONL. In production, tune against known gaming users, approved test ranges, and alternate applications on the port. A chat review requires raw capture and legal/policy authority to inspect content. Preserve sensor timestamps and case context; do not calculate flow duration from the span between separate connection events.
