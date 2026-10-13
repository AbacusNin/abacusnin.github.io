#!/usr/bin/env python3
"""Review three RSA padding choices using an expected plaintext prefix."""

import argparse
from getpass import getpass
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


def decrypt_options(key, ciphertext):
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValueError("loaded key is not RSA")
    if len(ciphertext) != (key.key_size + 7) // 8:
        raise ValueError("ciphertext length does not match RSA modulus")
    choices = [
        ("PKCS#1 v1.5", padding.PKCS1v15()),
        ("OAEP-SHA256", padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)),
        ("OAEP-SHA1", padding.OAEP(mgf=padding.MGF1(hashes.SHA1()), algorithm=hashes.SHA1(), label=None)),
    ]
    hits = []
    for label, scheme in choices:
        try:
            hits.append((label, key.decrypt(ciphertext, scheme)))
        except ValueError:
            pass
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--in", dest="ciphertext", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path, help="new file for recovered plaintext")
    parser.add_argument("--expect-prefix", required=True, help="known plaintext prefix, such as a flag wrapper")
    args = parser.parse_args()
    try:
        if args.key.stat().st_size > 1024 * 1024 or args.ciphertext.stat().st_size > 1024 * 1024:
            parser.error("input exceeds 1 MiB")
        password = getpass("Key passphrase: ").encode("utf-8")
        key = serialization.load_pem_private_key(args.key.read_bytes(), password=password)
        prefix = args.expect_prefix.encode("utf-8")
        if not prefix:
            parser.error("expected prefix must not be empty")
        hits = [(label, plain) for label, plain in decrypt_options(key, args.ciphertext.read_bytes())
                if plain.startswith(prefix)]
        if len(hits) != 1:
            parser.error(f"expected one prefix-matching candidate; found {len(hits)}")
        label, plaintext = hits[0]
        with args.out.open("xb") as output:
            output.write(plaintext)
        print(f"{label} matched the expected prefix; wrote {len(plaintext)} bytes to {args.out}.")
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
