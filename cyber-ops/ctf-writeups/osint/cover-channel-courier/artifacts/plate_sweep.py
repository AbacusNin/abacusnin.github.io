#!/usr/bin/env python3
"""Review candidate interior signs in local footage or existing OCR text."""

import argparse
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path


# A starting pattern for invented examples. Tune against an approved plate sample.
PLATE = re.compile(r"(?<![A-Z0-9])(?:[A-Z]{1,3}[ -]?[0-9]{1,2}[ -]?[0-9]{2,4}|RM[ -]?[A-Z0-9]{2,8})(?![A-Z0-9])")


def candidates(text):
    normalized = " ".join(text.upper().split())
    return sorted(set(PLATE.findall(normalized)))


def scan_video(video, fps, max_frames):
    if not video.is_file():
        raise ValueError("video must be a local file")
    if video.stat().st_size > 500_000_000:
        raise ValueError("video exceeds the 500 MB input limit")
    rows = []
    deadline = time.monotonic() + 600
    with tempfile.TemporaryDirectory(prefix="plate-sweep-") as temp:
        frame = Path(temp) / "frame_%06d.png"
        subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(video),
             "-vf", f"fps={fps:g},scale=1920:1080:force_original_aspect_ratio=decrease",
             "-frames:v", str(max_frames), str(frame)],
            check=True, capture_output=True, timeout=180,
        )
        for image in sorted(Path(temp).glob("frame_*.png")):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("video review exceeded ten minutes")
            result = subprocess.run(
                ["tesseract", str(image), "stdout", "--psm", "11"],
                check=True, capture_output=True, text=True, timeout=min(20, remaining),
            )
            hits = candidates(result.stdout[:100_000])
            if hits:
                rows.append({"frame": image.name, "candidates": hits})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", type=Path, help="local video; requires ffmpeg and tesseract")
    source.add_argument("--ocr-text", type=Path, help="local OCR text for pattern review")
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--max-frames", type=int, default=300)
    args = parser.parse_args()
    if not 0.1 <= args.fps <= 10 or args.max_frames < 1 or args.max_frames > 1000:
        parser.error("fps must be 0.1 to 10 and max-frames must be 1 to 1000")
    if args.ocr_text:
        if args.ocr_text.stat().st_size > 1_000_000:
            parser.error("OCR text exceeds the 1 MB input limit")
        rows = [{"frame": args.ocr_text.name, "candidates": candidates(args.ocr_text.read_text(encoding="utf-8"))}]
    else:
        rows = scan_video(args.video, args.fps, args.max_frames)
    print(json.dumps({"candidate_frames": rows, "review_required": True}, indent=2))


if __name__ == "__main__":
    main()
