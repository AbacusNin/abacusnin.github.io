// Client-side scoring for the elicitation defense lab.
//
// The three scorers below are line-for-line ports of the Python scorers in
// elicitation_defense_lab/score/. They read the same config.json, techniques,
// and banks that build_data.py froze into web/data/, and tests/test_parity.py
// pins them to the Python numbers so the two implementations cannot drift.
// Sums run in the same order as Python so the floating-point results match.
// The one deliberate divergence is scoreKnowledge's feedback array: the
// Python version keys each dimension's explanation to the correct choice
// only, but that array is dropped before the parity comparison (see
// tests/parity/run_js.mjs), so the JS side builds a richer per-dimension
// object here (chosen vs. correct id/text, score, status) for the page to
// render what the user actually picked.
//
// Pure module: no DOM access, no side effects on import. tests/parity/run_js.mjs
// and each page's own module script (self.js, interaction.js, knowledge.js) both
// import straight from here.

export const BASE_CLASSES = ["ego", "reciprocity", "social_pressure", "cognitive_cue"];
export const DIMENSIONS = ["recognition", "countermeasure", "response"];

// Wrong-behavior distractors for the knowledge check's response dimension,
// shared across every item instead of duplicated into each item's bank
// entry: the doctrine's response guidance (remain noncommittal, do not
// investigate or confront, report promptly) is the same regardless of which
// reporting context the taker picked, so these do not leak or depend on a
// regime the way the report_paths channels do. knowledge.js draws a random
// subset of these alongside the context-correct channel on each render; the
// feedback map below is what dimensionFeedback falls back to when the user
// picks one of these instead of the item's own choices.
export const RESPONSE_DISTRACTORS = [
  {
    id: "resp_investigate_yourself",
    text: "Try to find out who they are, or follow up yourself to gather more information.",
    feedback:
      "Investigating or identifying the person yourself is not the taught response; note the details and report them rather than running your own inquiry.",
  },
  {
    id: "resp_keep_engaging",
    text: "Play along and keep the conversation going to see what else they ask about.",
    feedback:
      "Continuing to engage keeps you exposed to further elicitation and delays the one action that actually matters, which is reporting the contact.",
  },
  {
    id: "resp_mention_coworker",
    text: "Mention it casually to a coworker and leave it there.",
    feedback:
      "Telling a coworker informally is not a report; it has to go through your actual reporting channel, not word of mouth.",
  },
  {
    id: "resp_wait_for_repeat",
    text: "Report it only if the same person approaches you again.",
    feedback:
      "The first contact is already reportable on its own; waiting for a repeat approach just delays a report that should happen promptly.",
  },
  {
    id: "resp_confront_directly",
    text: "Confront the person directly and accuse them of trying to extract information.",
    feedback:
      "Confronting the person tips off a trained collector that you noticed, without accomplishing anything a report wouldn't.",
  },
  {
    id: "resp_ignore_it",
    text: "Let it go; it was not a big deal.",
    feedback: "Elicitation attempts are reportable; letting it go skips the primary countermeasure.",
  },
  {
    id: "resp_handle_quietly",
    text: "Handle it quietly yourself and decide later whether it is worth reporting.",
    feedback:
      "Deciding on your own whether it's worth reporting substitutes your judgment for the process; the doctrine calls for reporting promptly, not self-adjudicating.",
  },
];

const RESPONSE_DISTRACTOR_FEEDBACK = new Map(RESPONSE_DISTRACTORS.map((d) => [d.id, d.feedback]));

export function tierFor(score, config) {
  if (score >= config.tier_thresholds.high) return "high";
  if (score >= config.tier_thresholds.elevated) return "elevated";
  return "low";
}

// hits: {technique_id: hit_score}. Buckets hits by class, weights them, and
// normalizes each class against the max achievable for that class. Non-base
// (composite/none) and unknown technique ids are ignored, matching common.py.
export function weightedClassScores(hits, techniques, config) {
  const byId = new Map(techniques.map((t) => [t.id, t]));
  const raw = {};
  const ceiling = {};
  for (const cls of BASE_CLASSES) {
    raw[cls] = 0.0;
    ceiling[cls] = 0.0;
  }

  for (const t of techniques) {
    if (!BASE_CLASSES.includes(t.technique_class)) continue;
    const weight = config.technique_weights[t.id] ?? t.default_weight;
    const classWeight = config.class_weights[t.technique_class] ?? 1.0;
    ceiling[t.technique_class] += weight * classWeight;
  }

  for (const [techId, hitScore] of Object.entries(hits)) {
    const t = byId.get(techId);
    if (t === undefined || !BASE_CLASSES.includes(t.technique_class)) continue;
    const weight = config.technique_weights[t.id] ?? t.default_weight;
    const classWeight = config.class_weights[t.technique_class] ?? 1.0;
    raw[t.technique_class] += hitScore * weight * classWeight;
  }

  const out = {};
  for (const cls of BASE_CLASSES) {
    out[cls] = ceiling[cls] > 0 ? raw[cls] / ceiling[cls] : 0.0;
  }
  return out;
}

