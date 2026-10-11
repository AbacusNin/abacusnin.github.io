#!/usr/bin/env python3
"""
mock_oracle.py

A standalone mock of a *comparison oracle* for offline validation of
comparison_oracle_search.solve(). It holds a secret integer and truthfully
reports the sort relationship of that secret to any candidate, mirroring the
behavior of a kiosk/endpoint that answers "sorts AFTER / BEFORE / MATCH".

No challenge-specific secret is embedded; callers supply their own.
"""

from __future__ import annotations

AFTER = "AFTER"
BEFORE = "BEFORE"
MATCH = "MATCH"


class MockComparisonOracle:
    """Truthful comparison oracle over a single hidden integer secret."""

    def __init__(self, secret: int) -> None:
        self.secret = secret
        self.queries = 0  # how many comparisons have been asked

    def __call__(self, candidate: int) -> str:
        """Return where the secret sorts relative to the candidate."""
        self.queries += 1
        if self.secret > candidate:
            return AFTER     # the record sorts AFTER the candidate
        if self.secret < candidate:
            return BEFORE    # the record sorts BEFORE the candidate
        return MATCH


if __name__ == "__main__":
    # Exhaustive edge coverage + a random sample. Every secret must be recovered
    # within the midpoint worst-case bound, and never exceed it.
    import os
    import random
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "artifacts"))
    from comparison_oracle_search import (  # type: ignore
        solve, binary_search_worst_case, info_theoretic_min,
    )

    LO, HI = 0x0000, 0xFFFF
    worst = binary_search_worst_case(LO, HI)
    ideal = info_theoretic_min(LO, HI)

    targets = [LO, HI, LO + 1, HI - 1, (LO + HI) // 2]
    targets += [random.randint(LO, HI) for _ in range(1000)]

    observed_worst = 0
    for secret in targets:
        mock = MockComparisonOracle(secret)
        result = solve(mock, LO, HI, max_queries=worst)
        assert result.value == secret, f"missed secret {secret:#06x}"
        assert result.queries <= worst, f"over budget for {secret:#06x}"
        observed_worst = max(observed_worst, result.queries)

    print(f"PASS: {len(targets)} secrets recovered over [0x{LO:04X},0x{HI:04X}]; "
          f"observed worst-case {observed_worst} queries "
          f"(theoretical worst {worst}, info-min {ideal}).")
