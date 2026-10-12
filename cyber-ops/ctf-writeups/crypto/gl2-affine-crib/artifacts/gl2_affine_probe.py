"""Probe a bounded, synthetic instance of the GL2(F67) affine cipher."""

import json
from pathlib import Path


P = 67
Q = 11
GENERATOR = 9
ROUNDS = Q + 1
BASE_CHAR = ord("<")
MAX_TEXT = 256


def symbols(text):
    if not isinstance(text, str) or any(not BASE_CHAR <= ord(ch) < BASE_CHAR + P for ch in text):
        raise ValueError("text must use characters from '<' through '~'")
    return [ord(ch) - BASE_CHAR for ch in text]


def chars(values):
    return "".join(chr(BASE_CHAR + value % P) for value in values)


def mul(left, right):
    d1, a1 = left
    d2, a2 = right
    return (d1 * d2 % P, (a1 + d1 * a2) % P)


def keystream(key, count):
    seed_values = symbols(key)
    if len(seed_values) != Q or not 1 <= count <= MAX_TEXT:
        raise ValueError("key must have 11 symbols and count must be 1-256")
    seed = [(1, value) for value in seed_values]
    needed = count + ROUNDS
    stream = list(seed)
    for a in range(P):
        for b in range(Q):
            if a == 0 and b == 0:
                continue
            group = (pow(GENERATOR, b, P), a)
            stream.extend(mul(group, entry) for entry in seed)
            if len(stream) >= needed:
                break
        if len(stream) >= needed:
            break
    stream = stream[:needed]
    for _ in range(ROUNDS):
        stream = [mul(left, right) for left, right in zip(stream, stream[1:])]
    return stream


def encrypt(key, plaintext):
    values = symbols(plaintext)
    return chars((d * value - a) % P for (d, a), value in zip(keystream(key, len(values)), values))


def decrypt(key, ciphertext):
    values = symbols(ciphertext)
    return chars(((value + a) * pow(d, -1, P)) % P for (d, a), value in zip(keystream(key, len(values)), values))


def affine_model(count):
    base = keystream("<" * Q, count)
    diagonal = [d for d, _ in base]
    constant = [a for _, a in base]
    columns = []
    for key_index in range(Q):
        unit = [0] * Q
        unit[key_index] = 1
        probe = keystream(chars(unit), count)
        if [d for d, _ in probe] != diagonal:
            raise ValueError("diagonal depends on key; affine model invalid")
        columns.append([(a - constant[i]) % P for i, (_, a) in enumerate(probe)])
    rows = [[columns[j][i] for j in range(Q)] for i in range(count)]
    return diagonal, constant, rows


def solve(rows, rhs):
    if len(rows) != len(rhs) or any(len(row) != Q for row in rows):
        raise ValueError("equations need one right-hand value and 11 coefficients per row")
    matrix = [[value % P for value in row] + [value % P] for row, value in zip(rows, rhs)]
    pivots = []
    rank = 0
    for col in range(Q):
        pivot = next((i for i in range(rank, len(matrix)) if matrix[i][col]), None)
        if pivot is None:
            continue
        matrix[rank], matrix[pivot] = matrix[pivot], matrix[rank]
        inv = pow(matrix[rank][col], -1, P)
        matrix[rank] = [value * inv % P for value in matrix[rank]]
        for index in range(len(matrix)):
            if index == rank:
                continue
            factor = matrix[index][col]
            if factor:
                matrix[index] = [(a - factor * b) % P for a, b in zip(matrix[index], matrix[rank])]
        pivots.append(col)
        rank += 1
        if rank == len(matrix):
            break
    if any(not any(row[:Q]) and row[Q] for row in matrix):
        raise ValueError("crib equations are inconsistent")
    free = [col for col in range(Q) if col not in pivots]
    particular = [0] * Q
    for row_index, col in enumerate(pivots):
        particular[col] = matrix[row_index][Q]
    basis = []
    for free_col in free:
        vector = [0] * Q
        vector[free_col] = 1
        for row_index, pivot_col in enumerate(pivots):
            vector[pivot_col] = -matrix[row_index][free_col] % P
        basis.append(vector)
    return particular, basis, rank


def crib_system(ciphertext, known):
    cipher_values = symbols(ciphertext)
    if not isinstance(known, dict) or any(type(index) is not int for index in known):
        raise ValueError("crib positions must be integer-indexed")
    diagonal, constant, rows = affine_model(len(cipher_values))
    selected = []
    rhs = []
    for index, ch in sorted(known.items()):
        if not isinstance(index, int) or not 0 <= index < len(cipher_values):
            raise ValueError("crib position outside ciphertext")
        plain_value = symbols(ch)
        if len(plain_value) != 1:
            raise ValueError("each crib value must be one symbol")
        selected.append(rows[index])
        rhs.append((diagonal[index] * plain_value[0] - constant[index] - cipher_values[index]) % P)
    return solve(selected, rhs)


def independent_positions(rows, count):
    chosen = []
    rank = 0
    for index, row in enumerate(rows):
        new_rank = solve([rows[i] for i in chosen + [index]], [0] * (len(chosen) + 1))[2]
        if new_rank > rank:
            chosen.append(index)
            rank = new_rank
            if rank == count:
                break
    if rank < count:
        raise ValueError(f"only {rank} independent positions found")
    return chosen


def demo():
    fixture = Path(__file__).resolve().parent.parent / "fixtures" / "synthetic_case.json"
    case = json.loads(fixture.read_text(encoding="utf-8"))
    key, plain = case["key"], case["plaintext"]
    cipher = encrypt(key, plain)
    diagonal, constant, rows = affine_model(len(plain))
    key_values = symbols(key)
    predicted = [(constant[i] + sum(x * y for x, y in zip(rows[i], key_values))) % P for i in range(len(plain))]
    assert predicted == [a for _, a in keystream(key, len(plain))]
    positions = independent_positions(rows, Q)
    known = {i: plain[i] for i in positions}
    recovered, basis, rank = crib_system(cipher, known)
    assert rank == Q and not basis and chars(recovered) == key
    assert decrypt(chars(recovered), cipher) == plain and encrypt(chars(recovered), plain) == cipher

    short_known = {i: plain[i] for i in positions[:7]}
    first, free_basis, short_rank = crib_system(cipher, short_known)
    alternate = [(x + y) % P for x, y in zip(first, free_basis[0])]
    p1, p2 = decrypt(chars(first), cipher), decrypt(chars(alternate), cipher)
    assert p1 != p2 and encrypt(chars(first), p1) == cipher and encrypt(chars(alternate), p2) == cipher
    print(json.dumps({
        "fixture": "synthetic_case.json",
        "full_crib_rank": rank,
        "full_crib_key_match": chars(recovered) == key,
        "full_crib_plaintext_match": decrypt(chars(recovered), cipher) == plain,
        "seven_crib_rank": short_rank,
        "seven_crib_candidate_count": P ** len(free_basis),
        "two_different_candidates_reencrypt": p1 != p2,
        "meaning": "re-encryption checks algebraic consistency, not candidate uniqueness",
    }, indent=2))


if __name__ == "__main__":
    demo()
