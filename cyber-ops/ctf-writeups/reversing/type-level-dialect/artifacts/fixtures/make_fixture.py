"""Rebuild the neutral answer transcript for the verifier demo."""

import json
from pathlib import Path


folder = Path(__file__).resolve().parent
model = json.loads((folder / "demo_model.json").read_text(encoding="utf-8"))
questions = [line.split() for line in (folder / "demo_questions.txt").read_text(encoding="utf-8").splitlines()]
key = "ABFCADE"
product = 1
lines = []
for char, names in zip(key, questions):
    forms = []
    for name in names:
        field = model["fields"][name]
        state = field["series"] * product % model["mod_state"]
        index = state * ord(char) % model["mod_form"]
        forms.append(field["forms"][index])
    lines.append(" ".join(forms))
    product = product * ord(char) % model["mod_state"]
(folder / "demo_answers.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
