#!/usr/bin/env python3
"""Recheck an ECDSA P-256 timing/HNP claim without printing the secret.

Requires PyCryptodome. Inputs stay local; no network access or flag output.
"""

import argparse
import csv
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from pathlib import Path

from Crypto.Cipher import AES, ChaCha20
from Crypto.Util import Counter
from Crypto.PublicKey import ECC


ORDER = int("ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551", 16)
MAX_TRACE_BYTES = 4_000_000
MAX_ROWS = 20_000


def read_bounded(path, limit):
    file = Path(path)
    if file.stat().st_size > limit:
        raise ValueError(f"Input exceeds {limit} bytes")
    return file.read_text(encoding="utf-8")


def gram_schmidt(basis):
    size = len(basis)
    orthogonal = []
    mu = [[Decimal(0) for _ in range(size)] for _ in range(size)]
    norms = []
    for i, row in enumerate(basis):
        current = [Decimal(value) for value in row]
        for j in range(i):
            product = sum(Decimal(row[t]) * orthogonal[j][t] for t in range(size))
            mu[i][j] = product / norms[j]
            current = [current[t] - mu[i][j] * orthogonal[j][t] for t in range(size)]
        orthogonal.append(current)
        norms.append(sum(value * value for value in current))
    return mu, norms


def reduce_lll(basis):
    with localcontext() as context:
        context.prec = 400
        mu, norms = gram_schmidt(basis)
        k = 1
        cycles = 0
        while k < len(basis):
            cycles += 1
            if cycles > 150_000:
                raise RuntimeError("LLL iteration limit exceeded")
            for j in range(k - 1, -1, -1):
                q = int(mu[k][j].to_integral_value(rounding=ROUND_HALF_EVEN))
                if q:
                    basis[k] = [a - q * b for a, b in zip(basis[k], basis[j])]
                    mu, norms = gram_schmidt(basis)
            if norms[k] >= (Decimal("0.75") - mu[k][k - 1] ** 2) * norms[k - 1]:
                k += 1
            else:
                basis[k], basis[k - 1] = basis[k - 1], basis[k]
                mu, norms = gram_schmidt(basis)
                k = max(k - 1, 1)
    return cycles


def recover(rows, public_key, base_ns, step_ns, padding):
    if len(rows) < 6:
        raise ValueError("At least six signatures are required for this replay")
    chosen = sorted(rows, key=lambda row: int(row["elapsed_ns"]))[:6]
    bounds = [round((int(row["elapsed_ns"]) - base_ns) / step_ns) + padding for row in chosen]
    if min(bounds) < 1 or max(bounds) > 256:
        raise ValueError("Inferred nonce bounds outside P-256 width")
    width = 1 << max(bounds)
    count = len(chosen)
    basis = [[0] * (count + 2) for _ in range(count + 2)]
    for i in range(count):
        basis[i][i] = ORDER * ORDER
    for i, row in enumerate(chosen):
        r, s, h = (int(row[name], 16) for name in ("r", "s", "h"))
        if not (1 <= r < ORDER and 1 <= s < ORDER):
            raise ValueError(f"Invalid signature scalar at ID {row['id']}")
        inverse = pow(s, -1, ORDER)
        alpha = inverse * r % ORDER
        beta = inverse * h % ORDER
        basis[count][i] = ORDER * alpha
        basis[count + 1][i] = ORDER * ((beta - width // 2) % ORDER)
    basis[count][count] = width
    basis[count + 1][count + 1] = width * ORDER
    cycles = reduce_lll(basis)

    coordinates = {}
    for line in public_key.splitlines():
        if line.startswith(("Qx =", "Qy =")):
            label, value = line.split("=", 1)
            coordinates[label.strip()] = int(value.strip(), 16)
    point = ECC.construct(curve="P-256", point_x=coordinates["Qx"], point_y=coordinates["Qy"])
    generator = ECC._curves["P-256"].G
    for row in basis:
        if row[count] == 0 or row[count] % width:
            continue
        for sign in (1, -1):
            candidate = (sign * row[count] // width) % ORDER
            if 1 <= candidate < ORDER and generator * candidate == point.pointQ:
                return candidate, chosen, bounds, cycles
    return None, chosen, bounds, cycles


def probe_ciphertext(scalar, ciphertext):
    scalar_bytes = scalar.to_bytes(32, "big")
    keys = {
        "raw scalar": scalar_bytes,
        "SHA256(scalar bytes)": sha256(scalar_bytes).digest(),
        "SHA256(scalar hex)": sha256(scalar_bytes.hex().encode()).digest(),
    }
    candidates = []
    raw_stream = (scalar_bytes * ((len(ciphertext) + 31) // 32))[:len(ciphertext)]
    candidates.append(("repeating scalar XOR", bytes(a ^ b for a, b in zip(ciphertext, raw_stream))))
    for label, key in keys.items():
        hash_stream = b"".join(
            sha256(key + i.to_bytes(4, "big")).digest()
            for i in range((len(ciphertext) + 31) // 32)
        )[:len(ciphertext)]
        candidates.append((f"hash-chain XOR / {label}", bytes(a ^ b for a, b in zip(ciphertext, hash_stream))))
        counter = Counter.new(128, initial_value=0)
        candidates.append((f"AES-CTR zero counter / {label}", AES.new(key, AES.MODE_CTR, counter=counter).decrypt(ciphertext)))
        for nonce_size in (8, 12):
            candidates.append((f"ChaCha20 zero nonce {nonce_size} / {label}", ChaCha20.new(key=key, nonce=b"\0" * nonce_size).decrypt(ciphertext)))
    def rank(item):
        _, plaintext = item
        printable = sum(32 <= value < 127 for value in plaintext)
        shape = plaintext.endswith(b"}") and b"{" in plaintext
        return (shape and printable == len(plaintext), printable)
    label, plaintext = max(candidates, key=rank)
    return label, sum(32 <= value < 127 for value in plaintext), plaintext.endswith(b"}") and b"{" in plaintext, len(candidates)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", help="CSV with id, h, r, s, elapsed_ns")
    parser.add_argument("public_key", help="Text with Qx and Qy lines")
    parser.add_argument("--ciphertext", help="Optional ASCII hex ciphertext")
    parser.add_argument("--base-ns", type=int, default=133662)
    parser.add_argument("--step-ns", type=int, default=250)
    parser.add_argument("--padding", type=int, default=4)
    args = parser.parse_args()
    if args.step_ns <= 0 or not 0 <= args.padding <= 32:
        parser.error("step must be positive and padding must be 0..32")
    import io
    rows = list(csv.DictReader(io.StringIO(read_bounded(args.trace, MAX_TRACE_BYTES))))
    if len(rows) > MAX_ROWS:
        raise ValueError("Too many trace rows")
    scalar, chosen, bounds, cycles = recover(
        rows, read_bounded(args.public_key, 4096), args.base_ns, args.step_ns, args.padding
    )
    print("trace_rows", len(rows))
    print("selected_ids", [row["id"] for row in chosen])
    print("nonce_bit_bounds", bounds)
    print("lll_cycles", cycles)
    print("public_key_match", scalar is not None)
    if args.ciphertext and scalar is not None:
        ciphertext = bytes.fromhex(read_bounded(args.ciphertext, 4096).strip())
        branch, printable, shape, probes = probe_ciphertext(scalar, ciphertext)
        print("ciphertext_bytes", len(ciphertext))
        print("probe_count", probes)
        print("best_branch", branch)
        print("printable_plaintext_bytes", printable)
        print("flag_shape", shape)


if __name__ == "__main__":
    main()
