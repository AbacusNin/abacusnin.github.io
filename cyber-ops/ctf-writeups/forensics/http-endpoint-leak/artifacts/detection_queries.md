# Numeric endpoint discovery query templates

Both queries need per-request web access events and **normalized** `client`, `host`, `path`, and `status` fields. The client field must be derived through a trusted proxy chain. `path` must omit the query string, and host casing/port handling must be consistent. The `_N` suffix is specific to this case. Threshold 100 is a review starting point, not a measured production optimum. Both examples use fixed five-minute bins, which can split a real sequence across a boundary; the offline detector uses a sliding window. Both also reject a sequence if more misses arrive after its first success in the same bin, a deliberate high-precision choice that can miss real cases. Neither query proves that the response held a secret or that the client lacked authorization.

## Splunk SPL template

Map `clientip`, `host`, `uri_path`, `status`, and `_time` to your web sourcetype first. `rex` extracts the family from the path. Distinct misses, a `200`, and event order are all required. The `200` could be a different path in the same family.

Preserve the original event time before binning; otherwise both ordering fields would be reduced to the same five-minute bin value.

```spl
index=web sourcetype=access_combined
| eval event_time=_time, path=uri_path, client=clientip, code=tonumber(status)
| rex field=path "^(?<path_family>/[^?]+_)[0-9]+$"
| where isnotnull(path_family) AND (code=404 OR code=200)
| bin _time span=5m
| stats dc(eval(if(code=404,path,null()))) as distinct_misses
        max(eval(if(code=404,event_time,null()))) as last_miss
        min(eval(if(code=200,event_time,null()))) as first_success
        values(eval(if(code=200,path,null()))) as success_paths
        by client host path_family _time
| where distinct_misses>=100 AND isnotnull(first_success) AND last_miss<=first_success
```

## Microsoft Sentinel KQL template

Map `ClientIP`, `Host`, `Path`, and `Status` from your table. `make_set_if` caps collected distinct paths at 200, sufficient for the threshold of 100. Test the regex and function availability in your own cluster.

```kql
let threshold = 100;
WebAccess_CL
| extend client = tostring(ClientIP), host = tostring(Host), path = tostring(Path), code = toint(Status)
| extend path_family = extract(@"^(/[^?]+_)[0-9]+$", 1, path)
| where isnotempty(path_family) and code in (404, 200)
| summarize misses = make_set_if(path, code == 404, 200),
            last_miss = maxif(TimeGenerated, code == 404),
            first_success = minif(TimeGenerated, code == 200),
            success_paths = make_set_if(path, code == 200, 20)
            by client, host, path_family, bin(TimeGenerated, 5m)
| where array_length(misses) >= threshold and isnotnull(first_success) and last_miss <= first_success
```

Tune for authorized discovery scans, link checkers, shared client IPs, and encoded paths. Preserve the raw log records behind any finding. A production detection should use an event-time sliding window or correlation engine if five-minute bin edges cause misses.
