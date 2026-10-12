"""Find Python digest-prefix comparisons for a human security review.

This AST-only tool does not execute the scanned file or decide whether a use is unsafe.
"""

import argparse
import ast
import json
from pathlib import Path

MAX_BYTES = 1_000_000
DIGEST_METHODS = {"digest", "hexdigest"}
HASH_CONSTRUCTORS = {"md5", "sha1", "sha224", "sha256", "sha384", "sha512",
                     "sha3_224", "sha3_256", "sha3_384", "sha3_512", "blake2b", "blake2s", "new"}


def review_text(source):
    tree = ast.parse(source)
    digest_names = set()
    hash_names = set()

    def hash_constructor(node):
        return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and ((node.func.value.id == "hashlib" and node.func.attr in HASH_CONSTRUCTORS)
                     or (node.func.value.id == "hmac" and node.func.attr == "new")))

    def digest_call(node):
        return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in DIGEST_METHODS
                and (hash_constructor(node.func.value)
                     or isinstance(node.func.value, ast.Name) and node.func.value.id in hash_names))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and hash_constructor(node.value):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            hash_names.update(t.id for t in targets if isinstance(t, ast.Name))
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and digest_call(node.value):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            digest_names.update(t.id for t in targets if isinstance(t, ast.Name))

    def is_digest(node):
        return digest_call(node) or isinstance(node, ast.Name) and node.id in digest_names

    def is_prefix_slice(node):
        return (isinstance(node, ast.Subscript) and is_digest(node.value)
                and isinstance(node.slice, ast.Slice) and node.slice.lower is None
                and node.slice.upper is not None)

    findings = []
    for node in ast.walk(tree):
        kind = None
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "startswith" and is_digest(node.func.value):
                kind = "digest-startswith"
            elif node.func.attr == "compare_digest" and any(is_prefix_slice(a) for a in node.args):
                kind = "partial-compare-digest"
        elif isinstance(node, ast.Compare):
            if is_prefix_slice(node.left) or any(is_prefix_slice(x) for x in node.comparators):
                kind = "digest-prefix-comparison"
        if kind:
            findings.append({"line": node.lineno, "kind": kind})
    return sorted(findings, key=lambda item: (item["line"], item["kind"]))


def review_file(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("file exceeds 1 MB limit")
    return review_text(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    output = []
    for path in args.files:
        output.extend({"file": str(path), **finding} for finding in review_file(path))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
