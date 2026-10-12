"""Review a bounded complex64 IQ recording for repeated OOK-like events."""

import argparse
import json
from pathlib import Path

import numpy as np


MAX_BYTES = 32_000_000


def runs(mask):
    edges = np.diff(np.pad(mask.astype(np.int8), (1, 1)))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def inspect(iq, fs, tune_hz):
    if fs <= 0 or len(iq) < 1000:
        raise ValueError("Need at least 1,000 samples and a positive sample rate")
    mag = np.abs(iq)
    smooth_n = max(1, round(fs * 20e-6))
    env = np.convolve(mag, np.ones(smooth_n) / smooth_n, mode="same")
    floor = float(np.median(env))
    peak = float(np.percentile(env, 99.9))
    if peak < floor * 5:
        return {"status": "no_signal", "events": 0}
    pulse = []
    for a, b in runs(env > max(floor * 4, peak * 0.12)):
        raw_on = np.flatnonzero(mag[a:b] > peak * 0.25)
        if raw_on.size:
            start, stop = a + int(raw_on[0]), a + int(raw_on[-1]) + 1
            if stop - start >= fs * 100e-6:
                pulse.append((start, stop))
    if not pulse:
        return {"status": "no_pulses", "events": 0}

    groups = []
    for a, b in pulse:
        if not groups or a - groups[-1][-1][1] > fs * 5000e-6:
            groups.append([])
        groups[-1].append((a, b))

    events = []
    for group in groups:
        offsets = []
        widths = []
        for a, b in group:
            segment = iq[a:b]
            size = max(2048, 1 << (len(segment) - 1).bit_length())
            spectrum = np.abs(np.fft.fft(segment * np.hanning(len(segment)), n=size))
            offsets.append(float(np.fft.fftfreq(size, 1 / fs)[int(np.argmax(spectrum))]))
            widths.append(round((b - a) / fs * 1e6 / 25) * 25)
        events.append({
            "start_ms": round(group[0][0] / fs * 1000, 2),
            "carrier_offset_hz": round(float(np.median(offsets)) / 5000) * 5000,
            "pulse_count": len(group),
            "widths_us": widths,
            "spans": group,
        })

    candidates = []
    for i, left in enumerate(events):
        if left["pulse_count"] < 16:
            continue
        for right in events[i + 1:]:
            if (left["carrier_offset_hz"] == right["carrier_offset_hz"]
                    and left["widths_us"] == right["widths_us"]):
                candidates.append(left)
                break
    if len(candidates) != 1:
        return {"status": "ambiguous_target", "events": len(events),
                "repeated_packet_candidates": len(candidates)}

    target = candidates[0]
    samples = np.concatenate([iq[a:b] for a, b in target["spans"]])
    amplitudes = np.abs(samples)
    middle_fraction = float(np.mean((amplitudes > peak * 0.2) & (amplitudes < peak * 0.7)))
    # Cross-pulse boundaries have arbitrary phase; use only within-pulse samples.
    steps = [np.angle(iq[a + 11:b - 10] * np.conj(iq[a + 10:b - 11])) * fs / (2 * np.pi)
             for a, b in target["spans"] if b - a > 22]
    frequency_std = float(np.std(np.concatenate(steps)))
    if middle_fraction < 0.08 and frequency_std < 1200:
        modulation = "OOK"
    elif middle_fraction >= 0.08 and frequency_std < 1200:
        modulation = "multi-level ASK candidate"
    elif frequency_std >= 1200:
        modulation = "frequency-varying candidate"
    else:
        modulation = "ambiguous"

    a, b = target["spans"][0]
    segment = iq[a:b]
    nfft = 1 << max(12, (len(segment) * 8 - 1).bit_length())
    spectrum = np.abs(np.fft.fft(segment * np.hanning(len(segment)), n=nfft))
    offset = float(np.fft.fftfreq(nfft, 1 / fs)[int(np.argmax(spectrum))])
    return {
        "status": "candidate" if modulation == "OOK" else "review_modulation",
        "events": len(events),
        "target_carrier_hz": round(tune_hz + offset),
        "carrier_bin_hz": round(fs / nfft, 3),
        "observed_on_time_ms": round(len(segment) / fs * 1000, 3),
        "modulation": modulation,
        "middle_amplitude_fraction": round(middle_fraction, 4),
        "on_frequency_std_hz": round(frequency_std, 1),
        "pulse_width_clusters_us": sorted(set(target["widths_us"])),
        "shortest_observed_pulse_us": min(target["widths_us"]),
        "repeated_packet_pulses": target["pulse_count"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("iq_file", type=Path, help="little-endian complex64 IQ")
    parser.add_argument("--sample-rate", type=int, required=True)
    parser.add_argument("--tune-hz", type=int, required=True)
    args = parser.parse_args()
    size = args.iq_file.stat().st_size
    if size > MAX_BYTES or size % 8:
        parser.error("IQ file must be complex64 and at most 32 MB")
    iq = np.fromfile(args.iq_file, dtype="<c8")
    print(json.dumps(inspect(iq, args.sample_rate, args.tune_hz), indent=2))


if __name__ == "__main__":
    main()
