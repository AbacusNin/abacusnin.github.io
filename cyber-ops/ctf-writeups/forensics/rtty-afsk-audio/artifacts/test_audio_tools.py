"""Synthetic audio and ITA2 checks; no challenge audio is used."""

import io
import unittest
import wave

import numpy as np

from audio_fsk_triage import analyze_samples, read_pcm16
from ita2_decode import decode


def frame(value):
    return [0] + [(value >> bit) & 1 for bit in range(5)] + [1, 1]


class AudioAndTextTests(unittest.TestCase):
    def test_alternating_fsk_candidate(self):
        rate = 48000
        symbol_size = round(rate / 45.45)
        frequencies = np.repeat([1580.0, 1420.0] * 20, symbol_size)
        phase = 2 * np.pi * np.cumsum(frequencies) / rate
        signal = 0.6 * np.sin(phase)
        result = analyze_samples(signal, rate)
        self.assertTrue(result["candidate"], result)

    def test_single_tone_and_noise_are_not_candidates(self):
        rate = 48000
        times = np.arange(rate) / rate
        tone = 0.6 * np.sin(2 * np.pi * 1580 * times)
        noise = np.random.default_rng(7).normal(0, 0.2, rate)
        self.assertFalse(analyze_samples(tone, rate)["candidate"])
        self.assertFalse(analyze_samples(noise, rate)["candidate"])

    def test_pcm_reader_and_rejections(self):
        rate = 8000
        with io.BytesIO() as file:
            with wave.open(file, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(rate)
                wav.writeframes(np.zeros(800, dtype="<i2").tobytes())
            raw = file.getvalue()
        samples, sample_rate = read_pcm16(io.BytesIO(raw))
        self.assertEqual((len(samples), sample_rate), (800, rate))
        with self.assertRaises(ValueError):
            analyze_samples(np.array([0.0, np.nan] * 1000), rate)

    def test_shift_mode_difference(self):
        bits = frame(27) + frame(28) + frame(3) + frame(9) + frame(3) + frame(28)
        self.assertEqual(decode(bits, "letters")["text"], "MADAM")
        self.assertNotEqual(decode(bits, "track")["text"], "MADAM")
        self.assertEqual(decode(bits, "track")["shifts"], [(1, "F")])


if __name__ == "__main__":
    unittest.main()
