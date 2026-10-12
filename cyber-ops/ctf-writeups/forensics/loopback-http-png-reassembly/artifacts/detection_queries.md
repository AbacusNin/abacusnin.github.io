# Burst-hunt query templates

The local loopback leg needs an endpoint sensor or host capture. A perimeter proxy and ordinary network flow log cannot see `127.0.0.1` traffic that never leaves the host. If a relay forwards content externally, inspect that separate observed flow; do not infer it from the loopback POSTs alone.

Normalized input fields: `TimeGenerated`/`_time`, `host`, `destination`, `path`, `method`, `body_bytes`, and `approved_service`. The last field must be joined to an independently maintained service inventory. The offline [burst hunter](post_burst_hunt.py) uses a rolling 60-second window and a 16-byte size spread. These fixed-bin queries are approximations and can split a burst across a bin boundary. They need local field mapping, a tested baseline, and access to HTTP request metadata. Neither query was executed in a SIEM.

## KQL

```kql
EndpointHttpRequests
| where method == "POST" and coalesce(approved_service, false) == false
| summarize PostCount=count(), MinBytes=min(body_bytes), MaxBytes=max(body_bytes)
    by host, destination, path, bin(TimeGenerated, 1m)
| where PostCount >= 3 and MaxBytes - MinBytes <= 16
| project TimeGenerated, host, destination, path, PostCount, MinBytes, MaxBytes
```

## SPL

```spl
index=endpoint_http method=POST
| fillnull value=false approved_service
| where approved_service!="true"
| bin _time span=1m
| stats count as post_count min(body_bytes) as min_bytes max(body_bytes) as max_bytes by host destination path _time
| where post_count>=3 AND max_bytes-min_bytes<=16
```

The three-request threshold is deliberately small for the invented fixture. Production thresholds should reflect each host role and approved application. Similar sizes and a repeated URI are a review lead, not proof of exfiltration. Do not put response bodies or carved images into a general logging index.
