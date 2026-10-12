# Registry write hunt templates

These queries find candidate value writes. They do not prove that all six values coexist in a hive, that a process executed, or that a DNS request reached a C2 server. Inspect the host and its approved registry baseline after a hit. The offline [event reviewer](registry_event_review.py) groups a normalized export by host; it does not infer order or causation.

## Microsoft Defender advanced hunting (KQL)

Requires Defender for Endpoint data in `DeviceRegistryEvents`. Microsoft's schema documents `Timestamp`, `DeviceName`, `RegistryKey`, `RegistryValueName`, `ActionType`, and `InitiatingProcessFileName`. Supported `ActionType` values should be checked in the tenant's in-portal schema. This template filters by paired key and value name, without exposing `RegistryValueData`.

```kql
DeviceRegistryEvents
| where Timestamp > ago(30d)
| extend key = tolower(RegistryKey), value_name = tolower(RegistryValueName)
| where (key endswith @"\software\microsoft\sqmclient" and value_name in ("token", "configpath", "cachemap", "sessionmap"))
    or (key endswith @"\software\microsoft\wbem" and value_name == "sessionid")
    or (key endswith @"\software\classes\installer" and value_name == "upload")
| project Timestamp, DeviceName, ActionType, RegistryKey, RegistryValueName, InitiatingProcessFileName
| order by Timestamp desc
```

## Splunk with Sysmon fields (SPL)

Requires Sysmon Event ID 13 registry value-set events in `index=sysmon`, with `TargetObject`, `Image`, and `host` mapped as shown. Adjust index and field names to the local ingestion pipeline. The search returns candidates; inspect the full host timeline before creating an alert.

```spl
index=sysmon EventCode=13
  (TargetObject="*\SOFTWARE\Microsoft\SQMClient\Token"
   OR TargetObject="*\SOFTWARE\Microsoft\SQMClient\ConfigPath"
   OR TargetObject="*\SOFTWARE\Microsoft\SQMClient\CacheMap"
   OR TargetObject="*\SOFTWARE\Microsoft\SQMClient\SessionMap"
   OR TargetObject="*\SOFTWARE\Microsoft\Wbem\SessionId"
   OR TargetObject="*\SOFTWARE\Classes\Installer\Upload")
| table _time host Image TargetObject
| sort 0 - _time
```

Neither template was run in a SIEM backend. They are field-checked against Microsoft's documentation and the synthetic case fixture, then left for tenant-specific conversion and tuning. Registry writes may predate log retention; absence of an event does not establish absence of a value. Sysmon Event 13 needs a collection policy that includes these keys. Native Security Event 4657 requires both Audit Registry policy and a `Set Value` SACL on the key; merely enabling a broad Object Access category is insufficient.
