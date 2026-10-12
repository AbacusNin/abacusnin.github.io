# Recovery activity query templates

These templates assume a normalized `RecoveryActivity` table or index created from authorized endpoint and directory telemetry. They were not run against a SIEM. In particular, raw Windows 4662 `ObjectType` values require schema GUID resolution and a SACL before mapping them to `attribute_name=ms-FVE-RecoveryPassword`. `ms-FVE-RecoveryInformation` names an AD object, not the password attribute. The normalization layer must suppress the recovery password and raw command line before indexing these fields for hunting.

Normalized fields: `TimeGenerated`/`_time`, `kind`, `actor`, `target_id`, `attribute_name`, `approved_case`, `image`, `command_line_recovery_unlock` (boolean generated at ingestion). A true `approved_case` requires a verified ticket or workflow join, not a self-asserted process flag.

## KQL: distinct recovery objects read in 15 minutes

```kql
RecoveryActivity
| where kind == "ad_recovery_read" and attribute_name == "ms-FVE-RecoveryPassword"
| where coalesce(approved_case, false) == false
| summarize DistinctTargets=dcount(target_id) by actor, bin(TimeGenerated, 15m)
| where DistinctTargets >= 3
```

## SPL: same normalized read event

```spl
index=recovery_activity kind=ad_recovery_read attribute_name="ms-FVE-RecoveryPassword"
| fillnull value=false approved_case
| where approved_case!="true"
| bin _time span=15m
| stats dc(target_id) as distinct_targets by actor, _time
| where distinct_targets>=3
```

## KQL: recovery unlock without approved case

```kql
RecoveryActivity
| where kind == "recovery_unlock" and coalesce(approved_case, false) == false
| where command_line_recovery_unlock == true
| project TimeGenerated, actor, image, target_id
```

## SPL: same normalized unlock event

```spl
index=recovery_activity kind=recovery_unlock command_line_recovery_unlock=true
| fillnull value=false approved_case
| where approved_case!="true"
| table _time actor image target_id
```

The fixed-bin SIEM queries are triage approximations of a rolling 15-minute window. Tune thresholds to the environment and verify that normal helpdesk activity is recorded with an approved case. A process match means an unlock command was invoked; it does not prove a successful unlock. Never put a 48-digit recovery password into a case title, output table, or ticket.
