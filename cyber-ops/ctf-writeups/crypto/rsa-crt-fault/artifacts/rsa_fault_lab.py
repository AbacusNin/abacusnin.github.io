"""Toy RSA-CRT fault and pre-return validation demonstration. Never use for real keys."""

from __future__ import annotations

from math import gcd

P, Q, E = 61, 53, 17
N = P * Q
D = pow(E, -1, (P - 1) * (Q - 1))


class CryptoFaultDetected(Exception):
    pass


def sign_raw(message: int, *, fault_q: bool = False, validate: bool = False) -> int:
    """CRT on tiny primes. Fault one residue only; validate before any return."""
    if not 0 <= message < N:
        raise ValueError("message representative out of range")
    sp = pow(message, D % (P - 1), P)
    sq = pow(message, D % (Q - 1), Q)
    if fault_q:
        sq = (sq + 1) % Q
    q_inverse = pow(Q, -1, P)
    signature = sq + Q * ((q_inverse * (sp - sq)) % P)
    if validate and pow(signature, E, N) != message:
        raise CryptoFaultDetected("invalid CRT output blocked before return")
    return signature


def recover_factor(message: int, faulty_signature: int, exponent: int, modulus: int) -> int:
    """A nontrivial GCD exists only if one CRT residue remained correct."""
    factor = gcd(pow(faulty_signature, exponent, modulus) - message, modulus)
    if factor in (1, modulus):
        raise ValueError("no nontrivial factor recovered")
    return factor


def blind(value: int, factor: int, exponent: int, modulus: int) -> int:
    if gcd(factor, modulus) != 1:
        raise ValueError("blinding factor must be invertible modulo n")
    return (value * pow(factor, exponent, modulus)) % modulus


def unblind(response: int, factor: int, modulus: int) -> int:
    return (response * pow(factor, -1, modulus)) % modulus


def demo() -> dict[str, object]:
    probes = {m: sign_raw(m, fault_q=(m == 3)) for m in (2, 3, 5)}
    valid = {m: pow(signature, E, N) == m for m, signature in probes.items()}
    factor = recover_factor(3, probes[3], E, N)
    other = N // factor
    recovered_d = pow(E, -1, (factor - 1) * (other - 1))
    ciphertext = pow(65, E, N)
    plaintext = pow(ciphertext, recovered_d, N)
    return {"validity": valid, "factor": factor, "other_factor": other, "plaintext": plaintext}


if __name__ == "__main__":
    print(demo())
