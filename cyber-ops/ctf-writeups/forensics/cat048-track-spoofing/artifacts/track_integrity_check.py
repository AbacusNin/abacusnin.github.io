"""Offline protected-track checks for normalized, synthetic ingest events."""

import argparse
import json
from pathlib import Path


MAX_BYTES = 1024 * 1024
MAX_EVENTS = 10000
SUSPICIOUS_CLASSES = {"spoof", "hijack", "compromised"}


def _read_bounded(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"{path.name} exceeds 1 MiB")
    return path.read_text(encoding="utf-8")


def _tuple(item):
    values = tuple(item[name] for name in ("sac", "sic", "track_number"))
    if any(type(value) is not int for value in values) or not all(0 <= value <= cap for value, cap in zip(values, (255, 255, 4095))):
        raise ValueError("invalid SAC/SIC/track number")
    return values


def _mode_s(value):
    if not isinstance(value, str) or len(value) != 6 or any(ch not in "0123456789ABCDEF" for ch in value):
        raise ValueError("Mode-S address must be six uppercase hex digits")
    return value


def load_registry(path):
    source = json.loads(_read_bounded(path))
    if not isinstance(source, dict) or not isinstance(source.get("protected_tracks"), list):
        raise ValueError("registry needs protected_tracks list")
    registry = {}
    for item in source["protected_tracks"]:
        if not isinstance(item, dict) or not isinstance(item.get("allowed_peers"), list) or not item["allowed_peers"]:
            raise ValueError("track needs a nonempty allowed_peers list")
        if any(not isinstance(peer, str) or not peer for peer in item["allowed_peers"]):
            raise ValueError("allowed_peers must contain names")
        key = _tuple(item)
        if key in registry:
            raise ValueError("duplicate protected-track key")
        _mode_s(item.get("expected_mode_s"))
        registry[key] = item
    return registry


def load_events(path):
    lines = _read_bounded(path).splitlines()
    if len(lines) > MAX_EVENTS:
        raise ValueError("more than 10000 events")
    events = []
    for line in lines:
        if not line.strip():
            raise ValueError("blank event line")
        event = json.loads(line)
        if not isinstance(event, dict) or not isinstance(event.get("event_id"), str) or not event["event_id"]:
            raise ValueError("each event needs event_id")
        _tuple(event)
        _mode_s(event.get("mode_s"))
        if not isinstance(event.get("classification"), str):
            raise ValueError("each event needs classification")
        peer = event.get("authenticated_peer")
        if peer is not None and (not isinstance(peer, str) or not peer):
            raise ValueError("authenticated_peer must be a name or null")
        events.append(event)
    return events


def check(registry, events):
    findings = []
    for event in events:
        key = _tuple(event)
        protected = registry.get(key)
        if protected is None:
            continue
        reasons = []
        peer = event.get("authenticated_peer")
        if peer is None:
            reasons.append("provenance_unavailable")
        elif peer not in protected["allowed_peers"]:
            reasons.append("unexpected_authenticated_peer")
        if event["mode_s"] != protected["expected_mode_s"]:
            reasons.append("registered_identity_mismatch")
        if event["classification"].lower() in SUSPICIOUS_CLASSES:
            reasons.append("suspicious_classification")
        if reasons:
            findings.append({"event_id": event["event_id"], "track": list(key), "reasons": reasons})
    return findings


def main():
    parser = argparse.ArgumentParser(description="Check normalized protected-track events offline")
    parser.add_argument("registry", type=Path)
    parser.add_argument("events", type=Path)
    args = parser.parse_args()
    findings = check(load_registry(args.registry), load_events(args.events))
    print(json.dumps({"findings": findings, "finding_count": len(findings)}, indent=2))


if __name__ == "__main__":
    main()
