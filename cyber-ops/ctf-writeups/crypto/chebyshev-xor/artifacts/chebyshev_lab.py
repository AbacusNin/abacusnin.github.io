"""Synthetic Chebyshev/XOR lab. No challenge ciphertext or key material is included."""

P = (1 << 256) - (1 << 32) - 977


def chebyshev_fast(x: int, n: int, p: int = P) -> int:
    if p < 2 or n < 0 or n.bit_length() > 4096:
        raise ValueError("invalid modulus or index")
    x %= p
    a, b = 1 % p, x  # T_0, T_1
    for bit in bin(n)[2:]:
        even = (2 * a * a - 1) % p
        odd = (2 * a * b - x) % p
        next_even = (2 * b * b - 1) % p
        a, b = (even, odd) if bit == "0" else (odd, next_even)
    return a


def chebyshev_slow(x: int, n: int, p: int = P) -> int:
    if p < 2 or not 0 <= n <= 100000:
        raise ValueError("reference index must be at most 100000")
    if n == 0:
        return 1 % p
    prev, current = 1 % p, x % p
    for _ in range(n - 1):
        prev, current = current, (2 * x * current - prev) % p
    return current


def keystream_bytes(x: int, n: int, p: int = P) -> bytes:
    """Minimal big-endian form, matching long_to_bytes for a nonnegative integer."""
    value = chebyshev_fast(x, n, p)
    return value.to_bytes(max(1, (value.bit_length() + 7) // 8), "big")


def xor_cycle(data: bytes, key: bytes) -> bytes:
    if not key:
        raise ValueError("empty keystream")
    return bytes(byte ^ key[index % len(key)] for index, byte in enumerate(data))


def matrix_reference(x: int, n: int, p: int = P) -> int:
    """Independent 2x2 exponentiation: A^(n-1) [x,1] gives T_n for n >= 1."""
    if p < 2 or n < 0 or n.bit_length() > 4096:
        raise ValueError("invalid modulus or index")
    if n == 0:
        return 1 % p

    def multiply(a, b):
        return (
            ((a[0] * b[0] + a[1] * b[2]) % p, (a[0] * b[1] + a[1] * b[3]) % p,
             (a[2] * b[0] + a[3] * b[2]) % p, (a[2] * b[1] + a[3] * b[3]) % p)
        )

    result = (1, 0, 0, 1)
    base = (2 * x % p, -1 % p, 1, 0)
    exponent = n - 1
    while exponent:
        if exponent & 1:
            result = multiply(result, base)
        base = multiply(base, base)
        exponent >>= 1
    return (result[0] * x + result[1]) % p
