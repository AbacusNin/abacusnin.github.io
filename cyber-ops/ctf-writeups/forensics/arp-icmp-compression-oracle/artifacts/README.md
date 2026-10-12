# Network relay and length-pattern triage

`network_hunt.py` is a defensive proof of concept for normalized events. It does
not parse packet captures. Run `python network_hunt.py events.jsonl --gateway
192.0.2.254` after translating sensor output into the fields shown below. Run
`python -m unittest test_network_hunt.py` for synthetic cases.

One JSON object per line uses `type`: `arp`, `icmp`, or `http`. ARP needs
`opcode`, `mac`, and claimed `ip`. ICMP needs `icmp_type`, `src`, and optional
advertised `gateway`. HTTP needs `method`, `src`, `dst`, `uri`, Unix `ts`, and
optional integer `response_bytes`. Missing required fields fail closed with a
Python error. The input cap is 1 MB, 10,000 records, and 4,096 characters per
line. Keep raw captures and parser errors outside this small helper.

The output names hypotheses. A MAC can legitimately serve several addresses.
A redirect may come from a known router. Two adjacent response lengths can arise
from ordinary application behavior, padding, framing, or packetization. Verify
the device's authorized bindings and routes, compare equal-length controlled
requests, and correlate application logs before declaring an attack.

The tests cover the full synthetic signal, a benign multi-address MAC that still
needs review, and a near miss with three response lengths and an authorized
redirect. They do not test a live sensor, SIEM backend, real traffic, or attack
success. No challenge values or secret material are included.
