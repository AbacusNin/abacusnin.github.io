// Page script for interaction.html. Renders every item in the interaction
// indicator bank, grouped into five collapsible sections (the four
// psychological classes plus conversational-control patterns), and scores
// it with scoreInteraction from app.js against the full bank. Every load
// shows the whole bank, and every item is answerable regardless of which
// section is expanded.

import { scoreInteraction } from "./app.js";
import { CLASS_LABELS, showResult } from "./ui.js";

const STORAGE_KEY = "edl-interaction-progress";
const CONTEXT_KEY = "edl-context";
const ANSWERS = [
  ["yes", "Yes"],
  ["no", "No"],
  ["unsure", "Unsure"],
];

// Group order and labels. The first four are the psychological classes an
// item's technique belongs to (looked up via technique_id in techniques.json);
// the fifth holds the pattern items (item.pattern === true), which carry no
// technique_id and so never sort into the first four.
const GROUP_ORDER = ["ego", "reciprocity", "social_pressure", "cognitive_cue", "patterns"];
const GROUP_LABELS = {
  ...CLASS_LABELS,
  patterns: "Conversational-control patterns",
};

// One or two sentences per group naming the lever it covers. Grounded in
// elicitation-catalog-comprehensive.md: Catalog A rows for the four
// technique classes, and the cross-cutting detection paragraph after A28 for
// the pattern items.
const GROUP_INTRO = {
  ego: "Ego techniques praise you, doubt you, or criticize your work so you defend it, expand on it, or try to top what they said.",
  reciprocity: "Reciprocity techniques share a confidence, do you a favor, or build rapport fast. The debt that creates gets paid back in information more often than people expect.",
  social_pressure: "Social pressure techniques ask you directly, play ignorant so you teach them, or route a question through someone close to you. Each one banks on the plain habit of answering when asked.",
  cognitive_cue: "Cognitive cue techniques assume you already know something, offer a range for you to correct, ask a question that assumes its own answer, or narrow a broad topic to one detail. Each one makes confirming feel like the natural next thing to do.",
  patterns: "These six items track the shape of a conversation, not one line in it: unusual interest in a topic, deliberate bridging toward it, a high density of questions on the same subject, persistence and circling back, reformulation of a question you didn't answer, and steering paired with mirroring.",
};

// Detection-framed per-class copy for the scorecard, distinct from the
// susceptibility copy ui.js ships for self-assessment (self and interaction
// ask fundamentally different questions: self asks how you would react,
// interaction asks what already happened). A high score here means several
// techniques on that lever were marked as having happened, a signal the
// conversation looked like a deliberate attempt on that lever, not a
// measure of what got disclosed.
const INTERACTION_CLASS_INFO = {
  ego: {
    low: "Praise, doubt, or criticism aimed at your work did not show up here as a pattern.",
    elevated: "Praise, doubt, or criticism aimed at your work showed up a few times in this conversation.",
    high: "Flattery, feigned doubt, criticism, and one-upping showed up together in this conversation. That is a signal this looked like a deliberate attempt on your ego. It does not mean you overshared.",
  },
  reciprocity: {
    low: "Confided secrets, favors, or fast rapport did not show up here as a pattern.",
    elevated: "A confided secret, an unprompted favor, or quick rapport showed up a few times in this conversation.",
    high: "Confided secrets, unprompted favors, attentive listening, and fast rapport showed up together in this conversation. That is a signal this looked like a deliberate attempt to build a felt debt. It does not mean you overshared.",
  },
  social_pressure: {
    low: "Direct questions, surveys, and informal settings did not show up here as a pattern.",
    elevated: "A blunt question, a survey, or a relaxed setting showed up a few times in this conversation.",
    high: "Direct questions, surveys, unverified recruiters, venting, and relaxed off-site settings showed up together in this conversation. That is a signal this looked like a deliberate attempt to press past your judgment. It does not mean you overshared.",
  },
  cognitive_cue: {
    low: "Assumed knowledge, estimates, leading questions, and hypotheticals did not show up here as a pattern.",
    elevated: "An assumed-knowledge opener, a rough estimate, or a leading question showed up a few times in this conversation.",
    high: "Assumed knowledge, bracketed estimates, leading questions, and hypotheticals showed up together in this conversation. That is a signal this looked like a deliberate attempt to draw a confirmation out of you. It does not mean you overshared.",
  },
};

// Overall reading for the interaction scorecard: whether the pattern looks
// like an elicitation attempt and whether it clears the reporting bar, plus
// an explicit reminder that the score reflects observed techniques, not
// disclosure.
const INTERACTION_OVERALL_READING = {
  low: "Few or none of these techniques showed up in this conversation. This does not look like a deliberate elicitation attempt. The result reflects the techniques you marked as happening. It does not measure how much you disclosed.",
  elevated: "Some of these techniques showed up in this conversation. Review the flagged classes below to see which lever they lean on. The result reflects the techniques you marked as happening. It does not measure how much you disclosed.",
  high: "Several of these techniques showed up together in this conversation. That is the pattern a deliberate elicitation attempt leaves. Check the reporting flag below. The result reflects the techniques you marked as happening. It does not measure how much you disclosed.",
};

