"""Narrow AST review lead for weak random key material reused under a transform."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


def _random_key(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "random"
        and node.func.attr == "randbytes"
    )


def _mentions(node: ast.AST, name: str) -> bool:
    return any(isinstance(child, ast.Name) and child.id == name for child in ast.walk(node))


def review(source: str) -> list[dict[str, object]]:
    tree = ast.parse(source)
    findings: list[dict[str, object]] = []
    for scope in (tree, *(node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))):
        nodes = list(scope.body) if isinstance(scope, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)) else []
        assigned = [
            (target.id, node.lineno)
            for node in nodes if isinstance(node, ast.Assign) and _random_key(node.value)
            for target in node.targets if isinstance(target, ast.Name)
        ]
        for name, line in assigned:
            later = [node for statement in nodes if statement.lineno > line for node in ast.walk(statement)]
            calls = [node for node in later if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "encrypt" and node.args]
            raw = any(isinstance(call.args[0], ast.Name) and call.args[0].id == name for call in calls)
            transformed = any(isinstance(call.args[0], ast.Call) and _mentions(call.args[0], name) for call in calls)
            findings.append({"line": line, "rule": "weak-random-key", "key": name})
            if raw and transformed:
                findings.append({"line": line, "rule": "possible-key-reuse-under-transform", "key": name})
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Python files to review")
    args = parser.parse_args()
    for path in args.files:
        try:
            findings = review(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError) as error:
            print(f"{path}: unable to review: {error}")
            continue
        for finding in findings:
            print(f"{path}:{finding['line']}: {finding['rule']} ({finding['key']})")


if __name__ == "__main__":
    main()
