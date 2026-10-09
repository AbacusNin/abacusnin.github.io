"""Reflect ASCII Latin letters through the alphabet for a CTF sample."""

import sys

SAMPLE_CT = "uozt{zgyzhs_rh_zm_rmelofgrlm}"


def atbash(text: str) -> str:
    out = []
    for char in text:
        if "a" <= char <= "z":
            out.append(chr(ord("z") - (ord(char) - ord("a"))))
        elif "A" <= char <= "Z":
            out.append(chr(ord("Z") - (ord(char) - ord("A"))))
        else:
            out.append(char)
    return "".join(out)


text = sys.argv[1] if len(sys.argv) > 1 else SAMPLE_CT
result = atbash(text)
print(result)
assert atbash(result) == text