function itemValue(item, answer) {
  if (!Number.isInteger(answer) || answer < 0 || answer > 4) {
    throw new Error(`answer for ${item.id} must be an integer 0-4, got ${answer}`);
  }
  const value = answer / 4;
  return item.reverse ? 1 - value : value;
}

export function scoreSelf(answers, config, techniques, bank) {
  const classSums = {};
  const classCounts = {};
  for (const cls of BASE_CLASSES) {
    classSums[cls] = 0.0;
    classCounts[cls] = 0;
  }
  let exposureSum = 0.0;
  let exposureCount = 0;

  const byId = new Map(bank.map((item) => [item.id, item]));
  for (const [itemId, answer] of Object.entries(answers)) {
    const item = byId.get(itemId);
    if (item === undefined) continue;
    const value = itemValue(item, answer);
    if (item.exposure) {
      exposureSum += value;
      exposureCount += 1;
    } else if (BASE_CLASSES.includes(item.technique_class)) {
      classSums[item.technique_class] += value;
      classCounts[item.technique_class] += 1;
    }
  }

  const classScores = {};
  for (const cls of BASE_CLASSES) {
    classScores[cls] = classCounts[cls] ? classSums[cls] / classCounts[cls] : 0.0;
  }
  const exposureScore = exposureCount ? exposureSum / exposureCount : 0.0;

  let weightTotal = 0.0;
  for (const cls of BASE_CLASSES) weightTotal += config.class_weights[cls] ?? 1.0;
  let classComponent = 0.0;
  if (weightTotal) {
    let acc = 0.0;
    for (const cls of BASE_CLASSES) acc += classScores[cls] * (config.class_weights[cls] ?? 1.0);
    classComponent = acc / weightTotal;
  }
  const overallScore = (classComponent + exposureScore) / 2;

  return {
    overall_score: overallScore,
    tier: tierFor(overallScore, config),
    class_scores: classScores,
    exposure_score: exposureScore,
  };
}

export function scoreInteraction(present, config, techniques, bank) {
  const byId = new Map(bank.map((item) => [item.id, item]));
  let totalDiagnosticity = 0.0;
  for (const item of bank) totalDiagnosticity += item.diagnosticity;
  let presentDiagnosticity = 0.0;
  for (const itemId of present) {
    if (byId.has(itemId)) presentDiagnosticity += byId.get(itemId).diagnosticity;
  }
  const overallScore = totalDiagnosticity ? presentDiagnosticity / totalDiagnosticity : 0.0;

  const hits = {};
  const matchedTechniques = [];
  for (const itemId of present) {
    const item = byId.get(itemId);
    if (item === undefined || item.technique_id === undefined) continue;
    hits[item.technique_id] = 1.0;
    matchedTechniques.push(item.technique_id);
  }

  return {
    overall_score: overallScore,
    tier: tierFor(overallScore, config),
    class_scores: weightedClassScores(hits, techniques, config),
    matched_techniques: matchedTechniques,
    reporting_flag: overallScore >= config.reporting_threshold,
  };
}

function responseCorrectId(item, context) {
  return item.report_paths[context] ?? item.report_paths.general;
}

function dimensionScore(item, dimension, chosen, correctId) {
  if (chosen === correctId) return 1.0;
  if (item.partial && item.partial[dimension] === chosen) return 0.5;
  return 0.0;
}

// Text for a choice id within one dimension of one item. Used to render what
// the user actually picked, not just the correct choice. The response
// dimension's choice list no longer carries the shared wrong-behavior
// distractors (see RESPONSE_DISTRACTORS above), so a response id missing
// from the item falls back to that shared pool before giving up.
function choiceText(item, dimension, choiceId) {
  if (choiceId === undefined || choiceId === null) return null;
  const choice = item.choices[dimension].find((c) => c.id === choiceId);
  if (choice) return choice.text;
  if (dimension === "response") {
    const distractor = RESPONSE_DISTRACTORS.find((d) => d.id === choiceId);
    if (distractor) return distractor.text;
  }
  return choiceId;
}

