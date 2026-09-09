// Page script for knowledge.html. Draws a random subset of the knowledge
// bank on each load, renders it, and scores it with scoreKnowledge from
// app.js against exactly that shown subset. Also owns the reporting-context
// selector: context changes which response choice scores as correct, and
// (see responseChoicesForContext below) which response options are shown at
// all, so switching it re-renders the drawn items without resampling.

import { DIMENSIONS, RESPONSE_DISTRACTORS, scoreKnowledge } from "./app.js";
import { renderCompetencyScorecard, sampleBank, shuffle, showResult } from "./ui.js";

const STORAGE_KEY = "edl-knowledge-progress";
const CONTEXT_KEY = "edl-context";
const SAMPLE_COUNT = 9;
const DISTRACTOR_MIN = 3;
const DISTRACTOR_MAX = 4;
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

function loadContext() {
  try {
    return localStorage.getItem(CONTEXT_KEY) ?? "general";
  } catch {
    return "general";
  }
}

function saveContext(context) {
  try {
    localStorage.setItem(CONTEXT_KEY, context);
  } catch {
    // storage unavailable (private mode, disabled); the page still scores fine.
  }
}

const state = loadState();

// The response dimension's option list for the selected reporting context:
// the correct channel for this context (item.report_paths[context], falling
// back to general the same way scoreKnowledge does) plus a random 3-4 of the
// shared wrong-behavior distractors (RESPONSE_DISTRACTORS in app.js). Every
// other context's channel (DoD, FSO, agency IG, and so on) is dropped, so a
// private-industry taker never sees a military or cleared-contractor option
// and vice versa, and the distractors themselves are the same regardless of
// context, so they never leak which regime is correct. Grading is untouched:
// it still compares the chosen id to report_paths[context] in scoreKnowledge.
// Called fresh on every render, so the distractor draw varies visit to visit
// and on each context switch.
function responseChoicesForContext(item, context) {
  const correctId = item.report_paths[context] ?? item.report_paths.general;
  const correctChoice = item.choices.response.find((choice) => choice.id === correctId);
  const distractorCount = DISTRACTOR_MIN + Math.floor(Math.random() * (DISTRACTOR_MAX - DISTRACTOR_MIN + 1));
  const distractors = shuffle(RESPONSE_DISTRACTORS).slice(0, distractorCount);
  return [correctChoice, ...distractors];
}

const contextSelect = el("context");
contextSelect.value = loadContext();

let shownItems = null;

contextSelect.addEventListener("change", () => {
  saveContext(contextSelect.value);
  if (!shownItems) return;
  // The response options just changed out from under any prior pick; drop
  // it rather than leave a now-hidden choice scored against the new
  // context's correct id.
  for (const item of shownItems) {
    if (state[item.id]) delete state[item.id].response;
  }
  saveState(state);
  renderItems(shownItems, contextSelect.value);
});

Promise.all([
  fetch("data/config.json").then((r) => r.json()),
  fetch("data/techniques.json").then((r) => r.json()),
  fetch("data/knowledge.json").then((r) => r.json()),
])
  .then(([config, techniques, knowledgeBank]) => {
    render(config, techniques, knowledgeBank);
  })
  .catch((err) => {
    el("load-error").textContent = `Could not load assessment data: ${err.message}`;
    el("load-error").hidden = false;
  });

function render(config, techniques, knowledgeBank) {
  const shown = sampleBank(knowledgeBank, { count: SAMPLE_COUNT });
  shownItems = shown;

  const sampleNote = el("sample-note");
  if (sampleNote) {
    sampleNote.textContent = `Showing ${shown.length} of ${knowledgeBank.length} scenarios, drawn fresh each visit.`;
  }

  renderItems(shown, contextSelect.value);

  el("knowledge-run").addEventListener("click", () => {
    const context = contextSelect.value;
    // Normalize over exactly what was shown, not the full bank.
    const result = scoreKnowledge(state, config, techniques, shown, context);
    const summary = document.createElement("div");
    summary.appendChild(renderCompetencyScorecard(result, config, techniques));
    summary.appendChild(renderItemFeedback(result.feedback, shown));
    showResult("knowledge", result, context, config, techniques, summary);
  });
}

