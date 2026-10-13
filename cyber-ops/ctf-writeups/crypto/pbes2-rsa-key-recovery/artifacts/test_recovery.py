"""Synthetic local check; does not use challenge material."""

import io
import unittest

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from crack_pkcs8 import find_password
from decrypt_rsa import decrypt_options


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.pem = cls.key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(b"synthetic-pass"),
        )

    def test_wordlist_match_and_single_block_decrypt(self):
        found = find_password(self.pem, io.BytesIO(b"wrong\nsynthetic-pass\n"))
        self.assertEqual((found[0], found[1]), (2, b"synthetic-pass"))
        ciphertext = self.key.public_key().encrypt(b"synthetic message", padding.PKCS1v15())
        self.assertIn(("PKCS#1 v1.5", b"synthetic message"), decrypt_options(found[2], ciphertext))

    def test_limit_and_invalid_password(self):
        self.assertIsNone(find_password(self.pem, io.BytesIO(b"wrong\nsynthetic-pass\n"), limit=1))

    def test_oaep_sha256_and_wrong_block_size(self):
        scheme = padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        ciphertext = self.key.public_key().encrypt(b"second fixture", scheme)
        self.assertIn(("OAEP-SHA256", b"second fixture"), decrypt_options(self.key, ciphertext))
        with self.assertRaisesRegex(ValueError, "length"):
            decrypt_options(self.key, ciphertext[:-1])


if __name__ == "__main__":
    unittest.main()
