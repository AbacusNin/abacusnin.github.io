"""Correlate a small, read-only subset of Linux audit records by event ID."""

import ipaddress
import json
import re
import shlex
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


MAX_BYTES = 5_000_000
MAX_LINES = 50_000
MAX_EVENTS = 5_000
AUDIT_LINE = re.compile(r"\btype=([A-Z_]+)\s+msg=audit\((\d+(?:\.\d+)?):(\d+)\):\s*(.*)")
UNSET_AUID = "4294967295"


def bounded_text(path):
    with Path(path).open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"{path}: more than {MAX_BYTES} bytes")
    return data.decode("utf-8")


def parse_audit(text):
    events = {}
    for number, line in enumerate(text.splitlines(), 1):
        if number > MAX_LINES or len(line) > 10_000:
            raise ValueError("audit input exceeds line limit")
        match = AUDIT_LINE.search(line)
        if not match:
            continue
        kind, stamp, serial, payload = match.groups()
        if kind not in {"SYSCALL", "EXECVE", "SOCKADDR", "USER_CHAUTHTOK"}:
            continue
        try:
            tokens = shlex.split(payload)
        except ValueError as exc:
            raise ValueError(f"malformed audit fields on line {number}") from exc
        fields = dict(token.split("=", 1) for token in tokens if "=" in token)
        if kind == "USER_CHAUTHTOK" and "msg" in fields:
            nested = shlex.split(fields["msg"])
            fields.update(token.split("=", 1) for token in nested if "=" in token)
        event = events.setdefault((stamp, serial), {})
        if len(events) > MAX_EVENTS:
            raise ValueError(f"more than {MAX_EVENTS} audit events")
        if kind in event:
            raise ValueError(f"duplicate {kind} record for audit event {serial}")
        event[kind] = fields
    return events


def decode_sockaddr(value):
    try:
        raw = bytes.fromhex(value)
    except ValueError:
        return None
    if len(raw) < 8 or int.from_bytes(raw[:2], "little") != 2:
        return None
    return str(ipaddress.IPv4Address(raw[4:8])), int.from_bytes(raw[2:4], "big")


def args_of(event):
    fields = event.get("EXECVE", {})
    numbered = [(int(key[1:]), value) for key, value in fields.items() if re.fullmatch(r"a\d+", key)]
    return [value for _, value in sorted(numbered)]


def download(args):
    if not args or Path(args[0]).name not in {"curl", "wget"}:
        return None
    output = None
    for index, arg in enumerate(args[1:], 1):
        if arg in {"-o", "--output"} and index + 1 < len(args):
            output = args[index + 1]
        elif arg.startswith("--output="):
            output = arg.partition("=")[2]
    urls = [arg for arg in args[1:] if arg.startswith(("http://", "https://"))]
    if not output or not output.startswith("/tmp/.") or len(urls) != 1:
        return None
    host = urlsplit(urls[0]).hostname
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return None
    if not isinstance(address, ipaddress.IPv4Address):
        return None
    return output, str(address)


def cron_counts(text):
    counts = Counter()
    for number, line in enumerate(text.splitlines(), 1):
        if number > MAX_LINES or len(line) > 10_000:
            raise ValueError("cron input exceeds line limit")
        match = re.search(r"\bCRON\[\d+\]: \(root\) CMD \((/tmp/\.[^ )]+)\)", line)
        if match:
            counts[match.group(1)] += 1
    return counts


def analyze(audit_text, cron_text):
    events = parse_audit(audit_text)
    records = []
    incomplete = 0
    connections = Counter()
    confirmed_edits = set()
    for (stamp, _serial), event in events.items():
        sys_record = event.get("SYSCALL")
        args = args_of(event)
        if args and not sys_record:
            incomplete += 1
            continue
        if sys_record:
            auid = sys_record.get("auid", "")
            session = sys_record.get("ses", "")
            success = sys_record.get("success") == "yes"
            records.append((float(stamp), auid, session, args, success))
            socket = event.get("SOCKADDR", {}).get("saddr", "")
            endpoint = decode_sockaddr(socket)
            if endpoint and success:
                connections[(sys_record.get("exe", ""), endpoint[0])] += 1
        auth = event.get("USER_CHAUTHTOK", {})
        if auth.get("op") == "crontab-edit" and auth.get("res") == "success":
            confirmed_edits.add((auth.get("auid", ""), auth.get("ses", ""), float(stamp)))

    cron = cron_counts(cron_text)
    findings = []
    for start, auid, session, args, success in records:
        if not success or not auid or auid == UNSET_AUID:
            continue
        candidate = download(args)
        if not candidate:
            continue
        path, source_ip = candidate
        same_session = [(time, other) for time, user, ses, other, ok in records if ok and user == auid and ses == session and time > start]
        chmod_times = [time for time, cmd in same_session if cmd and Path(cmd[0]).name == "chmod" and path in cmd[1:]]
        cron_times = [time for time, cmd in same_session if cmd and Path(cmd[0]).name == "crontab" and cmd[1:] == ["-u", "root", "-e"]]
        ordered = any(chmod < edit for chmod in chmod_times for edit in cron_times)
        edit_confirmed = any(user == auid and ses == session and auth_time > edit for user, ses, auth_time in confirmed_edits for edit in cron_times)
        beacons = connections[(path, source_ip)]
        runs = cron[path]
        if ordered and edit_confirmed and runs >= 2 and beacons >= 2:
            findings.append({
                "auid": auid, "session": session, "path": path,
                "delivery_ip": source_ip, "beacon_count": beacons,
                "root_cron_runs": runs, "result": "correlated_persistence_and_egress",
            })
    return {"findings": findings, "unattributed_execve_events": incomplete}


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: auditd_rat_triage.py AUDIT_LOG CRON_LOG")
    try:
        result = analyze(bounded_text(sys.argv[1]), bounded_text(sys.argv[2]))
    except (UnicodeError, ValueError) as exc:
        raise SystemExit(f"invalid input: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
