// Shared UI helpers for the three module pages: sampling banks down to a
// shown subset (self and knowledge; interaction now shows its whole bank),
// and rendering a scored result. All three pages render through showResult;
// knowledge.js supplies its own competency scorecard
// (renderCompetencyScorecard) in place of the default one, since its three
// dimensions score correctness, not susceptibility. The raw emitted event and
// the KQL/SPL a defender would query are deliberately not shown here; those
// stay available through buildEvent/detectionQueries in app.js for the CLI,
// the detections, and the parity test, but the end user never sees them.

import { BASE_CLASSES, DIMENSIONS, tierFor } from "./app.js";

function pct(x) {
  return `${(x * 100).toFixed(1)}%`;
}

// Fisher-Yates. Does not mutate the input.
export function shuffle(array) {
  const out = array.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

// Split a pool into two lists by whether opts.balanceKey is truthy on each
// item, draw half of n from each side (shuffled), and concatenate. Used to
// keep a drawn subset balanced forward/reverse so a constant-answer run
// still lands neutral (see sampleBank's balanceKey option below).
function drawBalanced(pool, n, balanceKey) {
  const half = Math.floor(n / 2);
  const trueItems = pool.filter((item) => item[balanceKey]);
  const falseItems = pool.filter((item) => !item[balanceKey]);
  const drawn = shuffle(trueItems).slice(0, half);
  drawn.push(...shuffle(falseItems).slice(0, n - half));
  return drawn;
}

// Draw a subset of a bank for display. Two modes, usable together:
//   - stratified: opts.groupKey names the field to group by (e.g.
//     "technique_class"); opts.perGroup caps how many items are drawn from
//     each group value present in the bank. Items missing that field are
//     skipped by this pass. With opts.balanceKey set (e.g. "reverse"), each
//     group draws an even split of perGroup between items where that field
//     is truthy and where it is falsy, instead of a plain random slice, so
//     every drawn group carries the same forward/reverse mix as the full
//     bank (see self.js: this is what keeps a constant-answer run neutral).
//   - extra: opts.extraFilter picks a side pool (e.g. exposure items) drawn
//     up to opts.extraCount items (all of them if extraCount is omitted).
//     opts.extraBalanceKey applies the same even split to this pool.
//   - plain random: opts.count alone, with neither groupKey nor extraFilter,
//     draws N items from the whole bank.
// The result is shuffled once more before it is returned, so the stratified
// and extra items are not blocked together.
export function sampleBank(bank, opts = {}) {
  const { groupKey, perGroup, balanceKey, extraFilter, extraCount, extraBalanceKey, count } = opts;
  let drawn = [];

  if (groupKey && perGroup) {
    const groups = new Map();
    for (const item of bank) {
      const key = item[groupKey];
      if (key === undefined || key === null) continue;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(item);
    }
    for (const items of groups.values()) {
      if (balanceKey) {
        drawn.push(...drawBalanced(items, perGroup, balanceKey));
      } else {
        drawn.push(...shuffle(items).slice(0, perGroup));
      }
    }
  }

  if (extraFilter) {
    const pool = bank.filter(extraFilter);
    const n = extraCount ?? pool.length;
    if (extraBalanceKey) {
      drawn.push(...drawBalanced(pool, n, extraBalanceKey));
    } else {
      drawn.push(...shuffle(pool).slice(0, n));
    }
  }

  if (!groupKey && !extraFilter && count) {
    drawn = shuffle(bank).slice(0, count);
  }

  return shuffle(drawn);
}

// Plain-language reading of an overall tier.
const TIER_READING = {
  low: "Limited susceptibility to the conversational pressure and pull to disclose covered here.",
  elevated:
    "A moderate pull to disclose under some of these techniques. Review the classes flagged below.",
  high: "A strong pull to disclose under several of these techniques. Treat the flagged classes as a training priority.",
};

// Exported so interaction.js can label its psychological-class accordion
// groups with the same wording the scorecard uses.
export const CLASS_LABELS = {
  ego: "Ego",
  reciprocity: "Reciprocity",
  social_pressure: "Social pressure",
  cognitive_cue: "Cognitive cue",
};

// One line per class per risk tier: what the tier means, and for elevated
// and high, which countermeasures to drill. Grounded in the Catalog A
// elicitation techniques each class covers (elicitation-catalog-comprehensive.md).
const CLASS_INFO = {
  ego: {
    low: "Praise, doubt, and criticism aimed at your work do not appear to pull extra detail out of you.",
    elevated:
      "Praise, doubt, or criticism sometimes pulls more detail out of you than the setting calls for. Practice acknowledging it without expanding.",
    high: "Flattery, feigned doubt, criticism, and one-upping reliably pull extra detail out of you. Drill acknowledging praise or a challenge without expanding, and letting a wrong claim about your work stand uncorrected (flattery, provocation, false statement, criticism, one-upper countermeasures).",
  },
  reciprocity: {
    low: "Offered confidences, favors, or fast rapport do not appear to create a felt obligation to share in return.",
    elevated:
      "A confided secret, an unprompted favor, or quick rapport sometimes tips you toward sharing more than you meant to.",
    high: "Confided secrets, unprompted favors, attentive listening, and fast rapport reliably create a felt debt that gets paid in information. Drill noticing the obligation and declining to trade (confidential bait, quid pro quo, good listener, mutual interest, offering-assistance countermeasures).",
  },
  social_pressure: {
    low: "Direct questions, surveys, and informal settings do not appear to push you past your own limits.",
    elevated:
      "A blunt question, a survey, or a relaxed setting sometimes pushes you to answer before you have judged whether you should.",
    high: "Direct questions, surveys, unverified recruiters, venting, and relaxed off-site settings reliably override your judgment about what to share. Drill pausing before a direct ask and holding the same discretion off-site as in the office (direct question, survey, ruse interview, urge-to-complain, setting-manipulation countermeasures).",
  },
  cognitive_cue: {
    low: "Assumed knowledge, estimates, leading questions, and hypotheticals do not appear to draw confirmations out of you.",
    elevated:
      "An assumed-knowledge opener, a rough estimate, or a leading question sometimes draws a confirming detail out of you.",
    high: "Assumed knowledge, bracketed estimates, leading questions, and hypotheticals reliably draw confirming detail out of you. Drill verifying what someone actually knows before you fill a gap, and refusing to narrow a range or engage a hypothetical on sensitive ground (assumed-knowledge, bracketing, leading-question, hypothetical countermeasures).",
  },
};

function riskFor(score, config) {
  return tierFor(score, config);
}

// Knowledge-check dimension labels and readings. These are a distinct set from
// TIER_READING/CLASS_INFO above: on self and interaction a high class score
// means the technique pulls disclosure out of you (bad), but on the knowledge
// check a high dimension score means you answered correctly (good). Reusing
// the susceptibility wording here would tell a weak scorer they look safe, so
// the knowledge scorecard gets its own reading text instead.
const DIMENSION_LABELS = {
  recognition: "Recognition",
  countermeasure: "Countermeasure",
  response: "Response",
};

const OVERALL_COMPETENCY_READING = {
  low: "Weak overall competency: recognition, countermeasure, or reporting-response answers are missing the mark across these scenarios. Treat this as a training priority.",
  elevated:
    "Moderate overall competency: some of these scenarios land correctly, but not consistently across recognition, countermeasure, and response.",
  high: "Strong overall competency: you are reliably naming the technique, picking the taught countermeasure, and reporting through the right channel.",
};

// One line per dimension per tier: what a low, elevated, or high score in
// that dimension means in practice. The low line is the headline case the
// scorecard is built to surface (weak recognition = missing the pattern,
// weak countermeasure = no practiced response, weak response = wrong or no
// report), per the module's design brief.
const DIMENSION_INFO = {
  recognition: {
    low: "You are not reliably spotting these techniques as they happen; the pattern is going unnoticed in the moment.",
    elevated:
      "You catch some of these techniques but miss others, especially close look-alikes from the same class.",
    high: "You are reliably naming the technique in play, including telling close look-alikes apart.",
  },
  countermeasure: {
    low: "Even when you notice a technique, you are not reaching for the taught response; the technique would likely still get the detail it's after.",
    elevated:
      "You sometimes reach for a softer, instinctive reaction instead of the practiced response, such as going quiet or leaving rather than declining while staying in the conversation.",
    high: "You are reliably applying the taught countermeasure, not just an instinctive workaround.",
  },
  response: {
    low: "You would say the wrong thing or not report at all; the reporting channel for your selected context is not landing.",
    elevated: "You partially get the reporting response right, but not consistently for this context.",
    high: "You are reliably reporting through the correct channel for your selected context.",
  },
};

// Color-code by performance, not by the risk-tier direction the CSS classes
// were named for: a high knowledge score is the good outcome, so it borrows
// the green risk-low styling, and a low score borrows the flagged risk-high
// styling. The label text still prints the literal low/elevated/high tier.
function competencyStyleClass(tier) {
  if (tier === "high") return "risk-low";
  if (tier === "low") return "risk-high";
  return "risk-elevated";
}

// Per-class hit rate for the items actually shown and answered this round,
// derived straight from result.feedback (each entry already carries the
// per-dimension 0/0.5/1 score against the user's own choice). This is
// deliberately not result.class_scores: that figure is normalized against
// the full technique catalog (matching the Python scorer's ceiling), so a
// 9-of-30 sample leaves most classes far short of their ceiling even on a
// perfect run, and a class with nothing drawn this round reads as 0%
// instead of untested. Returns null for a class with no items this round so
// the caller can print "not tested" instead of a misleading zero.
function classPerformance(feedback, techniques) {
  const classById = new Map(techniques.map((t) => [t.id, t.technique_class]));
  const sums = {};
  const counts = {};
  for (const entry of feedback) {
    const cls = classById.get(entry.technique_id);
    if (!BASE_CLASSES.includes(cls)) continue;
    const itemScore = DIMENSIONS.reduce((acc, dim) => acc + entry[dim].score, 0) / DIMENSIONS.length;
    sums[cls] = (sums[cls] ?? 0) + itemScore;
    counts[cls] = (counts[cls] ?? 0) + 1;
  }
  const out = {};
  for (const cls of BASE_CLASSES) {
    out[cls] = counts[cls] ? { score: sums[cls] / counts[cls], count: counts[cls] } : null;
  }
  return out;
}

// Render the knowledge check's competency scorecard: an overall competency
// tier, then the three scored dimensions (recognition, countermeasure,
// response) each with their own low/elevated/high indicator and a line on
// what that means. The four-class technique profile is included as a
// secondary breakdown of hit rate per class, scoped to what was actually
// drawn and answered this round (see classPerformance above) rather than
// through renderScorecard, since renderScorecard's class readings are
// written for susceptibility, not correctness, and would read backwards
// here. `techniques` is used to map each fed-back item's technique_id to its
// class. Returns a detached DOM node; the caller inserts it into the page.
export function renderCompetencyScorecard(result, config, techniques) {
  const wrap = document.createElement("div");
  wrap.className = "scorecard";

  const overall = document.createElement("p");
  const tierStrong = document.createElement("strong");
  tierStrong.textContent = `${result.tier} (${pct(result.overall_score)})`;
  overall.append("Overall competency: ", tierStrong, ". ", OVERALL_COMPETENCY_READING[result.tier] ?? "");
  wrap.appendChild(overall);

  const list = document.createElement("ul");
  list.className = "scorecard-classes";
  for (const dim of DIMENSIONS) {
    const score = result.dimension_scores[dim];
    const tier = riskFor(score, config);
    const li = document.createElement("li");
    li.className = competencyStyleClass(tier);
    const head = document.createElement("strong");
    head.textContent = `${DIMENSION_LABELS[dim]}: ${tier} (${pct(score)})`;
    li.appendChild(head);
    const line = document.createElement("p");
    line.textContent = DIMENSION_INFO[dim][tier];
    li.appendChild(line);
    list.appendChild(li);
  }
  wrap.appendChild(list);

  const secondary = document.createElement("details");
  secondary.className = "class-profile";
  const summary = document.createElement("summary");
  summary.textContent = "Technique-class breakdown (secondary)";
  secondary.appendChild(summary);
  const classList = document.createElement("ul");
  classList.className = "scorecard-classes";
  const perf = classPerformance(result.feedback, techniques);
  for (const cls of BASE_CLASSES) {
    const li = document.createElement("li");
    const clsPerf = perf[cls];
    li.textContent = clsPerf
      ? `${CLASS_LABELS[cls]}: ${pct(clsPerf.score)} correct (${clsPerf.count} scenario${clsPerf.count === 1 ? "" : "s"} this round)`
      : `${CLASS_LABELS[cls]}: not tested this round`;
    classList.appendChild(li);
  }
  secondary.appendChild(classList);
  wrap.appendChild(secondary);

  return wrap;
}

// Who to report to, by reporting context. Mirrors the response choices in
// taxonomy/banks/knowledge.json (report_paths -> resp_* text) so the two
// modules describe the same channels the same way.
const REPORT_TO = {
  general: "Report it through your organization's designated security or CI reporting channel.",
  dod: "Report it to your servicing counterintelligence element or supporting Military Department CI organization (or your security officer, supervisor, or commander if none is available), per DoD Directive 5240.06 (CIAR).",
  federal: "Report it to your agency's security officer or Inspector General hotline.",
  cleared_contractor: "Report the contact to your Facility Security Officer, per NISPOM (32 CFR Part 117).",
  private_industry: "Report it to your company's security, compliance, or corporate security team.",
};

// Render a scored result as a scorecard: the overall tier with a
// plain-language reading, and each of the four classes with its own risk
// indicator (low / elevated / high) plus one line on what that means and
// which countermeasures to drill. Returns a detached DOM node; the caller
// inserts it wherever the page wants it. `context` is optional and only
// changes the reporting-flag line: when it names a known reporting context
// the flag names who to report to, otherwise it falls back to the generic
// wording. `techniques` is optional and only changes how matched_techniques
// (module results that carry it, e.g. interaction) render: with it, ids are
// shown as "A1 Flattery"; without it, as bare ids. `classInfo` and
// `overallReading` default to the self-assessment susceptibility copy
// (CLASS_INFO/TIER_READING); interaction.js passes its own detection-framed
// copy instead, since a high class score there means techniques were
// observed, not that the user overshared.
export function renderScorecard(result, config, context, techniques, classInfo = CLASS_INFO, overallReading = TIER_READING) {
  const wrap = document.createElement("div");
  wrap.className = "scorecard";

  const overall = document.createElement("p");
  const tierStrong = document.createElement("strong");
  tierStrong.textContent = `${result.tier} (${pct(result.overall_score)})`;
  overall.append("Overall: ", tierStrong, ". ", overallReading[result.tier] ?? "");
  wrap.appendChild(overall);

  // The reporting flag is the headline risk indicator: it goes right under
  // the overall tier, ahead of the per-class breakdown. Only interaction's
  // result carries a reporting_flag key at all (true or false); self and
  // knowledge results have none, so this block never fires for them.
  if (result.reporting_flag !== undefined) {
    const flag = document.createElement("p");
    if (result.reporting_flag) {
      flag.className = "flag";
      const reportTo = REPORT_TO[context];
      flag.textContent = reportTo
        ? `Reporting threshold met: this interaction meets the bar to report. ${reportTo}`
        : "Reporting threshold met: this interaction meets the bar to report.";
    } else {
      flag.className = "note";
      flag.textContent = "No report is indicated based on what you marked as happening.";
    }
    wrap.appendChild(flag);
  }

  const list = document.createElement("ul");
  list.className = "scorecard-classes";
  for (const cls of BASE_CLASSES) {
    const score = result.class_scores[cls];
    const risk = riskFor(score, config);
    const li = document.createElement("li");
    li.className = `risk-${risk}`;
    const head = document.createElement("strong");
    head.textContent = `${CLASS_LABELS[cls]}: ${risk} (${pct(score)})`;
    li.appendChild(head);
    const line = document.createElement("p");
    line.textContent = classInfo[cls][risk];
    li.appendChild(line);
    list.appendChild(li);
  }
  wrap.appendChild(list);

  if (result.matched_techniques && result.matched_techniques.length) {
    const byId = new Map((techniques ?? []).map((t) => [t.id, t]));
    const matchedWrap = document.createElement("div");
    matchedWrap.className = "matched-techniques";
    const heading = document.createElement("strong");
    heading.textContent = "Matched techniques: ";
    matchedWrap.appendChild(heading);
    const names = result.matched_techniques.map((id) => {
      const t = byId.get(id);
      return t ? `${id} ${t.name}` : id;
    });
    matchedWrap.append(names.join(", "));
    wrap.appendChild(matchedWrap);
  }

  return wrap;
}

// Fill in the result panel every module page shares. Pass config to get the
// scorecard rendering (per-class risk indicators); without it this falls
// back to a plain score list, so pages that have not moved onto
// renderScorecard yet still work unchanged. `techniques` is optional and
// only used to name matched_techniques ids in the scorecard. `customSummary`,
// if given, is a prebuilt DOM node (e.g. from renderCompetencyScorecard) used
// in place of the default scorecard, for modules whose result shape needs
// its own summary layout. `classInfo` and `overallReading`, if given, are
// forwarded to renderScorecard in place of its self-assessment defaults (see
// renderScorecard above); interaction.js passes its own detection-framed
// copy this way. This only renders the scorecard: the emitted event and the
// KQL/SPL a defender would query never reach the page (see app.js's
// buildEvent/detectionQueries for those, used by the CLI and the parity
// test). `module` is accepted for a consistent call signature across pages
// even though it is unused now that the event panel is gone.
export function showResult(module, result, context, config, techniques, customSummary, classInfo, overallReading) {
  const el = (id) => document.getElementById(id);
  el("result").hidden = false;

  const summary = el("result-summary");
  summary.textContent = "";

  if (customSummary) {
    summary.appendChild(customSummary);
  } else if (config) {
    const args = [result, config, context, techniques];
    if (classInfo) args.push(classInfo, overallReading ?? TIER_READING);
    summary.appendChild(renderScorecard(...args));
  } else {
    const head = document.createElement("p");
    const scoreStrong = document.createElement("strong");
    scoreStrong.textContent = pct(result.overall_score);
    const tierStrong = document.createElement("strong");
    tierStrong.textContent = result.tier;
    head.append("Overall ", scoreStrong, ", tier ", tierStrong, ".");
    summary.appendChild(head);

    const classList = document.createElement("ul");
    for (const cls of BASE_CLASSES) {
      const li = document.createElement("li");
      li.textContent = `${cls}: ${pct(result.class_scores[cls])}`;
      classList.appendChild(li);
    }
    summary.appendChild(classList);

    if (result.reporting_flag) {
      const flag = document.createElement("p");
      flag.className = "flag";
      flag.textContent = "Reporting threshold met: this run would raise a reporting flag.";
      summary.appendChild(flag);
    }
  }

  el("result").scrollIntoView({ behavior: "smooth" });
}
