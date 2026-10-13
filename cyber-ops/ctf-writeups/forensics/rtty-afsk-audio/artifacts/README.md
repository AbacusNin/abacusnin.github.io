# AFSK and ITA2 review files

These proofs of concept use local files only. The challenge WAV, exact recovered message, and platform receipt are not included. Synthetic tests establish that the tools can distinguish an alternating dual-tone fixture from a single tone or seeded noise, and show how an ITA2 FIGS shift changes the reading of the same symbol values. They do not replay the challenge or establish a production false-positive rate.

`stix_behavior_example.json` is an illustrative STIX 2.1 bundle with a training-context behavior description and a course of action. It has no indicator, actor attribution, or real IOC. It has been checked for JSON syntax and basic required fields, not against the full STIX schema. `rtty-analysis-flow.svg` diagrams the challenge path and a separate, optional defensive review; it does not show an observed exfiltration event.

`audio_fsk_triage.py` reads only bounded mono 16-bit PCM WAV files. It measures energy near user-selected mark and space frequencies in short windows, checks that both tones appear and alternate, and prints diagnostic scores. This is a candidate filter, not full demodulation or evidence of exfiltration. It requires NumPy. `ita2_decode.py` accepts an already recovered 0/1 symbol-rate bitstream and compares shift-tracking with forced letters. It does not derive those bits from a WAV file; that needs a separately validated demodulator and timing recovery.

```sh
python test_audio_tools.py
python audio_fsk_triage.py candidate.wav --mark 1580 --space 1420
python ita2_decode.py bits.txt
```

Use these on authorized captures. Review a candidate spectrogram, tone spacing, timing, framing errors, both ITA2 interpretations, and the content's context before concluding it is teleprinter data or a covert channel. The 1420/1580 Hz pair is a case value, not a reliable universal signature. WAV headers, transfer MIME types, and `.wav` extensions are broad intake filters, not IOCs.
