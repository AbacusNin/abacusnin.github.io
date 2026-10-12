"""Bounded, manual decoding aid for the encoding exercises. Never executes output."""

import base64
import re

MAX_CHARS = 8192


def decode_once(text: str, scheme: str) -> str:
    if not text or len(text) > MAX_CHARS:
        raise ValueError("input must contain 1-8192 characters")
    if scheme == "binary":
        tokens = text.split()
        if not tokens or not all(re.fullmatch(r"[01]{8}", t) for t in tokens):
            raise ValueError("expected eight-bit binary groups")
        raw = bytes(int(t, 2) for t in tokens)
    elif scheme == "octal":
        tokens = text.split()
        if not tokens or not all(re.fullmatch(r"[0-7]{3}", t) for t in tokens):
            raise ValueError("expected three-digit octal groups")
        values = [int(t, 8) for t in tokens]
        if any(v > 255 for v in values):
            raise ValueError("octal value exceeds one byte")
        raw = bytes(values)
    elif scheme == "hex":
        compact = "".join(text.split())
        if not re.fullmatch(r"(?:[0-9a-fA-F]{2})+", compact):
            raise ValueError("expected complete hex pairs")
        raw = bytes.fromhex(compact)
    elif scheme == "base64":
        compact = "".join(text.split())
        if not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", compact) or len(compact) % 4:
            raise ValueError("expected padded standard Base64")
        raw = base64.b64decode(compact, validate=True)
        if base64.b64encode(raw).decode("ascii") != compact:
            raise ValueError("noncanonical Base64 input")
    else:
        raise ValueError("choose binary, octal, hex, or base64 explicitly")
    return raw.decode("ascii", errors="strict")


def decode_stack(text: str, schemes: tuple[str, ...]) -> list[tuple[str, str]]:
    if not 1 <= len(schemes) <= 4:
        raise ValueError("choose one to four layers")
    out = []
    for scheme in schemes:
        text = decode_once(text, scheme)
        out.append((scheme, text))
    return out


def encode_stack(text: str) -> str:
    """Invented fixture: ASCII -> octal -> Base64 -> space-delimited hex."""
    octal = " ".join(f"{ord(c):03o}" for c in text)
    blob = base64.b64encode(octal.encode("ascii"))
    return " ".join(f"{b:02x}" for b in blob)