// A28 (the Scharff technique) carries technique_class "composite" in
// techniques.json, not one of the four base classes: taxonomy/reference.md
// describes it as a composite of reciprocity and cognitive cue. It is
// grouped under reciprocity here so every item still lands in exactly one of
// the five sections.
const CLASS_OVERRIDE = { A28: "reciprocity" };

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

const contextSelect = el("context");
contextSelect.value = loadContext();
contextSelect.addEventListener("change", () => saveContext(contextSelect.value));

Promise.all([
  fetch("data/config.json").then((r) => r.json()),
  fetch("data/techniques.json").then((r) => r.json()),
  fetch("data/interaction.json").then((r) => r.json()),
])
  .then(([config, techniques, interactionBank]) => {
    render(config, techniques, interactionBank);
  })
  .catch((err) => {
    el("load-error").textContent = `Could not load assessment data: ${err.message}`;
    el("load-error").hidden = false;
  });

// Bucket the bank into the five groups, each ordered by id (numeric-aware,
// so a10 sorts after a9 rather than after a1) rather than by diagnosticity,
// so the layout does not telegraph which indicators weigh most.
function groupItems(interactionBank, techniques) {
  const techById = new Map(techniques.map((t) => [t.id, t]));
  const groups = new Map(GROUP_ORDER.map((key) => [key, []]));

  for (const item of interactionBank) {
    if (item.pattern) {
      groups.get("patterns").push(item);
      continue;
    }
    const cls = CLASS_OVERRIDE[item.technique_id] ?? techById.get(item.technique_id)?.technique_class;
    if (groups.has(cls)) groups.get(cls).push(item);
  }

  for (const items of groups.values()) {
    items.sort((a, b) => a.id.localeCompare(b.id, undefined, { numeric: true }));
  }
  return groups;
}

function renderItem(item, container) {
  const row = document.createElement("fieldset");
  row.className = "item";

  const legend = document.createElement("legend");
  legend.textContent = item.label;
  row.appendChild(legend);

  const desc = document.createElement("p");
  desc.textContent = item.description;
  row.appendChild(desc);

  const example = document.createElement("p");
  example.className = "note";
  example.textContent = `Example: ${item.example}`;
  row.appendChild(example);

  const prompt = document.createElement("p");
  const promptStrong = document.createElement("strong");
  promptStrong.textContent = item.pattern
    ? "Did this happen in the conversation?"
    : "Was this technique used on you?";
  prompt.appendChild(promptStrong);
  row.appendChild(prompt);

  for (const [value, label] of ANSWERS) {
    const id = `interaction-${item.id}-${value}`;
    const optLabel = document.createElement("label");
    optLabel.className = "choice";
    const input = document.createElement("input");
    input.type = "radio";
    input.name = `interaction-${item.id}`;
    input.value = value;
    input.id = id;
    if (state[item.id] === value) input.checked = true;
    input.addEventListener("change", () => {
      state[item.id] = value;
      saveState(state);
    });
    optLabel.appendChild(input);
    optLabel.append(` ${label}`);
    row.appendChild(optLabel);
  }

  container.appendChild(row);
}

function render(config, techniques, interactionBank) {
  const groups = groupItems(interactionBank, techniques);

  const groupsContainer = el("interaction-groups");
  groupsContainer.textContent = "";

  const jumpSelect = el("group-jump");
  const detailsByGroup = new Map();

  for (const key of GROUP_ORDER) {
    const items = groups.get(key);

    const details = document.createElement("details");
    details.className = "item-group";
    details.open = true;
    details.id = `group-${key}`;
    detailsByGroup.set(key, details);

    const summary = document.createElement("summary");
    summary.textContent = `${GROUP_LABELS[key]} (${items.length})`;
    details.appendChild(summary);

    const intro = document.createElement("p");
    intro.className = "note";
    intro.textContent = GROUP_INTRO[key];
    details.appendChild(intro);

    for (const item of items) {
      renderItem(item, details);
    }

    groupsContainer.appendChild(details);

    const option = document.createElement("option");
    option.value = key;
    option.textContent = `${GROUP_LABELS[key]} (${items.length})`;
    jumpSelect.appendChild(option);
  }

  jumpSelect.addEventListener("change", () => {
    const key = jumpSelect.value;
    if (!key) return;
    const details = detailsByGroup.get(key);
    details.open = true;
    details.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  el("interaction-run").addEventListener("click", () => {
    const context = contextSelect.value;
    // Only Yes counts as present; Unsure counts as No, same as an unanswered item.
    const present = interactionBank.map((item) => item.id).filter((id) => state[id] === "yes");
    // Score over the full bank: interaction shows every item, no sampling.
    const result = scoreInteraction(present, config, techniques, interactionBank);
    showResult(
      "interaction",
      result,
      context,
      config,
      techniques,
      undefined,
      INTERACTION_CLASS_INFO,
      INTERACTION_OVERALL_READING,
    );
  });
}
