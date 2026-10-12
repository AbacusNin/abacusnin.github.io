"""Invented positive, benign, near-miss and malformed cases."""

import unittest
from pathlib import Path

from digest_compare_review import review_text
from service_hash_review import read_events, review


class DigestCompareReviewTests(unittest.TestCase):
    def test_dynamic_prefix_and_slice(self):
        code = """import hashlib
digest = hashlib.sha1(data).hexdigest()
ok = digest.startswith(target)
also = digest[:6] == supplied
hasher = hashlib.sha256(data)
raw = hasher.digest()
third = raw[:3] == supplied_bytes
"""
        self.assertEqual([f["kind"] for f in review_text(code)],
                         ["digest-startswith", "digest-prefix-comparison", "digest-prefix-comparison"])

    def test_full_digest_and_nonsecurity_identifier(self):
        code = """import hashlib
digest = hashlib.sha256(data).hexdigest()
ok = digest == approved_digest
label = random_id[:6]
"""
        self.assertEqual(review_text(code), [])

    def test_expected_false_positive_short_display_label(self):
        code = """import hashlib
digest = hashlib.sha256(data).hexdigest()
same_label = digest.startswith(display_prefix)
"""
        self.assertEqual(review_text(code)[0]["kind"], "digest-startswith")

    def test_known_wrapper_limit(self):
        # This is a near miss: a custom helper hides digest provenance.
        self.assertEqual(review_text("ok = custom_digest(data)[:6] == supplied"), [])


class ServiceHashReviewTests(unittest.TestCase):
    def test_invented_fixture(self):
        events = read_events(Path(__file__).parent / "fixtures" / "service_events.jsonl")
        self.assertEqual([f["kind"] for f in review(events)],
                         ["short-comparison", "unkeyed-verifier", "diagnostic-echo", "unkeyed-verifier"])

    def test_malformed_and_near_miss(self):
        with self.assertRaises(ValueError):
            review([{"kind": "issued", "session": "s", "construction": "raw_hash", "tag_bits": True}])
        self.assertEqual(review([{"kind": "issued", "session": "s", "construction": "hmac", "tag_bits": 128}]), [])


if __name__ == "__main__":
    unittest.main()
