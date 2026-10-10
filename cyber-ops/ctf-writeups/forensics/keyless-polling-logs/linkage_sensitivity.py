"""Compare FIFO with time-compatible ballot pairings on a tiny synthetic dataset."""

import argparse
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

from block_tally import read_checkins, read_lookup, read_votes, validate


def target_wins(lookup, checkins, votes, assignment, target):
    counts = defaultdict(Counter)
    for i, vote_index in enumerate(assignment):
        block = lookup[checkins[i][2]]
        counts[block][votes[vote_index][2]] += 1
    wins = 0
    for parties in counts.values():
        high = max(parties.values())
        winners = [party for party, count in parties.items() if count == high]
        wins += len(winners) == 1 and winners[0] == target
    return wins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--sequence", type=Path, required=True)
    parser.add_argument("--values", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--expected-counts", help="comma-separated counts expected from the synthetic fixture")
    args = parser.parse_args()

    lookup = read_lookup(args.lookup)
    checkins = read_checkins(args.sequence)
    votes = read_votes(args.values)
    validate(lookup, checkins, votes)
    if len(votes) > 8:
        parser.error("sensitivity enumeration is limited to eight rows")

    fifo = target_wins(lookup, checkins, votes, range(len(votes)), args.target)
    possible = set()
    assignments = 0
    for assignment in permutations(range(len(votes))):
        if all(checkins[i][0] < votes[j][0] for i, j in enumerate(assignment)):
            assignments += 1
            possible.add(target_wins(lookup, checkins, votes, assignment, args.target))

    observed = sorted(possible)
    print(f"Time-compatible assignments: {assignments}")
    print(f"FIFO target wins: {fifo}")
    print(f"Possible target wins without FIFO: {observed}")
    if args.expected_counts is not None:
        expected = [int(item) for item in args.expected_counts.split(",")]
        if observed != expected:
            raise SystemExit(f"FAIL: expected {expected}, observed {observed}")
        print("PASS: synthetic sensitivity expectation")


if __name__ == "__main__":
    main()
