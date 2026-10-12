#!/usr/bin/env python3
"""
Solver for a NYT-Connections-style word-partition game with an 800 ms per-round
blitz timer, plaintext rounds 1-4, hashed rounds 5-10.

Exploit chain:
  1. Per-user PRNG seed initialized from SecureRandom but advanced by a
     deterministic LCG. Advanced seed is then passed to `new java.util.Random(seed)`
     to drive Fisher-Yates over the board's 16 words.
  2. The `getFragment` operation returns (int)(S >>> 16) after one LCG step,
     leaking 32 of 48 seed bits. Lower 16 brute-forced against first shuffle.
  3. Hashed mode validated by set-equality of submitted hashes against re-hashed
     group words. Since `getAllWords()` lays groups out contiguously at positions
     [0..3], [4..7], [8..11], [12..15], the salt is unnecessary: the partition is
     recovered by inverting the predicted shuffle and bucketing by index//4.

Usage:
  ./solve.py <target.host> <port> [path/to/Connections_Data.json]
"""
import json, os, random, socket, string, sys, time

# Java internals - values from the JDK source for java.util.Random.
JAVA_MULT = 0x5DEECE66D
JAVA_ADD = 0xB
MASK48 = (1 << 48) - 1

# Server LCG constants - derived from the supplied source by inspection.
# These constants are structural properties of the target, not secrets.
STEP_MULT = (JAVA_MULT ^ 0xABCDEF123) + JAVA_ADD
STEP_INCR = 11


def lcg_step(seed):
    """Advance the server's per-user PRNG state by one LCG step."""
    return (STEP_MULT * seed + STEP_INCR) & MASK48


def java_shuffle_perm(seed, n=16):
    """Java Random(seed) Fisher-Yates on [0..n) - returns a permutation array
    where a[shuffled_pos] = original_pos."""
    rnd = (seed ^ JAVA_MULT) & MASK48
    a = list(range(n))
    for i in range(n - 1, 0, -1):
        bound = i + 1
        m = bound - 1
        if (bound & m) == 0:
            # Power-of-two fast path.
            rnd = (rnd * JAVA_MULT + JAVA_ADD) & MASK48
            j = (bound * (rnd >> 17)) >> 31
        else:
            # Non-power-of-two rejection sampling. The Java check
            # `bits - val + (n-1) < 0` is a signed-int overflow test;
            # in Python we transcribe it as (u - r + m) < 2^31.
            while True:
                rnd = (rnd * JAVA_MULT + JAVA_ADD) & MASK48
                u = rnd >> 17
                r = u % bound
                if (u - r + m) < (1 << 31):
                    j = r
                    break
        a[i], a[j] = a[j], a[i]
    return a


def crack_seed(leaked_high32, target_perm):
    """Brute-force the lower 16 bits of S2 against an observed 16-position shuffle.

    Early abort on first position mismatch keeps expected work per wrong candidate
    at roughly two nextInt calls."""
    base = leaked_high32 << 16
    for low in range(1 << 16):
        S2 = base | low
        S3 = (STEP_MULT * S2 + STEP_INCR) & MASK48
        rnd = (S3 ^ JAVA_MULT) & MASK48
        a = list(range(16))
        ok = True
        for i in range(15, 0, -1):
            bound = i + 1
            m = bound - 1
            if (bound & m) == 0:
                rnd = (rnd * JAVA_MULT + JAVA_ADD) & MASK48
                j = (bound * (rnd >> 17)) >> 31
            else:
                while True:
                    rnd = (rnd * JAVA_MULT + JAVA_ADD) & MASK48
                    u = rnd >> 17
                    r = u % bound
                    if (u - r + m) < (1 << 31):
                        j = r
                        break
            a[i], a[j] = a[j], a[i]
            if a[i] != target_perm[i]:
                ok = False
                break
        if ok and a[0] == target_perm[0]:
            return S2
    return None


def normalize(w):
    """Match the server's word normalization on the submission path."""
    return w.replace('-', ' ').upper().strip()


def all_words_and_groups(game):
    """Reproduce Java Game.getAllWords(): sort words within each group,
    sort groups by first-word, concatenate. Positions [0..3], [4..7],
    [8..11], [12..15] map to the four groups in order."""
    groups = []
    for grp in game['groups']:
        words = sorted(normalize(w) for w in grp['words'])
        groups.append({'theme': grp['theme'], 'words': words})
    groups.sort(key=lambda g: g['words'][0])
    aw = []
    for g in groups:
        aw.extend(g['words'])
    return aw, groups


class Conn:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=15)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.f = self.s.makefile('rwb', buffering=0)

    def send(self, **kw):
        self.f.write((json.dumps({k: v for k, v in kw.items() if v is not None})
                      + '\n').encode())

    def recv(self):
        line = self.f.readline()
        if not line:
            raise EOFError('Connection closed')
        return json.loads(line.decode())

    def close(self):
        try: self.s.close()
        except Exception: pass


def solve(host, port, data_path):
    with open(data_path, encoding='utf-8') as fp:
        games = json.load(fp)

    # Index games by their 16-word set for O(1) game identification.
    by_set = {}
    for g in games:
        aw, sg = all_words_and_groups(g)
        by_set[frozenset(aw)] = (g, aw, sg)

    c = Conn(host, port)
    user = 'pwn_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))

    c.send(operation='register', name=user, psw='x')
    c.recv()

    c.send(operation='login', username=user, psw='x', udpPort=12345)
    c.recv()

    # Leak: getFragment returns (int)(S2 >>> 16).
    c.send(operation='getFragment')
    leaked = c.recv()['gameId'] & 0xFFFFFFFF

    c.send(operation='startChallenge')
    r = c.recv()
    board = r['boardWords']

    # Board words come back raw; normalize for DB lookup (fix for Bug.2).
    board_norm = [normalize(w) for w in board]
    game, aw, sg = by_set[frozenset(board_norm)]

    aw_idx = {w: i for i, w in enumerate(aw)}
    target_perm = [aw_idx[w] for w in board_norm]

    # Brute force the lower 16 bits.
    S2 = crack_seed(leaked, target_perm)
    if S2 is None:
        raise RuntimeError("Seed recovery failed - target permutation not matched")
    cur_seed = lcg_step(S2)

    for step in range(1, 11):
        if step <= 4:
            # Plaintext mode: identify game by frozenset, submit known groups.
            board_norm = [normalize(w) for w in board]
            game, aw, sg = by_set[frozenset(board_norm)]
            groups = [g['words'] for g in sg]
        else:
            # Hashed mode: invert predicted shuffle, bucket by original_index // 4.
            perm = java_shuffle_perm(cur_seed, 16)
            buckets = [[], [], [], []]
            for shuf_pos, orig_pos in enumerate(perm):
                buckets[orig_pos // 4].append(board[shuf_pos])
            groups = buckets

        # Pipeline all four submissions per round; one RTT total instead of four.
        for grp in groups:
            c.send(operation='submitProposal', words=grp)
        flag = None
        for grp in groups:
            r = c.recv()
            if r.get('status') not in ('OK', 'CHALLENGE_MODE'):
                raise RuntimeError(f"Rejected: {r.get('errorMessage')}")
            if r.get('boardWords') is not None:
                board = r['boardWords']
                cur_seed = lcg_step(cur_seed)
            if 'CHALLENGE COMPLETED' in (r.get('errorMessage') or ''):
                flag = r['errorMessage']

        if flag:
            print(flag)
            c.close()
            return

    c.close()


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    data = sys.argv[3] if len(sys.argv) > 3 else 'Connections_Data.json'
    solve(host, port, data)
