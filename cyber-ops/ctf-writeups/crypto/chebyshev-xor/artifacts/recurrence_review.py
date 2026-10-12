"""Narrow static review aid for Python modular Chebyshev-like recurrences."""

import ast
import json
import sys
from pathlib import Path

MAX_BYTES = 256000


def recurrence(node: ast.AST) -> bool:
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mod):
        return False
    sub = node.left
    if not isinstance(sub, ast.BinOp) or not isinstance(sub.op, ast.Sub):
        return False
    mul = sub.left
    if not isinstance(mul, ast.BinOp) or not isinstance(mul.op, ast.Mult):
        return False
    return (
        isinstance(mul.left, ast.BinOp)
        and isinstance(mul.left.op, ast.Mult)
        and isinstance(mul.left.left, ast.Constant)
        and mul.left.left.value == 2
        and isinstance(mul.left.right, ast.Name)
        and isinstance(mul.right, ast.Name)
        and isinstance(sub.right, ast.Name)
        and isinstance(node.right, ast.Name)
    )


def inspect(source: str) -> list[dict]:
    tree = ast.parse(source)
    large_literal = any(
        isinstance(node, ast.Constant)
        and type(node.value) is int
        and node.value.bit_length() >= 240
        for node in ast.walk(tree)
    )
    if not large_literal:
        return []
    return [
        {"line": node.lineno, "reason": "large integer and modular recurrence shape; review manually"}
        for node in ast.walk(tree) if recurrence(node)
    ]


def scan(path: Path) -> list[dict]:
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("source exceeds 256 KB")
    return inspect(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python recurrence_review.py file.py")
    for finding in scan(Path(sys.argv[1])):
        print(json.dumps(finding, sort_keys=True))
