"""Local checks for spoken-word decoding and armor validation."""

import csv
import io
import unittest
from pathlib import Path

from armor_crc_check import inspect_armor
from pgp_word_decoder import decode, load_table, parse_table


PAGE = Path(__file__).resolve().parent.parent


class DecoderChecks(unittest.TestCase):
    def test_synthetic_round_trip(self):
        tables = load_table(PAGE / "fixtures" / "synthetic_wordlist.tsv")
        words = (PAGE / "fixtures" / "synthetic_words.txt").read_text().split()
        self.assertEqual(decode(words, tables), b"HI")

    def test_parity_error(self):
        tables = load_table(PAGE / "fixtures" / "synthetic_wordlist.tsv")
        with self.assertRaisesRegex(ValueError, "odd list"):
            decode(["even072", "even073"], tables)

    def test_published_vectors(self):
        rows = [f"{value:02X}\teven{value:03}\todd{value:03}" for value in range(256)]
        rows[0xE5] = "E5\ttopmost\ttravesty"
        rows[0x82] = "82\tmiser\tIstanbul"
        tables = parse_table(list(csv.DictReader(io.StringIO("hex\teven\todd\n" + "\n".join(rows)), delimiter="\t")))
        self.assertEqual(decode(["topmost", "Istanbul"], tables), bytes.fromhex("E582"))
        self.assertEqual(decode(["miser", "travesty"], tables), bytes.fromhex("82E5"))

    def test_duplicate_word_rejected(self):
        rows = (PAGE / "fixtures" / "synthetic_wordlist.tsv").read_text().splitlines()
        rows[2] = rows[2].replace("even001", "even000")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_table(list(csv.DictReader(io.StringIO("\n".join(rows)), delimiter="\t")))

    def test_armor_crc_positive_and_negative(self):
        valid = inspect_armor((PAGE / "fixtures" / "sample_armor.asc").read_bytes())
        altered = inspect_armor((PAGE / "fixtures" / "bad_crc_armor.asc").read_bytes())
        self.assertEqual(valid["packet_bytes"], 11)
        self.assertTrue(valid["crc24_match"])
        self.assertFalse(altered["crc24_match"])

    def test_malformed_armor_rejected(self):
        with self.assertRaisesRegex(ValueError, "complete PGP MESSAGE"):
            inspect_armor(b"REVIEW ONLY")


if __name__ == "__main__":
    unittest.main()
