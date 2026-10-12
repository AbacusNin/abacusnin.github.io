# Chat indicator validity: offline proof of concept

The [IPv4 filter](reserved_ip_filter.py) checks a deliberately narrow set of documentation, benchmark, private, shared, link-local, and loopback ranges before an analyst sends addresses to public IOC enrichment. It does not contact a network service. Input is UTF-8 with one IPv4 value per line; blank lines and whole-line `#` comments are ignored. Output is tab-separated line number, normalized address, class, and suggested action. Invalid input values get a line-numbered `check_source` row without echoing untrusted text.

```sh
python -B artifacts/reserved_ip_filter.py fixtures/sample_ips.txt
cd artifacts
python -B -m unittest -v test_reserved_ip_filter.py
```

The [invented input](../fixtures/sample_ips.txt) has documentation and benchmark positives, private and local addresses, an ordinary public-address candidate, and two boundary examples. Its [expected output](../fixtures/expected_triage.tsv) is checked byte for byte by the tests. `192.0.0.9` is a globally reachable special-purpose anycast entry in the IANA registry. The filter leaves it for review, showing why a blanket "special-purpose means unreachable" rule would be wrong. `198.20.0.1` sits just beyond the benchmark block. An unclassified result never proves an address belongs to a host, is currently routed, or is malicious.

`do_not_enrich` means do not submit a known documentation or benchmark value to public IP geolocation as an external IOC. `local_context_only` means a private, shared, link-local, or loopback value may still matter inside an enterprise. Keep the original source record and provenance in either case. The [translation review record](translation_review_template.md) handles the separate language and screenshot-order problem; it is a manual worksheet, not a detection rule.

This subset is not a complete copy of the IANA registry. Update range policy from the [current IANA IPv4 special-purpose registry](https://www.iana.org/assignments/iana-ipv4-special-registry/) for a real pipeline. A production implementation needs an owner, registry refresh, IPv6 policy, source-schema mapping, audit logging, and testing on the actual enrichment workflow. No screenshot, actor handle, target, live IOC feed, SIEM, or production gateway was used in this local test.
