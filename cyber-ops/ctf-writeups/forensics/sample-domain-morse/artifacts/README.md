# Sample-domain Morse lab

The decoder reads a short Morse-like amplitude burst in a lossless, uncompressed, 16-bit stereo PCM WAV. It compares a selected payload channel with a quiet reference channel, prints the sample span and mark/gap run list, then decodes the text. Its timing matches the case: one- or three-sample marks, with one-, three-, or five-sample gaps. The five-sample word gap is specific to this exercise.

Run from this folder with Python 3:

```sh
python fixtures/make_fixture.py
python morse_channel_decoder.py fixtures/sample_morse_burst.wav
python morse_channel_decoder.py fixtures/benign_click.wav
python morse_channel_decoder.py fixtures/two_channel_near_miss.wav
```

The generator writes three deterministic, neutral WAVs at 48 kHz. The first contains `SAMPLE MORSE` in the left channel with a silent right channel. The expected and observed result is `Text: SAMPLE MORSE`, with a 101-sample burst and a printed run list. The two-sample benign click is rejected as an unexpected loud run. The near miss repeats the valid burst in both channels and is rejected because the reference is loud. Both rejected runs exit with status 2. These checks validate this code against the synthetic files only.

For another file, select a short quiet region with `--start` and `--end` in seconds, and tune `--payload`, `--reference`, `--threshold`, and `--reference-threshold` from measured channel amplitudes. The decoder reads at most 16 MiB and expects clean integer run lengths. It does not locate weak payloads inside noisy cover audio, handle compressed audio, estimate false-positive rates, or inspect endpoint behavior. A three-character minimum suppresses trivial single-click decodes; it is a lab rule, not a validated detection threshold. Preserve the printed run list if using the output as forensic evidence.
