# Green LSB image lab

These offline tools turn the image-forensics method into a small, reproducible review exercise. Every bundled PNG is synthetic. The visible message in the positive case is `GREEN_LSB_DEMO`, and it is unrelated to the challenge answer.

## Files

- [`extract_green_lsb.py`](extract_green_lsb.py): PNG chunk/CRC check and one-channel bit-plane renderer.
- [`lsb_triage.py`](lsb_triage.py): RGB bit-plane entropy and raw-byte zlib size comparison.
- [`make_fixture.py`](make_fixture.py): deterministic generator for four invented carriers. It refuses to overwrite an existing fixture.
- [`test_lsb_lab.py`](test_lsb_lab.py): positive, benign, expected false-positive, near-miss, and container-integrity tests.
- [`../fixtures/fixture_green_lsb.png`](../fixtures/fixture_green_lsb.png): drawn message in the green bit-0 plane.
- [`../fixtures/fixture_green_lsb_extracted.png`](../fixtures/fixture_green_lsb_extracted.png): the rendered positive plane.
- [`../fixtures/benign_random.png`](../fixtures/benign_random.png): no structured bit plane.
- [`../fixtures/benign_stripes.png`](../fixtures/benign_stripes.png): harmless green stripes that still trigger the heuristic.
- [`../fixtures/near_miss_random_payload.png`](../fixtures/near_miss_random_payload.png): independently random-looking green bits that the heuristic misses.

## Run

Python 3.8 or newer and Pillow are required. From the page directory:

```sh
python -B artifacts/lsb_triage.py fixtures/fixture_green_lsb.png
python -B artifacts/extract_green_lsb.py fixtures/fixture_green_lsb.png view.png --channel g --bit 0
python -B -m unittest discover -s artifacts -p test_lsb_lab.py -v
```

The triage output names `G` as a review candidate for the positive and striped images. It returns no candidate for the random baseline or the random-looking payload. `view.png` contains the synthetic drawn text. The extractor refuses to overwrite an existing output. To regenerate the carriers in a fresh directory, run `python -B artifacts/make_fixture.py NEW_DIR`.

## Data contract and limits

The extractor takes a local 8-bit RGB or RGBA PNG and an output path, with `--channel {r,g,b,a}` and `--bit {0..7}`. It checks the PNG signature, bounded chunks, CRCs, IHDR first, IEND last, and no data after IEND. It rejects files over 25 MiB or images over 20 million pixels. It writes an 8-bit grayscale PNG containing only 0 and 255 intensity values and prints dimensions, chunk names, channel/bit, and set-pixel count. The original carrier stays untouched.

The triage tool reads the same bounded image, extracts bit 0 by default from each RGB channel, and reports the fraction of set bits, binary entropy, and zlib size of the raw 0/1 plane bytes. Its local review rule names a channel only when its compressed size is no more than one quarter of the next-smallest RGB plane. This threshold is a demonstration setting, not a calibrated detector. It does not use the on-disk PNG sizes or scan alpha. A low-compressibility ratio is a lead for visual review; it is neither proof of hidden data nor proof of malicious intent.

The striped benign image is an expected false positive. The random-looking payload is an expected miss. Palette PNGs, animated PNGs, 16-bit samples, compressed payloads, and content spread across multiple planes are outside this implementation. Operational use would need representative clean and stego images, media provenance, review of the rendered plane, threshold tuning, and privacy safeguards for any collected images. No gateway, SIEM, or production corpus has been tested.
