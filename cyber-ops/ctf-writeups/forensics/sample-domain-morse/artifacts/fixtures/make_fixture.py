"""Make three small, neutral stereo WAVs for the sample-domain Morse lab."""

from pathlib import Path
import struct
import wave


MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..",
}


def marks(message):
    bits = []
    for word_no, word in enumerate(message.split()):
        if word_no:
            bits.extend([0] * 5)
        for letter_no, letter in enumerate(word):
            if letter_no:
                bits.extend([0] * 3)
            for mark_no, mark in enumerate(MORSE[letter]):
                if mark_no:
                    bits.append(0)
                bits.extend([1] * (1 if mark == "." else 3))
    return bits


def write_wav(path, bits, duplicate=False):
    silence = [0] * 2400
    left = silence + [12000 if bit else 0 for bit in bits] + silence
    right = left if duplicate else [0] * len(left)
    raw = b"".join(struct.pack("<hh", a, b) for a, b in zip(left, right))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(48000)
        wav.writeframes(raw)


folder = Path(__file__).resolve().parent
write_wav(folder / "sample_morse_burst.wav", marks("SAMPLE MORSE"))
write_wav(folder / "benign_click.wav", [1, 1])
write_wav(folder / "two_channel_near_miss.wav", marks("SAMPLE MORSE"), duplicate=True)
