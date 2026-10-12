from contextlib import redirect_stdout
from hashlib import sha256
from io import StringIO
from pathlib import Path
from unittest.mock import patch
import json
import unittest

import challenge_solver as solver
from challenge_solver import crack_seed, java_shuffle_perm, lcg_step
from session_sequence import load_events, review


HERE = Path(__file__).parent


class LabTests(unittest.TestCase):
    def test_prng_state_recovery_and_partition(self):
        leaked_state = 0x123456789ABC
        board_state = lcg_step(leaked_state)
        permutation = java_shuffle_perm(board_state)
        self.assertEqual(crack_seed(leaked_state >> 16, permutation), leaked_state)
        groups = [set() for _ in range(4)]
        for shuffled_position, original_position in enumerate(permutation):
            groups[original_position // 4].add(shuffled_position)
        self.assertEqual(sorted(map(len, groups)), [4, 4, 4, 4])

    def test_sequence_triage(self):
        findings = review(load_events(HERE / "fixtures/events.jsonl"))
        self.assertEqual({row["session_id"] for row in findings}, {"case", "fast-client"})
        self.assertEqual({row["submissions"] for row in findings}, {4})

    def test_without_state_read(self):
        events = load_events(HERE / "fixtures/events.jsonl")
        findings = review([row for row in events if row["operation"] != "getFragment"])
        self.assertEqual([row["session_id"] for row in findings], ["fast-client"])

    def test_complete_client_on_synthetic_protocol(self):
        game = {"groups": [
            {"theme": "A", "words": ["ALPHA ONE", "ALPHA TWO", "ALPHA THREE", "ZULU-ONE"]},
            {"theme": "B", "words": ["BRAVO ONE", "BRAVO TWO", "BRAVO THREE", "BRAVO FOUR"]},
            {"theme": "C", "words": ["CHARLIE ONE", "CHARLIE TWO", "CHARLIE THREE", "CHARLIE FOUR"]},
            {"theme": "D", "words": ["DELTA ONE", "DELTA TWO", "DELTA THREE", "DELTA FOUR"]},
        ]}

        class SyntheticConn:
            def __init__(self, host, port):
                self.responses = []
                self.state = 0x123456789ABC
                self.round = 0
                self.found = set()
                self.board = []

            def next_board(self):
                self.round += 1
                self.state = lcg_step(self.state)
                words, groups = solver.all_words_and_groups(game)
                self.groups = groups
                if self.round >= 5:
                    words = [sha256((w + "|test-salt").encode()).hexdigest()[:12] for w in words]
                else:
                    raw_by_normalized = {
                        solver.normalize(word): word
                        for group in game["groups"] for word in group["words"]
                    }
                    words = [raw_by_normalized[word] for word in words]
                permutation = java_shuffle_perm(self.state)
                self.board = [words[pos] for pos in permutation]
                return self.board

            def send(self, **request):
                operation = request["operation"]
                if operation in ("register", "login"):
                    self.responses.append({"status": "OK"})
                elif operation == "getFragment":
                    self.responses.append({"gameId": self.state >> 16})
                elif operation == "startChallenge":
                    self.responses.append({"status": "OK", "boardWords": self.next_board()})
                elif operation == "submitProposal":
                    words = (
                        {word.lower() for word in request["words"]}
                        if self.round >= 5 else
                        {solver.normalize(word) for word in request["words"]}
                    )
                    expected = [set(group["words"]) for group in self.groups]
                    if self.round >= 5:
                        expected = [
                            {sha256((w + "|test-salt").encode()).hexdigest()[:12] for w in group["words"]}
                            for group in self.groups
                        ]
                    match = next((i for i, group in enumerate(expected) if words == group), None)
                    if match is None or match in self.found:
                        self.responses.append({"status": "ERROR", "errorMessage": "WRONG"})
                        return
                    self.found.add(match)
                    if len(self.found) == 4:
                        self.found.clear()
                        if self.round == 10:
                            self.responses.append({"status": "OK", "errorMessage": "CHALLENGE COMPLETED! Flag: TEST_ONLY"})
                        else:
                            self.responses.append({"status": "CHALLENGE_MODE", "boardWords": self.next_board()})
                    else:
                        self.responses.append({"status": "CHALLENGE_MODE"})

            def recv(self):
                return self.responses.pop(0)

            def close(self):
                pass

        output = StringIO()
        with patch.object(solver, "Conn", SyntheticConn), patch("builtins.open", return_value=StringIO(json.dumps([game]))), redirect_stdout(output):
            solver.solve("synthetic", 0, "synthetic.json")
        self.assertIn("CHALLENGE COMPLETED! Flag: TEST_ONLY", output.getvalue())


if __name__ == "__main__":
    unittest.main()
