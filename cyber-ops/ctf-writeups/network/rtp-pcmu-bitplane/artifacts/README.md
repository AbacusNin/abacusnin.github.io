# RTP PCMU periodicity review

`rtp_pcmu_review.py` is an offline defensive proof of concept. It inventories IPv4 UDP flows in a classic pcap, accepts RTP version 2 with static payload type 0, checks sequence/timestamp continuity, and measures byte repetition plus sparse LSB changes at a chosen period. Its JSON `review_lead` is a triage lead, not proof of steganography or exfiltration. It never emits recovered content.

Run `python -B rtp_pcmu_review.py capture.pcap --period 400`. The default period corresponds to 50 ms at PCMU's 8 kHz clock. Run synthetic tests with `python -B -m unittest test_rtp_pcmu_review.py`. The tests generate an invented capture in this folder and remove it after each case; no challenge capture or flag is shipped.

**Inputs and sensor:** classic pcap from a lawful network tap or session border controller media mirror, with plain RTP/PCMU payload visibility. Supported link types are Ethernet and raw IPv4. Other codecs, IPv6, pcapng, IP fragments, SRTP, multi-SSRC mixing, and loss-tolerant reassembly are outside this proof of concept. The script caps file size at 32 MiB, packet count at 100,000, and assembled flow bytes at 8 MiB.

**Output and mapping:** `flow.src_ip/src_port/dst_ip/dst_port` come from IPv4/UDP headers. `packets`, `payload_bytes`, `sequence_gaps`, `timestamp_gaps`, `byte_match_rate`, and `lsb_deviation_row_count` come from parsed RTP PT0 payloads. The detector requires a byte match rate of at least 0.95 and sparse nonzero LSB deviation rows. Period and threshold need a local baseline. Repetitive test tones can create false positives; distributed or keyed embedding can evade the sparse rule.

**Validation:** the local synthetic positive, benign repeating carrier, near miss with widespread changes, and malformed extension tests pass. A replay of the case capture also returned the expected 400-sample period, packet continuity, and two modified rows. No backend conversion, deployed sensor, production accuracy estimate, or maliciousness decision has been performed. Flow metadata alone cannot reveal payload bit planes. Before deployment, pair this offline lead with approved SBC signaling logs and endpoint context.

`stix-behavior-example.json` is an illustrative STIX 2.1 attack-pattern, course-of-action, and relationship bundle. It contains no actor attribution or extracted case data. JSON syntax and object references were checked locally; full STIX schema validation and TAXII interchange were not performed.
