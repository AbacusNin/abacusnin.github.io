"""Scan Python source for a marshal-to-__code__ path without executing it."""

import ast
import json
import sys
from pathlib import Path


def inspect_source(source: str) -> dict:
    tree = ast.parse(source)
    marshal_names = {"marshal"}
    loads_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            marshal_names.update(alias.asname or alias.name for alias in node.names if alias.name == "marshal")
        elif isinstance(node, ast.ImportFrom) and node.module == "marshal":
            loads_names.update(alias.asname or alias.name for alias in node.names if alias.name == "loads")

    load_calls = 0
    code_writes = 0
    literal_byte_lengths = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, bytes):
            literal_byte_lengths.append(len(node.value))
        elif isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute) and target.attr == "loads" and isinstance(target.value, ast.Name) and target.value.id in marshal_names:
                load_calls += 1
            elif isinstance(target, ast.Name) and target.id in loads_names:
                load_calls += 1
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            code_writes += sum(isinstance(target, ast.Attribute) and target.attr == "__code__" for target in targets)

    return {
        "marshal_load_calls": load_calls,
        "code_assignments": code_writes,
        "literal_byte_lengths": sorted(literal_byte_lengths),
        "lead": load_calls > 0 and code_writes > 0,
    }


def main(path: str) -> None:
    source = Path(path)
    if source.stat().st_size > 1_000_000:
        raise ValueError("input exceeds 1 MB")
    cases = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) > 100:
        raise ValueError("input must contain at most 100 cases")
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("name"), str) or not isinstance(case.get("source"), str):
            raise ValueError("each case needs a name and source string")
        if len(case["source"]) > 100_000:
            raise ValueError(f"{case['name']}: source exceeds 100,000 characters")
        result = {"name": case["name"], **inspect_source(case["source"])}
        if "expected_lead" in case and result["lead"] is not case["expected_lead"]:
            raise ValueError(f"{case['name']}: unexpected lead result")
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python static_swap_triage.py <cases.json>")
    try:
        main(sys.argv[1])
    except (OSError, ValueError, SyntaxError, TypeError, json.JSONDecodeError) as error:
        raise SystemExit(f"invalid input: {error}") from error
