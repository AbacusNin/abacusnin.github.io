#!/usr/bin/env python3
"""Bounded, read-only spectral triage for dual-tone PCM WAV audio."""

import argparse
import io
import json
from pathlib import Path
import wave

import numpy as np


MAX_BYTES = 16 * 1024 * 1024
MAX_FRAMES = 6_000_000


def read_pcm16(path):
    size = len(path.getbuffer()) if isinstance(path, io.BytesIO) else path.stat().st_size
    if size > MAX_BYTES:
        raise ValueError("file exceeds 16 MiB")
    source = path if isinstance(path, io.BytesIO) else str(path)
    with wave.open(source, "rb") as wav:
        rate = wav.getframerate()
        count = wav.getnframes()
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getcomptype() != "NONE":
            raise ValueError("expected uncompressed mono 16-bit PCM WAV")
        if not 8000 <= rate <= 96000 or not 100 <= count <= MAX_FRAMES:
            raise ValueError("sample rate or frame count outside bounded range")
        raw = wav.readframes(count)
    if len(raw) != count * 2:
        raise ValueError("truncated PCM data")
    return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0, rate


def analyze_samples(samples, rate, mark=1580.0, space=1420.0):
    samples = np.asarray(samples, dtype=np.float64)
    if samples.ndim != 1 or len(samples) > MAX_FRAMES or not np.isfinite(samples).all():
        raise ValueError("invalid or oversized sample array")
    if not (0 < space < mark < rate / 2 and mark - space >= 40):
        raise ValueError("invalid tone frequencies")
    width = round(rate * 0.022)
    if len(samples) < width * 4:
        raise ValueError("audio too short for alternating-tone triage")
    hop = max(1, width // 2)
    n_fft = max(8192, 1 << (width - 1).bit_length())
    freqs = np.fft.rfftfreq(n_fft, d=1 / rate)
    mark_bins = abs(freqs - mark) <= 50
    space_bins = abs(freqs - space) <= 50
    band_bins = (freqs >= 500) & (freqs <= min(3500, rate / 2))
    window = np.hanning(width)
    labels = []
    fractions = []
    for start in range(0, len(samples) - width + 1, hop):
        frame = samples[start:start + width] * window
        if np.mean(frame * frame) < 1e-7:
            continue
        power = abs(np.fft.rfft(frame, n=n_fft)) ** 2
        total = float(power[band_bins].sum())
        if total <= 0:
            continue
        mark_power = float(power[mark_bins].sum())
        space_power = float(power[space_bins].sum())
        fractions.append(min(1.0, (mark_power + space_power) / total))
        labels.append(1 if mark_power > space_power else 0)
    if not labels:
        return {"candidate": False, "windows": 0, "dual_tone_fraction": 0.0,
                "median_tone_energy_fraction": 0.0, "transitions": 0}
    mark_count = sum(labels)
    space_count = len(labels) - mark_count
    transitions = sum(a != b for a, b in zip(labels, labels[1:]))
    dual = min(mark_count, space_count) / len(labels)
    concentration = float(np.median(fractions))
    return {
        "candidate": len(labels) >= 8 and dual >= 0.15 and concentration >= 0.55 and transitions >= 3,
        "windows": len(labels),
        "dual_tone_fraction": round(dual, 3),
        "median_tone_energy_fraction": round(concentration, 3),
        "transitions": transitions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--mark", type=float, default=1580)
    parser.add_argument("--space", type=float, default=1420)
    args = parser.parse_args()
    try:
        samples, rate = read_pcm16(args.wav)
        result = analyze_samples(samples, rate, args.mark, args.space)
    except (OSError, ValueError, wave.Error) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    print("Triage only: a dual-tone match does not prove ITA2 content or malicious use.")


if __name__ == "__main__":
    main()