// Builds the scenario blocks for the drawn subset into #knowledge-items.
// Runs on initial load and again whenever the reporting context changes, off
// the same drawn subset, so switching context doesn't redraw the sample;
// only the response dimension's option list (responseChoicesForContext)
// depends on context.
function renderItems(shown, context) {
  const container = el("knowledge-items");
  container.textContent = "";
  for (const item of shown) {
    state[item.id] = state[item.id] ?? {};
    const block = document.createElement("div");
    block.className = "scenario";
    const p = document.createElement("p");
    p.textContent = item.scenario;
    block.appendChild(p);
    for (const dim of DIMENSIONS) {
      const group = document.createElement("fieldset");
      group.className = "item";
      const legend = document.createElement("legend");
      legend.textContent = dim;
      group.appendChild(legend);
      const choices = dim === "response" ? responseChoicesForContext(item, context) : item.choices[dim];
      // Shuffle the choice order per dimension per render so the correct
      // answer isn't predictably in the same slot every time (it's always
      // choice 0 in the bank data). Scoring compares chosen id to correct
      // id, so this has no effect on grading.
      for (const choice of shuffle(choices)) {
        const label = document.createElement("label");
        label.className = "choice";
        const input = document.createElement("input");
        input.type = "radio";
        input.name = `know-${item.id}-${dim}`;
        input.value = choice.id;
        if (state[item.id][dim] === choice.id) input.checked = true;
        input.addEventListener("change", () => {
          state[item.id][dim] = choice.id;
          saveState(state);
        });
        label.appendChild(input);
        label.append(` ${choice.text}`);
        group.appendChild(label);
      }
      block.appendChild(group);
    }
    container.appendChild(block);
  }
}

const STATUS_LABEL = {
  correct: "Correct",
  partial: "Partial credit",
  incorrect: "Incorrect",
  unanswered: "Not answered",
};

const DIMENSION_LABEL = {
  recognition: "Recognition",
  countermeasure: "Countermeasure",
  response: "Response",
};

// One block per dimension, laid out as separate lines rather than one
// run-on paragraph: a status line (dimension name and correct / partial /
// incorrect / unanswered), then the user's own choice, the correct choice
// when the pick wasn't it, and the explanation for the choice the user
// actually made (scoreKnowledge already resolves that; see dimensionFeedback
// in app.js). Previously this always printed the correct choice's
// explanation regardless of what was picked, so a wrong answer still read
// as "Correct."
function renderDimensionLine(dim, entry) {
  const wrap = document.createElement("div");
  wrap.className = "dim-feedback";

  const status = document.createElement("p");
  status.className = "dim-status";
  status.textContent = `${DIMENSION_LABEL[dim]}: ${STATUS_LABEL[entry.status]}`;
  wrap.appendChild(status);

  if (entry.status === "unanswered") {
    const correct = document.createElement("p");
    correct.textContent = `Correct answer: "${entry.correct_text}"`;
    wrap.appendChild(correct);
  } else {
    const chosen = document.createElement("p");
    chosen.textContent = `You chose: "${entry.chosen_text}"`;
    wrap.appendChild(chosen);
    if (entry.status !== "correct") {
      const correct = document.createElement("p");
      correct.textContent = `Correct answer: "${entry.correct_text}"`;
      wrap.appendChild(correct);
    }
  }

  if (entry.explanation) {
    const explanation = document.createElement("p");
    explanation.className = "dim-explanation";
    explanation.textContent = entry.explanation;
    wrap.appendChild(explanation);
  }

  return wrap;
}

// One card per scored item: the scenario text plus the recognition,
// countermeasure, and response lines, each reflecting the user's own choice
// (right, wrong, or partial) rather than only the correct answer. shown is
// the drawn subset, used to look up each item's scenario text by id.
function renderItemFeedback(feedback, shown) {
  const wrap = document.createElement("div");
  const heading = document.createElement("h3");
  heading.textContent = "Per-item feedback";
  wrap.appendChild(heading);

  const byId = new Map(shown.map((item) => [item.id, item]));
  for (const entry of feedback) {
    const item = byId.get(entry.item_id);
    const card = document.createElement("div");
    card.className = "scenario";
    if (item) {
      const p = document.createElement("p");
      p.textContent = item.scenario;
      card.appendChild(p);
    }
    for (const dim of DIMENSIONS) {
      card.appendChild(renderDimensionLine(dim, entry[dim]));
    }
    wrap.appendChild(card);
  }
  return wrap;
}
