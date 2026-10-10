"""Tally groups from ordered check-in and value logs under an explicit FIFO assumption."""

import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def read_lookup(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"id", "block"} <= set(reader.fieldnames):
            raise ValueError("lookup needs id and block columns")
        rows = list(reader)
    lookup = {}
    for row in rows:
        entity, block = row["id"].strip(), row["block"].strip()
        if not entity or not block or entity in lookup:
            raise ValueError("lookup has an empty or duplicate id/block")
        lookup[entity] = block
    return lookup


def read_checkins(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 4:
            raise ValueError(f"malformed check-in: {line}")
        date, time, sequence, entity = fields
        rows.append((datetime.fromisoformat(f"{date}T{time}"), int(sequence), entity))
    return rows


def read_votes(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        date, rest = line.split(maxsplit=1)
        time, vote_id, party = rest.rsplit(":", 2)
        if not party:
            raise ValueError("vote has an empty party")
        rows.append((datetime.fromisoformat(f"{date}T{time}"), vote_id, party))
    return rows


def validate(lookup, checkins, votes):
    if not lookup or len(checkins) != len(votes) or len(checkins) != len(lookup):
        raise ValueError("lookup, check-in, and vote counts must match and be nonzero")
    entities = [entity for _, _, entity in checkins]
    if len(set(entities)) != len(entities) or set(entities) != set(lookup):
        raise ValueError("check-ins must contain every lookup id exactly once")
    sequences = [sequence for _, sequence, _ in checkins]
    if sequences != list(range(sequences[0], sequences[0] + len(sequences))):
        raise ValueError("check-in sequence numbers must be contiguous")
    if len({vote_id for _, vote_id, _ in votes}) != len(votes):
        raise ValueError("vote ids must be unique")
    if any(left[0] > right[0] for rows in (checkins, votes) for left, right in zip(rows, rows[1:])):
        raise ValueError("both logs must be sorted by time")
    if any(checkin[0] >= vote[0] for checkin, vote in zip(checkins, votes)):
        raise ValueError("a paired vote does not follow its check-in")


def tally(lookup, checkins, votes, target):
    counts = defaultdict(Counter)
    for (_, _, entity), (_, _, party) in zip(checkins, votes):
        counts[lookup[entity]][party] += 1
    group_sizes = Counter(lookup.values())
    if {group: sum(counts[group].values()) for group in group_sizes} != dict(group_sizes):
        raise ValueError("group totals do not match lookup sizes")
    if sum((counter for counter in counts.values()), Counter()) != Counter(party for _, _, party in votes):
        raise ValueError("party totals do not match the vote log")

    wins = 0
    for group in sorted(counts):
        counter = counts[group]
        highest = max(counter.values())
        winners = sorted(party for party, total in counter.items() if total == highest)
        winner = winners[0] if len(winners) == 1 else "TIE"
        wins += winner == target
        breakdown = ", ".join(f"{party}:{total}" for party, total in sorted(counter.items()))
        print(f"{group}: total={sum(counter.values())}, winner={winner}, {breakdown}")
    print(f"Groups won by {target!r}: {wins}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lookup", type=Path, required=True)
    parser.add_argument("--sequence", type=Path, required=True)
    parser.add_argument("--values", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--assume-fifo", action="store_true", help="Acknowledge that log order reflects voter order")
    args = parser.parse_args()
    if not args.assume_fifo:
        parser.error("the logs cannot prove FIFO voting; pass --assume-fifo to apply positional pairing")
    lookup = read_lookup(args.lookup)
    checkins = read_checkins(args.sequence)
    votes = read_votes(args.values)
    validate(lookup, checkins, votes)
    tally(lookup, checkins, votes, args.target)


if __name__ == "__main__":
    main()