// Per-dimension feedback for one scored item: what the user chose (id and
// text), the correct choice (id and text), the 0/0.5/1 score already computed
// for it, a correct/partial/incorrect/unanswered status, and the explanation
// text for the choice the user actually made (falling back to the correct
// choice's explanation when nothing was chosen). This is what lets the page
// show "you picked X, which was wrong; the correct answer was Y" instead of
// always printing the correct answer's explanation.
function dimensionFeedback(item, dimension, chosenId, correctId, score) {
  let status;
  if (chosenId === undefined || chosenId === null) status = "unanswered";
  else if (score === 1.0) status = "correct";
  else if (score === 0.5) status = "partial";
  else status = "incorrect";

  const explanationId = chosenId ?? correctId;
  // Item-level feedback covers the item's own choices; a response id not
  // found there is one of the shared wrong-behavior distractors, whose
  // explanation lives in RESPONSE_DISTRACTOR_FEEDBACK instead (see
  // RESPONSE_DISTRACTORS above).
  const fallback = dimension === "response" ? RESPONSE_DISTRACTOR_FEEDBACK.get(explanationId) : undefined;
  return {
    chosen_id: chosenId ?? null,
    chosen_text: choiceText(item, dimension, chosenId),
    correct_id: correctId,
    correct_text: choiceText(item, dimension, correctId),
    score,
    status,
    explanation: item.feedback[dimension][explanationId] ?? fallback ?? null,
  };
}

export function scoreKnowledge(answers, config, techniques, bank, context) {
  const dimSums = {};
  const dimCounts = {};
  for (const dim of DIMENSIONS) {
    dimSums[dim] = 0.0;
    dimCounts[dim] = 0;
  }
  const hits = {};
  const feedback = [];

  for (const item of bank) {
    const answer = answers[item.id];
    if (answer === undefined || answer === null) continue;

    const correctIds = {
      recognition: item.correct.recognition,
      countermeasure: item.correct.countermeasure,
      response: responseCorrectId(item, context),
    };

    let itemTotal = 0.0;
    const perDimension = {};
    for (const dim of DIMENSIONS) {
      const chosen = answer[dim];
      const score = dimensionScore(item, dim, chosen, correctIds[dim]);
      itemTotal += score;
      dimSums[dim] += score;
      dimCounts[dim] += 1;
      perDimension[dim] = dimensionFeedback(item, dim, chosen, correctIds[dim], score);
    }

    hits[item.technique_id] = itemTotal / DIMENSIONS.length;

    feedback.push({
      item_id: item.id,
      technique_id: item.technique_id,
      ...perDimension,
    });
  }

  const dimensionScores = {};
  for (const dim of DIMENSIONS) {
    dimensionScores[dim] = dimCounts[dim] ? dimSums[dim] / dimCounts[dim] : 0.0;
  }

  const weights = config.knowledge_dimension_weights;
  let weightTotal = 0.0;
  for (const dim of DIMENSIONS) weightTotal += weights[dim] ?? 1.0;
  let overallScore = 0.0;
  if (weightTotal) {
    let acc = 0.0;
    for (const dim of DIMENSIONS) acc += dimensionScores[dim] * (weights[dim] ?? 1.0);
    overallScore = acc / weightTotal;
  }

  return {
    overall_score: overallScore,
    tier: tierFor(overallScore, config),
    class_scores: weightedClassScores(hits, techniques, config),
    dimension_scores: dimensionScores,
    feedback,
  };
}

// ---------------------------------------------------------------------------
// Event assembly: mirrors elicitation_defense_lab/schema.py build_event so the
// JSON the page shows matches what the CLI would emit for the same run.
// ---------------------------------------------------------------------------

const SCHEMA_VERSION = "1.0";
const INSTRUMENT_VERSION = "1.0";

export function buildEvent(module, result, context) {
  const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  return {
    schema_version: SCHEMA_VERSION,
    instrument_version: INSTRUMENT_VERSION,
    module,
    tier: result.tier,
    overall_score: result.overall_score,
    class_scores: result.class_scores,
    timestamp,
    context,
    subject_id: null,
    peer_group: null,
    dimension_scores: result.dimension_scores ?? null,
    matched_techniques: result.matched_techniques ?? null,
    reporting_flag: result.reporting_flag ?? null,
  };
}

// The detection queries a defender would run over the emitted event. These match
// the ElicitationAssessment table/index the Task 13 detections build against.
export function detectionQueries(event) {
  const kql = [
    "ElicitationAssessment",
    `| where module == "${event.module}"`,
    "| where tier in (\"elevated\", \"high\")",
  ];
  if (event.reporting_flag) kql.push("| where reporting_flag == true");
  kql.push("| project timestamp, subject_id, module, tier, overall_score, class_scores");

  const spl = [
    `index=elicitation_assessment module="${event.module}" (tier="elevated" OR tier="high")`,
  ];
  if (event.reporting_flag) spl.push("reporting_flag=true");
  spl.push("| table _time subject_id module tier overall_score");

  return { kql: kql.join("\n"), spl: spl.join(" ") };
}
