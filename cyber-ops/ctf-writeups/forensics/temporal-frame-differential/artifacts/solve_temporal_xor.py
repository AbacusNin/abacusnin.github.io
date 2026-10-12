#!/usr/bin/env python3
"""
Temporal XOR / frame-differential steganography recovery.

Recovers a glyph sequence hidden in the RELATIONSHIP between frames of an
all-intra binary-noise video. Nothing is visible in any single frame and
nothing useful appeared in the frame averages I tried. The payload exists in the XOR of frame pairs
at a fixed temporal offset.

Usage:
  python3 solve_temporal_xor.py -i static.mp4 -o out/ --width 300 --height 300

Requires: ffmpeg in PATH, numpy, pillow. ffprobe is needed if geometry is not supplied.
Tesseract is optional.
"""

import argparse, itertools, json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageFilter, ImageOps


def probe(path):
    """Read geometry from the container rather than assuming it."""
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
           "-show_entries", "stream=width,height,nb_frames,has_b_frames",
           "-of", "json", path]
    d = json.loads(subprocess.run(cmd, capture_output=True, text=True,
                                  check=True, timeout=30).stdout)
    s = d["streams"][0]
    return int(s["width"]), int(s["height"]), int(s.get("nb_frames", 0) or 0)


def extract_luma(path, w, h):
    """Decode to raw grayscale for the binary-luma comparison."""
    if w > 1024 or h > 1024 or os.path.getsize(path) > 100_000_000:
        raise ValueError("carrier exceeds this review script's size limits")
    cap = min(3000, 500_000_000 // (w * h))
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-frames:v", str(cap),
           "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True, timeout=90).stdout
    if len(raw) > 500_000_000 or len(raw) % (w * h):
        raise ValueError("decoded byte count exceeds limit or frame geometry")
    n = len(raw) // (w * h)
    if n > 3000:
        raise ValueError("too many frames for this review script")
    return np.frombuffer(raw, dtype=np.uint8).reshape(n, h, w)


def verify_bit_depth(frames, sample=4):
    """
    Confirm 1 bpp BEFORE thresholding. The claim that matters is not "0 and 255
    are common" but "the decision boundary is sparsely occupied." Check
    thresholded pair equality separately; a sample histogram proves neither
    losslessness nor the behavior of every frame.
    """
    idx = np.linspace(0, len(frames) - 1, sample).astype(int)
    c = np.bincount(frames[idx].reshape(-1), minlength=256).astype(float)
    tot = c.sum()
    return {"mid_band_112_143_pct": 100 * c[112:144].sum() / tot,
            "low_0_15_pct": 100 * c[0:16].sum() / tot,
            "high_240_255_pct": 100 * c[240:256].sum() / tot}


def frame_relatedness_scan(bits, sample_size=20000, sigma=6.0, seed=0):
    """
    Technique-agnostic linear-correlation screen over sampled frame pairs.
    It does not detect every possible relation. Map {0,1} -> {-1,+1} and take a normalized
    Gram matrix; for independent uniform bits the off-diagonal has mean 0 and
    std 1/sqrt(m) under the independent fair-bit model. The threshold is a
    screening choice; corpus false positives still need measurement.
    """
    rng = np.random.default_rng(seed)
    idx = rng.choice(bits.shape[1], min(sample_size, bits.shape[1]), replace=False)
    X = (bits[:, idx].astype(np.float32) * 2 - 1) / np.sqrt(len(idx))
    C = X @ X.T
    np.fill_diagonal(C, 0.0)
    floor = 1.0 / np.sqrt(len(idx))
    hits = [(i, j, float(C[i, j]))
            for i, j in zip(*np.where(np.abs(C) > sigma * floor)) if i < j]
    return hits, floor


def infer_geometry(hits, n_frames):
    """Derive (period, offset) from the hits instead of assuming a triplet."""
    if not hits:
        return None, None
    offs = [j - i for i, j, _ in hits]
    offset = int(np.bincount(offs).argmax())
    starts = sorted(i for i, j, _ in hits if j - i == offset)
    if len(starts) < 2:
        return None, offset
    diffs = np.diff(starts)
    period = int(np.bincount(diffs).argmax()) if len(diffs) else None
    if period and n_frames % period != 0:
        for p in range(1, 13):
            if n_frames % p == 0 and p > offset:
                period = p
                break
    return period, offset


def segment_runs(bits, period, offset):
    """
    Group-wise XOR popcount, then run-length segment on the RAW distance.
    Collapsing to a zero/nonzero predicate first would preserve only the
    blanking cadence and destroy the per-character fingerprint.
    """
    n_groups = bits.shape[0] // period
    d = [int(np.count_nonzero(bits[period * t] != bits[period * t + offset]))
         for t in range(n_groups)]
    runs = []
    for value, grp in itertools.groupby(enumerate(d), key=lambda x: x[1]):
        grp = list(grp)
        runs.append((value, grp[0][0], len(grp)))
    return d, runs


def accumulate_glyph(bits3d, period, offset, start, length, blur=2.0, rel_thresh=0.35):
    """
    Render the repeated XOR mask for OCR. In this carrier, each XOR is the
    same exact mask within a glyph run. Blurring helps OCR but does not recover
    a signal missing from a single pair.
    """
    h, w = bits3d.shape[1], bits3d.shape[2]
    acc = np.zeros((h, w), np.float32)
    for t in range(start, start + length):
        acc += (bits3d[period * t] ^ bits3d[period * t + offset])
    acc /= max(length, 1)
    im = Image.fromarray((acc * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    a = np.array(im, dtype=np.float32)
    peak = a.max() if a.max() > 0 else 1.0
    return ((a > peak * rel_thresh) * 255).astype(np.uint8)


def cross_validate(candidate, distances):
    """
    In this carrier, exact XOR masks repeat within each glyph window. A repeated
    character should map to one popcount, but different glyphs can collide.
    Brace mirrors are one plausible collision, not a uniqueness proof.

    LIMITATION (see writeup §6): this constrains REPEATED characters only.
    A character appearing exactly once is unconstrained -- the check is a
    consistency test, not a uniqueness proof.
    """
    if len(candidate) != len(distances):
        return False, ["length mismatch"]
    fwd, rev, conflicts = {}, {}, []
    for ch, dist in zip(candidate, distances):
        fwd.setdefault(dist, set()).add(ch)
        rev.setdefault(ch, set()).add(dist)
    for dist, chars in sorted(fwd.items()):
        if len(chars) > 1 and chars != {"{", "}"}:
            conflicts.append("popcount %d -> %s" % (dist, sorted(chars)))
    for ch, ds in rev.items():
        if len(ds) > 1:
            conflicts.append("char %r -> %s" % (ch, sorted(ds)))
    return not conflicts, conflicts


def ocr_glyph(mask, path):
    """OCR is a NOISY channel here; never trust it standalone (see writeup §6)."""
    im = Image.fromarray(255 - mask)
    ImageOps.expand(im, 60, 255).save(path)
    if not shutil.which("tesseract"):
        return ""
    wl = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
          "0123456789_{}!@#$%^&*")
    r = subprocess.run(["tesseract", path, "stdout", "--psm", "10",
                        "-c", "tessedit_char_whitelist=" + wl],
                       capture_output=True, text=True)
    return r.stdout.strip().replace(" ", "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True)
    ap.add_argument("-o", "--outdir", default="out")
    ap.add_argument("--sample", type=int, default=20000)
    ap.add_argument("--sigma", type=float, default=6.0)
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    if (a.width is None) != (a.height is None):
        ap.error("supply both --width and --height or neither")
    w, h = (a.width, a.height) if a.width else probe(a.input)[:2]
    frames = extract_luma(a.input, w, h)
    print("[+] %d frames of %dx%d" % (len(frames), w, h))

    depth = verify_bit_depth(frames)
    print("[+] sampled mid-band 112-143: %.3f%%  (verify pair equality separately)"
          % depth["mid_band_112_143_pct"])
    if depth["mid_band_112_143_pct"] > 5.0:
        print("[!] boundary not empty -- thresholding will inject errors")

    bits3d = (frames >= 128).astype(np.uint8)
    bits = bits3d.reshape(len(frames), -1)

    hits, floor = frame_relatedness_scan(bits, a.sample, a.sigma)
    print("[+] relatedness: %d pairs > %.1f sigma (floor %.4f)" % (len(hits), a.sigma, floor))
    if not hits:
        print("[!] no related frames under this sampled linear-correlation test")
        return 1

    period, offset = infer_geometry(hits, len(frames))
    print("[+] inferred geometry: period=%s offset=%s" % (period, offset))
    if not period:
        return 1

    d, runs = segment_runs(bits, period, offset)
    glyph_runs = [r for r in runs if r[0] != 0]
    print("[+] %d runs, %d glyph windows" % (len(runs), len(glyph_runs)))

    masks, dists, ocr = [], [], []
    for k, (dist, start, length) in enumerate(glyph_runs):
        m = accumulate_glyph(bits3d, period, offset, start, length)
        masks.append(m); dists.append(dist)
        ocr.append(ocr_glyph(m, os.path.join(a.outdir, "g%02d.png" % k)))

    cols = min(13, len(masks)) or 1
    rows = (len(masks) + cols - 1) // cols
    cell = 120
    grid = Image.new("L", (cell * cols, cell * rows), 0)
    for i, m in enumerate(masks):
        grid.paste(Image.fromarray(m).resize((cell, cell), Image.LANCZOS),
                   ((i % cols) * cell, (i // cols) * cell))
    grid.save(os.path.join(a.outdir, "glyphs.png"))

    print("[+] popcounts: %s" % dists)
    print("[+] OCR (UNRELIABLE alone): %r" % "".join(ocr))
    print("[+] %d distinct popcounts over %d glyphs -- repeated counts need visual review"
          % (len(set(dists)), len(dists)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
