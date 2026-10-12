"""Positive, benign, and near-miss checks for the two synthetic PoCs."""

from crypto_review import review
from keystream_lab import candidates, run_trial


VULNERABLE = '''
import random
key = random.randbytes(25)
a = encrypt(key, b"cover")
b = encrypt(reverse_bits(key), b"secret")
'''
BENIGN = '''
import random
sample = random.sample(range(20), 3)
key = secrets.token_bytes(32)
out = encrypt(key, b"data")
'''
NEAR_MISS = '''
import random
key = random.randbytes(25)
out = encrypt(key, b"one message")
'''


def main() -> None:
    assert [item["rule"] for item in review(VULNERABLE)] == [
        "weak-random-key", "possible-key-reuse-under-transform"
    ]
    assert review(BENIGN) == []
    assert [item["rule"] for item in review(NEAR_MISS)] == ["weak-random-key"]
    for seed in (0, 1, 2):
        result = run_trial(seed)
        assert result["positions"] == 25
        assert result["raw_candidates"] == 2 ** 50
        assert 1 <= result["filtered_candidates"] <= result["raw_candidates"]
    assert len(candidates(0x00, 0x20, 0x00, range_filter=True)) == 3
    print("positive, benign, near miss, 3 synthetic recovery trials, and range-filter test passed")


if __name__ == "__main__":
    main()
