# Loopback HTTP framing lab

These are defensive proofs of concept for investigating a suspected local upload and hunting a similar request pattern. All fixtures are invented. No challenge capture, carved image, watermark, answer, or claimed outbound relay traffic is included.

| File | Purpose | Input and output |
|---|---|---|
| [pcap_http_reassemble.py](pcap_http_reassemble.py) | Bounded offline classic-PCAP parser, TCP stream reconstruction, HTTP/1.1 request splitter, index/tag validation, PNG CRC/structure check, and three arrival-order definitions | Local PCAP to JSON summary; optional new PNG file with `--output` |
| [post_burst_hunt.py](post_burst_hunt.py) | Rolling-window burst check over normalized endpoint HTTP events | JSONL up to 1 MiB to findings with host, destination, path, counts, and size range |
| [programmatic_post_sigma.yml](programmatic_post_sigma.yml) | Single-event candidate for programmatic HTTP POST activity | Normalized proxy-like or endpoint HTTP event; requires backend field mapping |
| [detection_queries.md](detection_queries.md) | KQL and SPL templates for repeated similar-size POSTs | Documented normalized request fields |
| [test_loopback_lab.py](test_loopback_lab.py) | Positive, near-miss, malformed, and benign checks | Generated small PCAP and JSONL fixture |
| [make_sample.py](../fixtures/make_sample.py) | Deterministic fixture generator | Generates [sample_loopback.pcap](../fixtures/sample_loopback.pcap), an invented 1x1 PNG sent in three POSTs |
| [sample_events.jsonl](../fixtures/sample_events.jsonl) | Synthetic hunt events | One alerting burst, an approved build-agent case, a GET, and a variable-size near miss |
| [visibility_boundary.svg](visibility_boundary.svg) | Observed and unobserved data paths | Static diagram used in the article |

Run from this folder with Python 3.10+:

```sh
python -m unittest test_loopback_lab.py
python pcap_http_reassemble.py ../fixtures/sample_loopback.pcap
python post_burst_hunt.py ../fixtures/sample_events.jsonl
```

The PCAP reader supports classic little- and big-endian PCAP with Ethernet or raw IPv4, unfragmented IPv4/TCP, HTTP/1.1 requests framed with `Content-Length`, and a user-supplied destination port and path. It rejects missing bytes, conflicting TCP overlaps, transfer coding, duplicate HTTP headers, incomplete bodies, duplicate or missing application indices, bad truncated SHA-256 tags, and invalid PNG CRCs. It caps input, packets, flows, requests, bodies, and output. It does not support PCAPNG, IPv6, TLS, TCP sequence wrap, multi-session chunk indices, or general HTTP transfer codings. It does not verify IP or TCP checksums; frame tags and PNG CRCs validate the reconstructed application data against accidental corruption, without authenticating it. A rejected capture needs a fuller parser and analyst review; the tool does not silently repair gaps.

The event hunter expects timezone-aware `time`, `method`, `host`, `destination`, `path`, `body_bytes`, and `approved_service`. Approval must come from a verified service inventory. Its default threshold is three POSTs within a rolling minute with a 16-byte spread. This is a demonstration threshold, not a production baseline. It does not ingest request bodies. A matching burst warrants review; it does not prove exfiltration. The Sigma file was syntax-parsed locally, but no SIEM backend conversion, live sensor run, or production accuracy measurement was performed.

Loopback requests require a host sensor or host capture. The source capture describes only the local leg. Evidence of off-host forwarding would require separate process, socket, proxy, or egress telemetry. Sysmon Event ID 3 records network connections; it does not by itself establish that a process bound a listening socket.
