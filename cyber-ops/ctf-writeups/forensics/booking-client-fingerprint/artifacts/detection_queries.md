# Scheduling endpoint hunt templates

These are defensive proofs of concept, not deployed detections. Both queries assume normalized web events with `timestamp`, `source_ip`, `method`, and `path`. Replace the illustrative paths and field names with the local schema. They use source IP because that is all the exercise log has. A production pipeline should use an authenticated account ID where possible and preserve the IP for context. Neither query alone proves a reservation was granted.

## Splunk SPL

This produces a *candidate list*. It groups by source and day so an overnight idle gap cannot inflate the interval variance. A two-POST same-second burst must occur within five seconds of that day's final poll. The day grouping is a practical approximation of session splitting: a session crossing midnight or a later unrelated poll will need an explicit idle-gap session ID.

```spl
index=web (path="/availability" OR path="/reserve")
| eval day=strftime(_time,"%Y-%m-%d"), is_poll=if(method="GET" AND path="/availability",1,0), is_post=if(method="POST" AND path="/reserve",1,0)
| eventstats sum(is_poll) as total_polls by source_ip day
| eventstats max(eval(if(is_poll=1,_time,null()))) as last_poll by source_ip day
| eval second=floor(_time)
| eventstats sum(is_post) as posts_in_second by source_ip day second
| eval burst=if(is_post=1 AND posts_in_second>=2 AND second>=floor(last_poll) AND second<=floor(last_poll)+5,1,0)
| eventstats max(burst) as has_burst by source_ip day
| where is_poll=1 AND total_polls>=4 AND has_burst=1
| sort 0 source_ip day _time
| streamstats current=f last(_time) as previous by source_ip day
| eval interval=if(isnotnull(previous),_time-previous,null())
| where interval>0 AND interval<=600
| stats count as interval_count avg(interval) as mean_interval stdev(interval) as sd_interval max(total_polls) as polls by source_ip day
| eval cv=sd_interval/mean_interval
| where interval_count>=3 AND cv<0.05
| table source_ip day polls mean_interval cv
```

## Microsoft Sentinel KQL

Replace `WebEvents` and its columns with the actual table mapping. `prev()` follows a sort on source and day, and the partition guard prevents an interval between two sources. This is still a day-window approximation, not a full sessionizer.

```kusto
let scoped = WebEvents
| where Path in ("/availability", "/reserve")
| extend Day=startofday(TimeGenerated), Second=bin(TimeGenerated, 1s);
let polls = scoped
| where Method == "GET" and Path == "/availability";
let terminal = polls
| summarize LastPoll=max(TimeGenerated) by SourceIp, Day;
let bursts = scoped
| where Method == "POST" and Path == "/reserve"
| summarize Posts=count() by SourceIp, Day, Second
| where Posts >= 2
| join kind=inner terminal on SourceIp, Day
| where Second between (bin(LastPoll, 1s) .. bin(LastPoll, 1s) + 5s)
| distinct SourceIp, Day;
polls
| join kind=inner bursts on SourceIp, Day
| sort by SourceIp asc, Day asc, TimeGenerated asc
| serialize PreviousIp=prev(SourceIp), PreviousDay=prev(Day), PreviousTime=prev(TimeGenerated)
| extend Interval=iff(SourceIp==PreviousIp and Day==PreviousDay, datetime_diff('second',TimeGenerated,PreviousTime), long(null))
| where Interval > 0 and Interval <= 600
| summarize Intervals=count(), Mean=avg(Interval), SD=stdev(Interval) by SourceIp, Day
| extend CV=SD/Mean
| where Intervals>=3 and CV<0.05
```

## Sensor and tuning notes

- Keep one-second or finer timestamps. The POST burst check cannot work on minute-rounded logs.
- Preserve the authenticated account ID, result or booking ID, and application outcome in protected logging. A `200` access-log status is not proof of a successful reservation.
- Legitimate auto-refresh clients can produce low interval variance. Planned integrations, health checks, and ordinary double-clicks belong in the baseline review.
- The `600` second gap, `0.05` CV threshold, and five-second poll-to-burst window come from this small exercise. Tune them on local traffic before alerting. Neither query has been run in a SIEM or measured against production traffic.
