# SSH auth-log triage examples

These are defensive proofs of concept built from the behaviors in the case. The log fixture is invented and uses RFC 5737 documentation addresses. It is not challenge evidence.

## Offline parser

Run `python -B auth_log_triage.py synthetic_secure.log` in this directory. The script reads a local syslog file and prints service coverage, SSH password failures by account and address, closure counts, HTTP-like protocol errors, accepted logins, and addresses appearing in both failure and success records. It makes no network requests. It retains only aggregates in memory, but its JSON output contains account names and source addresses; handle output as sensitive security data. It never prints raw log messages. No temporal normalization is attempted.

The expected synthetic result has nine lines, eight `sshd` records, one `vsftpd` record, one HTTP-like mismatch, one source seen in both a failed and an accepted SSH event, and one rejected non-IP source. `unparsed_headers` is an explicit coverage bucket. Its count plus the service counts must equal the line count. The parser limits individual line length to 65,536 bytes by default, but counters grow with distinct input values; use normal file and process limits for large deployments. This is a lab parser for classic syslog headers, not a general journald or RFC 5424 parser. An `Accepted` line shows a logged authentication, but the failure/success intersection alone does not prove that an attacker took over the account.

Run `python -B -m unittest test_auth_log_triage.py`. The three tests cover the attack-like path, a benign accepted login with no preceding failure, an invalid source address, a second process without a PID, an unparsed header from `synthetic_malformed.log`, and an overlong line.

## Detection rules

`mr_ssh_failure_volume.yml` uses a Sigma event rule and a separate Sigma correlation rule. The 50-event threshold is an untuned starting value. A target backend must map `message`, `src_ip`, and `host` and support `event_count` correlations; many raw syslog ingests do not provide `src_ip` until parsing. The companion `ssh_http_probe.yml` is a single-event selection over the full message. These rules have not been converted to a backend or run on production telemetry. A matching HTTP method can come from an approved scanner or misconfigured probe, so neither rule is an automatic incident verdict.

With PyYAML installed, `python -B -m unittest test_detection_examples.py` checks the intended selections and the 50/51 boundary, including an authorized 51-event test that would still alert. The rules were also parsed with pySigma. These checks do not exercise a backend's field mappings, time windows, or correlation conversion.

For a production pipeline, compare parser coverage against raw ingest, retain both SSH and FTP service events, review success after failure with account and time context, tune for authorized automation, and protect centralized logs in transit and at rest.
