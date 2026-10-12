"""Synthetic, dependency-free reproduction of the partial keystream leak."""

from __future__ import annotations

import random
import string


def reverse_bits(value: int) -> int:
    return int(f"{value:08b}"[::-1], 2)


def child_block(parent: bytes, rng: random.Random) -> bytes:
    output = bytearray()
    for value in parent:
        high = sum(
            (((value >> (2 * i)) & 1) ^ ((value >> (2 * i + 1)) & 1))
            << (7 - i)
            for i in range(4)
        )
        output.append(high + rng.getrandbits(4))
    return bytes(output)


def candidates(parent_ct: int, child_ct: int, secret_ct: int, *, range_filter: bool) -> set[int]:
    """Recover possible secret bytes from two lowercase cover bytes at one position."""
    known = ((parent_ct ^ 0x60) & 0xE0)
    parities = ((child_ct ^ 0x60) >> 5) & 7
    b5 = (known >> 5) & 1
    b4 = b5 ^ (parities & 1)
    known |= b4 << 4
    results: set[int] = set()
    for b0 in (0, 1):
        for b2 in (0, 1):
            b1 = b0 ^ ((parities >> 2) & 1)
            b3 = b2 ^ ((parities >> 1) & 1)
            key = known | (b3 << 3) | (b2 << 2) | (b1 << 1) | b0
            cover_byte = parent_ct ^ key
            if range_filter and not (ord("a") <= cover_byte <= ord("z")):
                continue
            results.add(secret_ct ^ reverse_bits(key))
    return results


def run_trial(seed: int, length: int = 25) -> dict[str, int]:
    rng = random.Random(seed)  # Reproducible toy instance; never a production key source.
    key = rng.randbytes(length)
    cover = "".join(rng.choices(string.ascii_lowercase, k=2 * length)).encode("ascii")
    secret = (b"FLAG{" + b"x" * (length - 6) + b"}")
    child = child_block(key, rng)
    cover_ct = bytes(a ^ b for a, b in zip(cover, key + child))
    secret_ct = bytes(a ^ reverse_bits(b) for a, b in zip(secret, key))
    raw = filtered = 1
    for index, expected in enumerate(secret):
        parent_ct, child_ct = cover_ct[index], cover_ct[length + index]
        choices = candidates(parent_ct, child_ct, secret_ct[index], range_filter=False)
        narrowed = candidates(parent_ct, child_ct, secret_ct[index], range_filter=True)
        assert len(choices) == 4
        assert expected in choices and expected in narrowed
        raw *= len(choices)
        filtered *= len(narrowed)
    return {"positions": length, "raw_candidates": raw, "filtered_candidates": filtered}


if __name__ == "__main__":
    for trial in (0, 1, 2):
        print(f"seed={trial}: {run_trial(trial)}")
