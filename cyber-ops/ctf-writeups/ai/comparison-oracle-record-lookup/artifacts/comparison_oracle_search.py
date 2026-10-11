#!/usr/bin/env python3
"""
comparison_oracle_search.py

Recover a secret from a *comparison oracle* in a logarithmic number of queries.

A comparison oracle is any endpoint that, given a candidate value, truthfully
reports where the hidden secret sorts relative to that candidate -- i.e. it
answers "the record sorts AFTER / BEFORE your candidate" or "MATCH". Such an
endpoint may refuse to disclose the secret directly yet still leak ~1 bit per
query through the ordering response, collapsing a blind keyspace search into a
logarithmic one (binary search).

This module is generic and challenge-agnostic. Supply your own `oracle`
callable and keyspace bounds. For CTF use, respect the platform's rules
(attempt caps, cooldowns) and only automate submissions where permitted.

Author: portfolio sample. No challenge-identifying values are embedded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

# Oracle response vocabulary. `oracle(candidate)` must return one of these.
AFTER = "AFTER"    # the secret sorts AFTER the candidate  -> secret > candidate
BEFORE = "BEFORE"  # the secret sorts BEFORE the candidate -> secret < candidate
MATCH = "MATCH"    # the candidate IS the secret


@dataclass
class SearchResult:
    """Outcome of a comparison-oracle search."""
    value: Optional[int]                     # matched integer, or None if not found
    queries: int                             # number of oracle calls consumed
    trace: List[Tuple[int, str]] = field(default_factory=list)  # (candidate, response)


def info_theoretic_min(lo: int, hi: int) -> int:
    """
    Lower bound on queries to distinguish one value in [lo, hi] with binary
    (two-outcome) responses: ceil(log2(size)). Computed via bit_length to avoid
    floating-point rounding at exact powers of two. For 65,536 values this is 16.
    """
    size = hi - lo + 1
    if size <= 1:
        return 1
    return (size - 1).bit_length()


def binary_search_worst_case(lo: int, hi: int) -> int:
    """
    Guaranteed worst-case queries for the midpoint binary search below over
    [lo, hi]: floor(log2(size)) + 1 == size.bit_length(). The extra probe over
    the info-theoretic minimum is spent on a boundary element. For 65,536
    values this is 17.
    """
    size = hi - lo + 1
    if size <= 1:
        return 1
    return size.bit_length()


def solve(
    oracle: Callable[[int], str],
    lo: int,
    hi: int,
    max_queries: Optional[int] = None,
) -> SearchResult:
    """
    Binary-search the inclusive integer window [lo, hi] using a comparison oracle.

    Args:
        oracle: callable taking an integer candidate and returning AFTER, BEFORE,
                or MATCH. The response describes where the SECRET sorts relative
                to the CANDIDATE (AFTER => secret is larger).
        lo, hi: inclusive bounds of the keyspace to search.
        max_queries: optional hard cap (e.g. a platform attempt budget). The
                search aborts and returns value=None if the cap is reached.

    Returns:
        SearchResult with the matched value (or None), the query count, and the
        full (candidate, response) trace.
    """
    if lo > hi:
        raise ValueError("lo must be <= hi")

    trace: List[Tuple[int, str]] = []
    queries = 0

    while lo <= hi:
        if max_queries is not None and queries >= max_queries:
            return SearchResult(value=None, queries=queries, trace=trace)

        mid = (lo + hi) // 2
        resp = oracle(mid)
        queries += 1
        trace.append((mid, resp))

        if resp == MATCH:
            return SearchResult(value=mid, queries=queries, trace=trace)
        elif resp == AFTER:        # secret > mid
            lo = mid + 1
        elif resp == BEFORE:       # secret < mid
            hi = mid - 1
        else:
            raise ValueError(f"oracle returned unexpected response: {resp!r}")

    return SearchResult(value=None, queries=queries, trace=trace)


def format_fixed_width_hex(value: int, prefix: str = "ID", width: int = 4) -> str:
    """
    Render an integer as PREFIX-XXXX uppercase hex (zero-padded).

    NOTE: fixed-width hex strings sort lexicographically in the same order as
    their integer values (ASCII '0'-'9' precede 'A'-'F', matching numeric
    order), so a string-sort comparison oracle is equivalent to a numeric one.
    Normalize case before comparing if the target echoes mixed case.
    """
    return f"{prefix}-{value:0{width}X}"


if __name__ == "__main__":
    # Self-check against the bundled mock oracle (see ../fixtures/mock_oracle.py).
    # Uses a GENERIC secret; no challenge value is referenced.
    import os
    import random
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fixtures"))
    from mock_oracle import MockComparisonOracle  # type: ignore

    LO, HI = 0x0000, 0xFFFF
    worst = binary_search_worst_case(LO, HI)
    ideal = info_theoretic_min(LO, HI)
    secret = random.randint(LO, HI)
    mock = MockComparisonOracle(secret)

    result = solve(mock, LO, HI, max_queries=worst)
    assert result.value == secret, "search failed to recover the secret"
    assert result.queries <= worst, "search exceeded the worst-case bound"
    print(f"recovered {format_fixed_width_hex(result.value)} in "
          f"{result.queries} queries (worst-case {worst}, info-min {ideal})")
