"""Check a modular form-selection transcript and profile one candidate path."""

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEMO = HERE / "fixtures"
DEMO_KEY = "ABFCADE"
MAX_BYTES = 1024 * 1024


def read_small(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"Input exceeds 1 MiB: {path}")
    return path.read_bytes()


def load_model(path):
    model = json.loads(read_small(path))
    m1, m2, fields = model["mod_form"], model["mod_state"], model["fields"]
    if not (isinstance(m1, int) and 2 <= m1 <= 64 and isinstance(m2, int) and 2 <= m2 <= 65536):
        raise ValueError("Moduli must be positive integers within the lab limits")
    if not isinstance(fields, dict) or not (1 <= len(fields) <= 32):
        raise ValueError("Expected 1-32 named fields")
    for name, field in fields.items():
        forms = field["forms"]
        if not isinstance(name, str) or not name or not isinstance(field["series"], int) or field["series"] < 1:
            raise ValueError("Each field needs a name and positive series")
        if not isinstance(forms, list) or len(forms) != m1 or len(set(forms)) != m1:
            raise ValueError(f"{name}: expected {m1} distinct forms")
        if any(not isinstance(form, str) or not form or form != form.strip() or "\n" in form or len(form) > 200 for form in forms):
            raise ValueError(f"{name}: forms must be short, nonempty lines without edge spaces")
    return m1, m2, fields


def parse_answer(answer, names, fields):
    found = []

    def walk(position, offset, indices):
        if len(found) > 1:
            return
        if position == len(names):
            if offset == len(answer):
                found.append(tuple(indices))
            return
        forms = fields[names[position]]["forms"]
        for index in sorted(range(len(forms)), key=lambda i: -len(forms[i])):
            form = forms[index]
            if not answer.startswith(form, offset):
                continue
            end = offset + len(form)
            if position < len(names) - 1:
                if end < len(answer) and answer[end] == " ":
                    walk(position + 1, end + 1, indices + [index])
            elif end == len(answer):
                walk(position + 1, end, indices + [index])

    walk(0, 0, [])
    if len(found) != 1:
        raise ValueError(f"Answer has {len(found)} valid parses: {answer!r}")
    return found[0]


def render(key, questions, m1, m2, fields):
    product, lines = 1, []
    for char, names in zip(key, questions):
        forms = []
        for name in names:
            field = fields[name]
            state = field["series"] * product % m2
            forms.append(field["forms"][(state * ord(char)) % m1])
        lines.append(" ".join(forms))
        product = product * ord(char) % m2
    return ("\n".join(lines) + "\n").encode("utf-8")


def profile(key, questions, observed, alphabet, m1, m2, fields):
    product = 1
    for position, (char, names, indices) in enumerate(zip(key, questions, observed), 1):
        choices = [candidate for candidate in alphabet if all(
            ((fields[name]["series"] * product % m2) * ord(candidate)) % m1 == index
            for name, index in zip(names, indices)
        )]
        if char not in choices:
            raise ValueError(f"Candidate character at position {position} violates the transcript")
        label = "zero-state: all alphabet characters fit" if product == 0 else "candidate-path condition"
        print(f"{position}: state={product}, choices={len(choices)}/{len(alphabet)}, {label}")
        product = product * ord(char) % m2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--questions", type=Path)
    parser.add_argument("--answers", type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--key")
    group.add_argument("--key-file", type=Path)
    parser.add_argument("--alphabet", default="ABCDEF")
    args = parser.parse_args()
    custom = any((args.model, args.questions, args.answers))
    if custom and (not all((args.model, args.questions, args.answers)) or not (args.key or args.key_file)):
        parser.error("Supply model, questions, answers, and a candidate key together")
    if not args.alphabet or len(set(args.alphabet)) != len(args.alphabet):
        parser.error("Alphabet must contain distinct characters")
    model_path = args.model or DEMO / "demo_model.json"
    questions_path = args.questions or DEMO / "demo_questions.txt"
    answers_path = args.answers or DEMO / "demo_answers.txt"
    key = args.key or (read_small(args.key_file).decode("utf-8").rstrip("\r\n") if args.key_file else DEMO_KEY)
    try:
        m1, m2, fields = load_model(model_path)
        questions = [line.split() for line in read_small(questions_path).decode("utf-8").splitlines()]
        answer_bytes = read_small(answers_path)
        answers = answer_bytes.decode("utf-8").splitlines()
        if len(questions) != len(answers) or len(key) != len(questions) or not questions or len(questions) > 5000:
            raise ValueError("Expected one nonempty question and answer line per key character")
        if any(not names or len(names) > 12 or any(name not in fields for name in names) for names in questions):
            raise ValueError("Question contains an unknown field or too many fields")
        observed = [parse_answer(answer, names, fields) for answer, names in zip(answers, questions)]
        generated = render(key, questions, m1, m2, fields)
        print(f"Transcript parity: {generated == answer_bytes}")
        print("Generated SHA-256:", hashlib.sha256(generated).hexdigest())
        print("Observed SHA-256: ", hashlib.sha256(answer_bytes).hexdigest())
        profile(key, questions, observed, args.alphabet, m1, m2, fields)
        if generated != answer_bytes:
            parser.exit(1, "Candidate did not reproduce the answer bytes\n")
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Rejected: {exc}\n")


if __name__ == "__main__":
    main()
