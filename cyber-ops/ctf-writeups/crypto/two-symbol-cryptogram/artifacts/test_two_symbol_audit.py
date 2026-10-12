import unittest

from two_symbol_audit import analyze, check_candidate, parse_stream, segments


class TwoSymbolAuditTests(unittest.TestCase):
    def setUp(self):
        self.tokens = parse_stream("/\\ // /\\\\ \\\\ /\\\\ //")

    def test_homophonic_candidate(self):
        report = analyze(self.tokens, "banana", [3, 3])
        self.assertTrue(report["candidate"]["consistent"])
        self.assertEqual(report["token_count"], 6)
        self.assertEqual(report["distinct_token_count"], 4)
        self.assertEqual(report["proposed_segments"][0]["local_tokens"], ["/\\"])

    def test_benign_morse(self):
        report = analyze(parse_stream("/ / //"))
        self.assertEqual(report["morse_slash_dot"]["text"], "EEI")
        self.assertEqual(report["morse_slash_dot"]["invalid_positions"], [])

    def test_wrong_length_and_conflict(self):
        with self.assertRaisesRegex(ValueError, "length"):
            check_candidate(self.tokens, "banan")
        report = check_candidate(self.tokens, "bacana")
        self.assertFalse(report["consistent"])
        self.assertEqual(report["conflicts"][0]["position"], 5)

    def test_rejects_malformed_stream(self):
        for raw in ("", "/  \\", "/x", "/////", "/\n\\", "/\n\n"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_stream(raw)

    def test_local_tokens_depend_on_proposed_boundaries(self):
        tokens = parse_stream("/ // / // \\")
        report = segments(tokens, [2, 3])
        self.assertEqual(report[0]["local_tokens"], [])
        self.assertEqual(report[1]["local_tokens"], ["\\"])
        with self.assertRaisesRegex(ValueError, "sum"):
            segments(tokens, [2, 2])


if __name__ == "__main__":
    unittest.main()
