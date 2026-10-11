"""Standard RC4 for historical analysis and CTF reproduction, not protection."""

import argparse


def rc4(key: bytes, data: bytes) -> bytes:
    if not isinstance(key, bytes) or not 1 <= len(key) <= 256:
        raise ValueError("key must contain 1 to 256 bytes")
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")

    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) & 255
        state[i], state[j] = state[j], state[i]

    i = j = 0
    output = bytearray()
    for byte in data:
        i = (i + 1) & 255
        j = (j + state[i]) & 255
        state[i], state[j] = state[j], state[i]
        stream = state[(state[i] + state[j]) & 255]
        output.append(byte ^ stream)
    return bytes(output)


def selftest() -> None:
    # RFC 6229, 40-bit key 0102030405, stream offset 0.
    key = bytes.fromhex("0102030405")
    expected = bytes.fromhex("b2396305f03dc027ccc3524a0a1118a8")
    assert rc4(key, bytes(16)) == expected
    sample = bytes.fromhex("00010001ff00")
    assert rc4(key, rc4(key, sample)) == sample
    print("PASS: RFC 6229 offset-0 vector and byte-preserving round trip")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RC4 analysis helper; prints hex output")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--key-hex")
    data = parser.add_mutually_exclusive_group()
    data.add_argument("--data-hex")
    data.add_argument("--data-text")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        if args.key_hex is None or (args.data_hex is None and args.data_text is None):
            parser.error("provide --key-hex and either --data-hex or --data-text")
        try:
            key = bytes.fromhex(args.key_hex)
            payload = bytes.fromhex(args.data_hex) if args.data_hex is not None else args.data_text.encode("utf-8")
            print(rc4(key, payload).hex())
        except ValueError as error:
            parser.error(str(error))
