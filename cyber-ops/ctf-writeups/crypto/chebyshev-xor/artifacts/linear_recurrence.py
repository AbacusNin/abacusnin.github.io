"""Bounded companion-matrix evaluator for a constant-coefficient recurrence."""


def linrec(coeffs: list[int], inits: list[int], n: int, modulus: int) -> int:
    """a_k = sum(coeffs[i] * a_(k-1-i)) modulo modulus."""
    degree = len(coeffs)
    if not 1 <= degree <= 16 or len(inits) != degree or modulus < 2 or n < 0 or n.bit_length() > 4096:
        raise ValueError("invalid recurrence dimensions, modulus, or index")
    if n < degree:
        return inits[n] % modulus

    def multiply(a, b):
        return [
            [sum(a[i][k] * b[k][j] for k in range(degree)) % modulus for j in range(degree)]
            for i in range(degree)
        ]

    companion = [[0] * degree for _ in range(degree)]
    companion[0] = [value % modulus for value in coeffs]
    for row in range(1, degree):
        companion[row][row - 1] = 1
    result = [[int(i == j) for j in range(degree)] for i in range(degree)]
    exponent = n - degree + 1
    while exponent:
        if exponent & 1:
            result = multiply(result, companion)
        companion = multiply(companion, companion)
        exponent >>= 1
    state = list(reversed(inits))
    return sum(result[0][i] * state[i] for i in range(degree)) % modulus
