# Keyless polling-log analysis files

These files demonstrate a positional join on fictional polling records and show where that join remains uncertain. They contain no real voter data or challenge answer. The accepted challenge count is withheld in the article.

| File | Purpose |
|---|---|
| `block_tally.py` | Check lookup, check-in, and vote invariants, then tally block plurality under an explicit FIFO assumption. |
| `fixtures/lookup.csv`, `fixtures/checkins.log`, `fixtures/votes.log` | Twelve-voter synthetic example; Alpha wins two of three blocks under FIFO pairing. |
| `linkage_sensitivity.py` | Enumerate time-compatible pairings for at most eight synthetic rows and report the possible target win counts. |
| `fixtures/ambiguity_lookup.csv`, `fixtures/ambiguity_checkins.log`, `fixtures/ambiguity_votes.log` | Four-voter counterexample; 24 time-compatible pairings give either zero or one Alpha block win. |
| `join-flow.svg` | Data flow with the invariant-failure stop branch and the explicit FIFO step. |

From this directory, run:

```bash
python block_tally.py --lookup fixtures/lookup.csv --sequence fixtures/checkins.log --values fixtures/votes.log --target Alpha --assume-fifo
python linkage_sensitivity.py --lookup fixtures/ambiguity_lookup.csv --sequence fixtures/ambiguity_checkins.log --values fixtures/ambiguity_votes.log --target Alpha --expected-counts 0,1
```

The first command reports two Alpha block wins in its separate three-block fixture. The second reports a FIFO count of one, 24 time-compatible assignments, and possible counts of zero or one. Both use Python's standard library. The sensitivity enumeration is capped at eight rows because possible assignments grow factorially.

The required data sources are a voter-to-block lookup, a timestamped check-in sequence with voter IDs, and a timestamped vote sequence with party labels. Both helpers reject missing or duplicate voter IDs, duplicate vote IDs, count mismatches, noncontiguous check-in sequence numbers, unsorted timestamps, and a positional vote that precedes its paired check-in. The tally also checks block sizes and global party totals. These checks catch malformed input, but a passing result does not prove that voters cast ballots in check-in order. The sensitivity tool assumes only that each paired ballot follows its check-in; it does not model booths, queues, or ballot-processing duration.

For operational log correlation, first seek a real correlation key or a documented process guarantee. Use a keyless positional join only when its assumptions are justified for that workflow, and keep uncertainty visible. Neither helper is an election audit, a vote-attribution method for real people, or a security detection rule. Do not feed personal voting records into a public demo or publish inferred individual choices.
