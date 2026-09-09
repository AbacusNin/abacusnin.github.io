// Page script for self.html. Draws a stratified random subset of the
// self-assessment bank on each load (4 items per technique class, split 2
// forward + 2 reverse, plus a couple of exposure items split 1 + 1), renders
// it with the shared labels, and scores it with scoreSelf from app.js
// against exactly that shown subset. The forward/reverse split matters: the
// full bank is balanced per class so a constant answer scores neutral (see
// tests/test_self_assess.py), and drawing an even split each session keeps
// that anti-gaming property true of every sample shown, not just the bank
// as a whole.

import { scoreSelf } from "./app.js";
import { sampleBank, showResult } from "./ui.js";

const STORAGE_KEY = "edl-self-progress";
const PER_CLASS = 4;
const EXPOSURE_COUNT = 2;
const LABELS = [
  "0 strongly disagree",
  "1 disagree",
  "2 neutral",
  "3 agree",
  "4 strongly agree",
];
const el = (id) => document.getElementById(id);

function loadState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? {};
  } catch {
    return {};
  }
}

function saveState(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // storage unavailable (private mode, disabled); the page still scores fine.
  }
}

const state = loadState();

Promise.all([
  fetch("data/config.json").then((r) => r.json()),
  fetch("data/techniques.json").then((r) => r.json()),
  fetch("data/self_assessment.json").then((r) => r.json()),
])
  .then(([config, techniques, selfBank]) => {
    render(config, techniques, selfBank);
  })
  .catch((err) => {
    el("load-error").textContent = `Could not load assessment data: ${err.message}`;
    el("load-error").hidden = false;
  });

function render(config, techniques, selfBank) {
  const shown = sampleBank(selfBank, {
    groupKey: "technique_class",
    perGroup: PER_CLASS,
    balanceKey: "reverse",
    extraFilter: (item) => item.exposure === true,
    extraCount: EXPOSURE_COUNT,
    extraBalanceKey: "reverse",
  });

  const sampleNote = el("sample-note");
  if (sampleNote) {
    sampleNote.textContent = `Showing ${shown.length} of ${selfBank.length} items, drawn fresh each visit.`;
  }

  const container = el("self-items");
  container.textContent = "";
  for (const item of shown) {
    const row = document.createElement("fieldset");
    row.className = "item";
    const legend = document.createElement("legend");
    legend.textContent = item.prompt;
    row.appendChild(legend);
    for (let v = 0; v <= 4; v++) {
      const id = `self-${item.id}-${v}`;
      const label = document.createElement("label");
      label.className = "likert";
      const input = document.createElement("input");
      input.type = "radio";
      input.name = `self-${item.id}`;
      input.value = String(v);
      input.id = id;
      if (state[item.id] === v) input.checked = true;
      input.addEventListener("change", () => {
        state[item.id] = v;
        saveState(state);
      });
      label.appendChild(input);
      label.append(` ${LABELS[v]}`);
      row.appendChild(label);
    }
    container.appendChild(row);
  }

  el("self-run").addEventListener("click", () => {
    // Normalize over exactly what was shown, not the full bank.
    const result = scoreSelf(state, config, techniques, shown);
    showResult("self", result, "general", config);
  });
}
