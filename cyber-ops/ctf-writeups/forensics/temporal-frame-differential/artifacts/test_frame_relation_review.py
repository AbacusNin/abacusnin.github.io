"""Synthetic logic checks: fixed-offset relation, expected repeats, and near miss."""

from pathlib import Path
import numpy as np
from frame_relation_review import scan


def run_case(frames: np.ndarray) -> dict:
    path = Path(__file__).parent / ".test_frames.gray"
    try:
        frames.tofile(path)
        return scan(path, frames.shape[2], frames.shape[1], len(frames), 256, 3)
    finally:
        path.unlink(missing_ok=True)


def test_cases() -> None:
    rng = np.random.default_rng(4)
    base = rng.integers(0, 2, (36, 16, 16), dtype=np.uint8) * 255
    positive = base.copy()
    positive[2::3] = positive[0::3]
    positive_hits = run_case(positive)["by_lag"]
    assert any(row["lag"] == 2 and row["exact"] == 12 and row["inferred_spacing"] == 3
               for row in positive_hits), positive_hits

    benign = base.copy()
    benign[1::3] = benign[0::3]  # legitimate repeated still frames
    benign_hits = run_case(benign)["by_lag"]
    assert any(row["lag"] == 1 and row["exact"] == 12 for row in benign_hits), benign_hits

    near_miss = base.copy()  # independent noise with no embedded relation
    assert run_case(near_miss)["by_lag"] == [], run_case(near_miss)["by_lag"]
    print("PASS: fixed-offset positive, benign duplicate, independent near miss")


if __name__ == "__main__":
    test_cases()
