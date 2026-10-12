"""Synthetic positive, benign, and near-miss checks for the two aids."""

import base64
import unittest

from decode_lab import decode_once, decode_stack, encode_stack
from process_hunt import inspect


class LocalChecks(unittest.TestCase):
    def test_all_single_layers(self):
        self.assertEqual(decode_once("01001000 01101001", "binary"), "Hi")
        self.assertEqual(decode_once("110 151", "octal"), "Hi")
        self.assertEqual(decode_once("48 69", "hex"), "Hi")
        self.assertEqual(decode_once("SGk=", "base64"), "Hi")

    def test_three_layers_and_one_character_change(self):
        for word in ("call", "cell"):
            self.assertEqual(decode_stack(encode_stack(word), ("hex", "base64", "octal"))[-1][1], word)
        self.assertNotEqual(encode_stack("call"), encode_stack("cell"))

    def test_malformed_and_ambiguous_near_miss(self):
        for text, scheme in (("1111", "binary"), ("777", "octal"), ("SGk*", "base64")):
            with self.assertRaises(ValueError):
                decode_once(text, scheme)

    def test_process_positive_benign_and_near_miss(self):
        token = base64.b64encode("Write-Output 'hello'".encode("utf-16le")).decode("ascii")
        command = "powershell.exe -EncodedCommand " + token
        positive = {"event_id": "p1", "image": "C:\\Windows\\powershell.exe", "command_line": command}
        self.assertTrue(inspect(positive)["review_required"])
        self.assertIsNone(inspect({**positive, "image": "certutil.exe"}))
        self.assertIsNone(inspect({**positive, "command_line": "powershell.exe -File maintenance.ps1"}))
        self.assertIsNone(inspect({**positive, "command_line": "powershell.exe -enc SGk*"}))
        # Valid encoded admin commands still need review; this detector cannot decide malice.
        self.assertNotIn("decoded", inspect(positive))


if __name__ == "__main__":
    unittest.main()
