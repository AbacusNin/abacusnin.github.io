# Host log review for a suspected scheduled implant

1. Preserve the raw audit, cron, auth, and syslog files. Record host, boot interval, acquisition time, hash, and known gaps.
2. Identify the audit rules that were enabled. Check whether `execve`, network connections, login UID, session, and relevant authentication events were actually collected.
3. Group multi-record audit events by timestamp and serial. Do not attach an `EXECVE` argument list to the nearest `SYSCALL` merely because the lines are adjacent.
4. Baseline common `comm` and `exe` values. Review dot-prefixed or writable-path executables without treating the filename alone as a verdict.
5. Trace the candidate's download command, output path, `chmod`, and root crontab edit. Record success and failure fields and the event order.
6. Read `auid`, `ses`, and `tty` on the installer actions. Treat unset `auid` on a later cron process as a gap in person attribution. Check the host's loginuid policy and any privilege escalation records.
7. Confirm the scheduled entry and actual cron execution from cron logs. Preserve the crontab itself when available.
8. Decode supported `SOCKADDR` values and compare the destination with the delivery host. Use network telemetry to determine protocol, volume, and direction before claiming exfiltration.
9. Test competing accounts and benign updaters against the same chain. A download without persistence and matching egress does not identify the installer.
10. Resolve the installer `auid` through an authenticated account roster, then corroborate the identity and access path. Record any synthetic or missing privilege step before presenting a person-level conclusion.
