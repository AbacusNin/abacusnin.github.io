# RF event triage lab

These files are defensive proofs of concept for reviewing a locally captured RF trace. They do not contain the challenge recording, a keyfob code, a replay tool, or a detection claim about a deployed sensor.

| File | Use |
|---|---|
| [iq_review.py](iq_review.py) | Read bounded complex64 IQ, find pulse groups, select one repeated long packet, and report its carrier and modulation clues. |
| [make_fixture.py](make_fixture.py) | Generate invented positive, beacon-only, and multi-level ASK IQ examples. |
| [test_lab.py](test_lab.py) | Run the positive, benign, and near-miss checks. |

Python 3 with NumPy is required. Run from this directory:

```sh
python -m unittest -v test_lab.py
python make_fixture.py example.c64 --kind positive
python iq_review.py example.c64 --sample-rate 200000 --tune-hz 433920000
```

The invented positive example has two identical 28-pulse OOK packets at the tune frequency, a periodic five-pulse beacon 40 kHz high, and a separate telemetry event 80 kHz low. The expected result is five events, one repeated long-packet candidate, OOK, and 500/1000 microsecond pulse widths. The beacon-only example has no qualifying repeated long packet. The ASK near miss keeps the repeated packet but alternates two ON amplitudes, so the reviewer must withhold the OOK label. These tests passed locally. They do not reproduce the original 20-million-sample capture.

The reviewer accepts a little-endian complex64 file up to 32 MB. Required inputs are the actual sample rate and receiver tune frequency. Its output is a candidate lead, not a device identity or security verdict. A repeated packet can come from many devices. The 5 ms event gap, 16-pulse minimum, amplitude thresholds, 5 kHz carrier bucket, and 1.2 kHz frequency-variation threshold were chosen for this clean example. Measure the noise floor and packet structure before retuning them on another sensor. Overlapping emitters, oscillator drift, low signal-to-noise ratio, clipping, pulse shaping, and a different symbol code can defeat this simple grouping.

The output's `carrier_bin_hz` is the spacing of an interpolated FFT grid. The first ON pulse supplies only about 0.5 to 1 ms of real data, so the bin spacing is **not** the measurement uncertainty or the ability to resolve neighboring emitters. For a field estimate, use a long clean carrier interval, calibrate the receiver oscillator, compare repeated events, and report uncertainty. The shortest observed pulse is also a candidate chip width; confirm a stable pulse-width comb and distinguish chip from bit duration before naming a protocol.

This lab has no transmitter or protocol decoder. To hunt real RF misuse, an authorized RF sensor needs center frequency, sample rate, calibrated timestamps, antenna location, gain, noise floor, and an approved collection policy. Endpoint process logs can only surface SDR software on monitored hosts. They cannot observe a passive receiver outside the managed fleet. An RF replay finding requires demodulated payload equality, timing context, access-controller outcomes, and knowledge of whether the system uses fixed or rolling codes. This lab makes none of those claims.
