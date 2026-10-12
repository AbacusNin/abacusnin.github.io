# Offline frame-relation review

These files turn the video's frame-pair observation into an offline file-analysis proof of concept. They do not identify a malicious actor or establish that a media file carries stolen data.

## Files

- [`frame_relation_review.py`](frame_relation_review.py): scans bounded, decoded 8-bit gray frames for strong relationships at short lags. It reports hit counts, exact sampled matches, likely spacing, and first start positions as JSON.
- [`test_frame_relation_review.py`](test_frame_relation_review.py): deterministic synthetic positive, harmless repeated-frame, and independent-noise cases.
- [`solve_temporal_xor.py`](solve_temporal_xor.py): the challenge-specific full solve logic shown in the article. It can write glyph images and an OCR suggestion; treat the suggestion as a reading aid.

## Input and use

The reviewer needs the **media file content**, decoded to raw 8-bit grayscale in frame order. It does not read SIEM events. The operator supplies width, height, and frame count. For a 300x300, 1,500-frame file:

```sh
ffmpeg -v error -i input.mp4 -frames:v 1500 -pix_fmt gray -f rawvideo frames.gray
python frame_relation_review.py frames.gray --width 300 --height 300 --frames 1500 --sample 20000 --max-lag 12
python test_frame_relation_review.py
```

Confirm the geometry from a trusted media probe first. The script rejects dimensions above 1024x1024, more than 3,000 frames, raw data above 500 MB, and any byte-count mismatch. It compares sampled thresholded luma at 128. Its six-standard-deviation screen assumes independent fair bits only as a null scale; that assumption does not describe ordinary video. Review the reported lag, spacing, and actual frames before escalating.

The challenge solver requires `ffmpeg`, `ffprobe`, NumPy, Pillow, and optionally Tesseract in `PATH`. Its output images can include the challenge string. It is a reproduction aid, not a general detector or a production media parser. Run it only on authorized input.

## Verification and limits

The synthetic tests pass for a lag-two, period-three positive; a legitimate repeated-frame case also alerts; independent noise does not. The article's carrier was replayed separately: 1,500 frames, 251 zero-distance and 249 nonzero triplets, 25 nonzero glyph windows, and identical XOR masks within all 25 windows. No production media set, backend event mapping, detection rate, or false-positive rate was measured. A nonlinear embedding, a lag beyond the configured range, quantization error, or codec behavior outside this case can evade the reviewer. Its report is triage evidence, not a verdict.

For an operational trial, collect quarantined media under the organization's approved process, record file provenance and the decoder version, run the reviewer, and have an analyst inspect both the flagged pairs and benign controls. Do not ship raw media or extracted strings to an intelligence exchange solely because this heuristic fired.
