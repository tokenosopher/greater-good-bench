/* A Little Better — plain words, careful decisions, kind speech, compounding kindness. */

/* ============================================================
   Tabs
   ============================================================ */
const tabs = Array.from(document.querySelectorAll(".tab"));
const panels = Array.from(document.querySelectorAll(".panel"));

function activatePanel(name) {
  tabs.forEach((t) => {
    const on = t.dataset.panel === name;
    t.setAttribute("aria-selected", String(on));
    t.classList.toggle("is-active", on);
  });
  panels.forEach((p) => {
    const on = p.id === "panel-" + name;
    p.hidden = !on;
    p.classList.toggle("is-active", on);
  });
}

tabs.forEach((t) =>
  t.addEventListener("click", () => {
    activatePanel(t.dataset.panel);
    try { history.replaceState(null, "", "#" + t.dataset.panel); } catch (_) {}
    t.focus();
  })
);

/* keyboard: left/right arrows move between tabs */
tabs.forEach((t, i) =>
  t.addEventListener("keydown", (e) => {
    let n = null;
    if (e.key === "ArrowRight") n = (i + 1) % tabs.length;
    if (e.key === "ArrowLeft") n = (i - 1 + tabs.length) % tabs.length;
    if (e.key === "Home") n = 0;
    if (e.key === "End") n = tabs.length - 1;
    if (n !== null) {
      e.preventDefault();
      tabs[n].focus();
      tabs[n].click();
    }
  })
);

/* deep-link on load */
const startPanel = (location.hash || "").replace("#", "");
if (tabs.some((t) => t.dataset.panel === startPanel)) activatePanel(startPanel);

/* ============================================================
   Plain Words — readability analysis
   ============================================================ */

/* Curated replacements: jargon & filler -> plain. */
const PLAIN = new Map([
  ["utilize", "use"], ["utilize", "use"], ["utilise", "use"], ["utilization", "use"],
  ["utilise", "use"], ["utilized", "used"], ["utilised", "used"], ["utilizing", "using"],
  ["utilising", "using"], ["facilitate", "help"], ["facilitates", "helps"], ["facilitated", "helped"],
  ["facilitating", "helping"], ["facilitation", "help"], ["endeavor", "try"], ["endeavour", "try"],
  ["endeavors", "tries"], ["endeavoring", "trying"], ["endeavouring", "trying"],
  ["commence", "begin"], ["commences", "begins"], ["commenced", "began"], ["commencing", "beginning"],
  ["commencement", "start"], ["terminate", "end"], ["terminated", "ended"], ["termination", "end"],
  ["ascertain", "find out"], ["ascertained", "found out"], ["request", "ask"], ["requested", "asked"],
  ["purchase", "buy"], ["purchased", "bought"], ["purchasing", "buying"], ["obtain", "get"],
  ["obtained", "got"], ["obtaining", "getting"], ["subsequent", "later"], ["subsequently", "later"],
  ["prior to", "before"], ["in order to", "to"], ["in the event that", "if"], ["in the event of", "if"],
  ["with regard to", "about"], ["regarding", "about"], ["concerning", "about"],
  ["in relation to", "about"], ["in respect of", "about"], ["in regards to", "about"],
  ["at this point in time", "now"], ["at the present time", "now"], ["at this time", "now"],
  ["a number of", "some"], ["the majority of", "most"], ["a large number of", "many"],
  ["a small number of", "a few"], ["due to the fact that", "because"], ["owing to the fact that", "because"],
  ["for the purpose of", "to"], ["for the purposes of", "for"], ["in order that", "so that"],
  ["in addition", "also"], ["in addition to", "besides"], ["as well as", "and"],
  ["notwithstanding", "despite"], ["aforementioned", "the"], ["heretofore", "before"],
  ["hereinafter", "below"], ["hereby", "now"], ["therein", "in it"], ["thereof", "of it"],
  ["herewith", "here"], ["in the near future", "soon"], ["in the foreseeable future", "soon"],
  ["it is important to note that", "note that"], ["it should be noted that", "note that"],
  ["it is worth noting that", "note that"], ["needless to say", ""], ["as a matter of fact", ""],
  ["in actual fact", ""], ["in point of fact", ""], ["the fact that", "that"], ["the fact remains that", ""],
  ["in spite of the fact that", "although"], ["despite the fact that", "although"],
  ["on a daily basis", "daily"], ["on a regular basis", "regularly"], ["on a weekly basis", "weekly"],
  ["on an annual basis", "yearly"], ["in a timely manner", "on time"], ["in a timely fashion", "quickly"],
  ["at all times", "always"], ["at any time", "anytime"], ["at no time", "never"],
  ["each and every", "each"], ["first and foremost", "first"], ["basic fundamentals", "basics"],
  ["close proximity", "near"], ["completely eliminate", "remove"], ["completely filled", "filled"],
  ["completely finished", "finished"], ["general consensus", "consensus"], ["past history", "history"],
  ["future plans", "plans"], ["advance planning", "planning"], ["advance warning", "warning"],
  ["final conclusion", "conclusion"], ["final outcome", "outcome"], ["end result", "result"],
  ["free gift", "gift"], ["new innovation", "innovation"], ["new invention", "invention"],
  ["new initiative", "initiative"], ["revert back", "reply"], ["collaborate together", "work together"],
  ["merge together", "merge"], ["combine together", "combine"], ["repeat again", "repeat"],
  ["return back", "return"], ["postpone until later", "postpone"], ["advance forward", "advance"],
  ["proceed forward", "proceed"], ["sufficient", "enough"], ["sufficiently", "enough"],
  ["insufficient", "not enough"], ["numerous", "many"], ["additional", "more"], ["additional", "extra"],
  ["approximately", "about"], ["approximately", "around"], ["attempt", "try"], ["attempting", "trying"],
  ["demonstrate", "show"], ["demonstrated", "showed"], ["demonstrates", "shows"], ["demonstrating", "showing"],
  ["indicate", "show"], ["indicated", "showed"], ["indicates", "shows"], ["initial", "first"],
  ["initially", "at first"], ["assist", "help"], ["assistance", "help"], ["assisting", "helping"],
  ["adequate", "enough"], ["inadequate", "not enough"], ["require", "need"], ["required", "needed"],
  ["requires", "needs"], ["requiring", "needing"], ["requirements", "needs"], ["requirement", "need"],
  ["advise", "tell"], ["informed", "told"], ["inform", "tell"], ["immediately", "now"],
  ["regrettably", "sadly"], ["unfortunately", "sadly"], ["aforementioned", "the"],
  ["above-mentioned", "the"], ["the aforementioned", "the"], ["the following", "these"],
  ["the following", "this"], ["circulated", "sent"], ["circulate", "send"], ["disseminate", "share"],
  ["disseminated", "shared"], ["dissemination", "sharing"], ["expedite", "speed up"], ["expedited", "sped up"],
  ["expeditiously", "quickly"], ["implement", "carry out"], ["implemented", "carried out"],
  ["implementation", "setup"], ["implementing", "carrying out"], ["in the process of", ""],
  ["in the course of", "during"], ["in the midst of", "during"], ["is able to", "can"],
  ["are able to", "can"], ["was able to", "could"], ["were able to", "could"], ["be able to", "can"],
  ["modalities", "ways"], ["paradigm", "model"], ["leverage", "use"], ["leveraging", "using"],
  ["leveraged", "used"], ["synergy", "teamwork"], ["synergies", "teamwork"], ["synergistic", "working together"],
  ["robust", "strong"], ["optimize", "improve"], ["optimized", "improved"], ["optimization", "improvement"],
  ["operationalize", "put into practice"], ["of an operational nature", ""], ["proactively", "early"],
  ["incentivize", "encourage"], ["incentivized", "encouraged"], ["actionable", "practical"],
  ["bandwidth", "capacity"], ["best practice", "good way"], ["best practices", "good ways"],
  ["scalable", "growable"], ["cutting-edge", "new"], ["state-of-the-art", "modern"], ["innovative", "new"],
  ["circling back", "returning to"], ["touch base", "check in"], ["reaching out", "contacting"],
  ["reach out", "contact"], ["reached out", "contacted"], ["moving forward", "from now on"],
  ["going forward", "from now on"], ["at the end of the day", "in the end"], ["it goes without saying", ""],
  ["very", ""], ["really", ""], ["extremely", "very"], ["actually", ""], ["basically", ""],
  ["essentially", ""], ["literally", ""], ["honestly", ""], ["just", ""], ["quite", ""],
  ["a little bit", "slightly"], ["a bit", "slightly"], ["kind of", "somewhat"], ["sort of", "somewhat"],
  ["in my opinion", "I think"], ["i think that", "I think"], ["i feel like", "I think"],
  ["i believe that", "I think"], ["the reason why", "the reason"], ["the reason why is that", "because"],
  ["the reason is because", "because"], ["the reason is that", "because"], ["due to", "because of"],
  ["in light of", "because of"], ["in view of", "because of"], ["as a result of", "because of"],
  ["as a consequence of", "because of"], ["resulting in", "causing"], ["in the amount of", "of"],
  ["in a position to", "able to"], ["not in a position to", "unable to"], ["with the exception of", "except"],
  ["in terms of", "in"], ["in the field of", "in"], ["in the area of", "in"], ["in the realm of", "in"],
  ["per annum", "a year"], ["per annum", "yearly"], ["per diem", "daily"], ["enclosed please find", "here is"],
  ["attached please find", "here is"], ["please find attached", "I have attached"], ["thank you in advance", "thank you"],
  ["i am writing to", ""], ["this is to inform you that", ""], ["we regret to inform you that", "sadly,"],
  ["we are pleased to inform you that", "good news:"], ["please be advised that", ""],
  ["please be informed that", ""], ["it is requested that", "please"], ["you are requested to", "please"],
  ["we would like to", "we want to"], ["we would like to inform you", "this is to tell you"],
  ["we would like to request", "we ask"], ["we would like to thank", "we thank"],
  ["i would like to", "I want to"], ["i would appreciate it if", "please"], ["i would be grateful if", "please"],
  ["we apologize for", "we are sorry about"], ["we apologize for any inconvenience", "sorry for the trouble"],
  ["please do not hesitate to contact", "please contact"], ["should you have any questions", "if you have questions"],
  ["if you have any questions", "if you have questions"], ["do not hesitate to", ""],
  ["aforementioned", "the"], ["the undersigned", "I"], ["without further delay", "now"],
  ["without further ado", ""], ["in conclusion", "finally"], ["to summarize", "in short"],
  ["it is evident that", "clearly"], ["it is clear that", "clearly"], ["it is obvious that", "clearly"],
  ["there is a need for", "we need"], ["there is a possibility that", "possibly"],
  ["there is a chance that", "maybe"], ["afford the opportunity", "let"], ["has the ability to", "can"],
  ["has the capability to", "can"], ["possess", "have"], ["possesses", "has"], ["possessed", "had"],
  ["reside", "live"], ["residence", "home"], ["approximately", "about"],
]);

const FILLER = ["very", "really", "just", "actually", "basically", "essentially", "literally", "quite", "extremely", "totally", "absolutely", "definitely", "obviously", "stuff", "things", "so" ];

/* multi-word phrases to check first (longest-first so we replace whole phrases) */
const PLAIN_PHRASES = Array.from(PLAIN.keys())
  .filter((k) => k.includes(" "))
  .sort((a, b) => b.split(" ").length - a.split(" ").length);

/* Rough syllable counter (good enough for readability heuristics). */
function countSyllables(word) {
  const w = word.toLowerCase().replace(/[^a-z]/g, "");
  if (!w) return 0;
  const t = w
    .replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, "")
    .replace(/^y/, "")
    .replace(/([^laeiouy])y/g, "$1");
  const vowels = (t.match(/[aeiouy]{1,2}/g) || []).length;
  return Math.max(1, vowels);
}

/* split text roughly into sentences for averaging */
function splitSentences(text) {
  const parts = text
    .split(/(?<=[.!?]+)\s+|\n+/)
    .map((s) => s.trim())
    .filter((s) => /\w/.test(s));
  return parts.length ? parts : [text.trim()];
}

function analyzeText(text) {
  const words = text.trim().length ? text.trim().split(/\s+/) : [];
  const cleanWords = words.map((w) => w.toLowerCase().replace(/^[^a-z0-9]+|[^a-z0-9]+$/g, "")).filter(Boolean);
  const sentences = splitSentences(text).length;
  const syllables = cleanWords.reduce((n, w) => n + countSyllables(w), 0);
  const avgSentence = sentences ? words.length / sentences : 0;

  let flesch = 0, ari = 0, grade = null;
  if (cleanWords.length && sentences) {
    flesch = 206.835 - 1.015 * (words.length / sentences) - 84.6 * (syllables / cleanWords.length);
    ari = 4.71 * (cleanWords.join("").length / cleanWords.length) + 0.5 * (words.length / sentences) - 21.43;
    // blend the two into one friendly "grade"
    grade = Math.max(1, Math.round((ari + (16 - flesch / 9)) / 2));
  }
  return { words, cleanWords, sentences, syllables, avgSentence, grade, ari };
}

/* long words after excluding common endings */
function isHardWord(w) {
  if (w.length < 7) return false;
  if (countSyllables(w) < 3) return false;
  if (/(ing|ed|es|ly|tion|sion|ment|ness|ful|less|able|ible|ance|ence|ship|hood|ous|ive|ish)$/.test(w)) return false;
  return true;
}

function renderClarity() {
  const raw = document.getElementById("clarity-input").value;
  const text = raw;
  const a = analyzeText(text);
  const hasText = a.cleanWords.length > 0;

  document.getElementById("m-words").textContent = a.words.length;
  document.getElementById("m-sentences").textContent = a.sentences;
  document.getElementById("m-avg").textContent = a.sentences ? a.avgSentence.toFixed(1) + " words" : "—";
  document.getElementById("m-time").textContent = hasText ? Math.max(1, Math.round(a.words.length / 220)) + " min" : "—";

  const gradeNum = document.getElementById("grade-num");
  const ring = document.getElementById("gauge-ring");
  const label = document.getElementById("grade-label");

  if (!hasText || a.grade === null) {
    gradeNum.textContent = "—";
    ring.style.setProperty("--pct", 0);
    ring.className = "gauge-ring";
    label.textContent = "Add text to see its reading level.";
    document.getElementById("m-hard").textContent = "0";
    document.getElementById("btn-simplify").disabled = true;
  } else {
    gradeNum.textContent = a.grade;
    const pct = Math.min(100, Math.max(0, (a.grade / 15) * 100));
    ring.style.setProperty("--pct", Math.round(pct).toString());
    const hardCount = a.cleanWords.filter((w) => isHardWord(w)).length;
    document.getElementById("m-hard").textContent = hardCount;
    document.getElementById("btn-simplify").disabled = false;

    let cls = "", msg = "";
    if (a.grade <= 8) { cls = "easy"; msg = "Easy to read — most people can follow this easily."; }
    else if (a.grade <= 11) { cls = ""; msg = "Moderate — fine for many, slightly heavy for general readers."; }
    else { cls = "hard"; msg = "Dense — simplify so more people can follow it."; }
    // color blend: any grade should still show proportion; treat >11 as "hard" color
    ring.className = "gauge-ring " + cls;
    label.textContent = msg;
  }

  renderInsights(a, text);
}

function renderInsights(a, text) {
  const box = document.getElementById("clarity-insights");
  const list = document.getElementById("insight-list");
  list.innerHTML = "";
  const items = [];
  if (!a.cleanWords.length) { box.hidden = true; return; }

  /* long sentences */
  const longish = splitSentences(text).filter((s) => s.split(/\s+/).length > 22);
  if (longish.length) {
    items.push({ kind: "ok", title: "Long sentences", body: longish.length + " sentence" + (longish.length > 1 ? "s" : "") + " run over 22 words. Split the longest one at its commas; short beats elegant." });
  }

  /* filler words */
  const fillerHits = a.cleanWords.filter((w) => FILLER.includes(w));
  if (fillerHits.length) {
    items.push({ kind: "ok", title: "Filler words", body: "\u201c" + [...new Set(fillerHits)].slice(0, 6).join("\u201d, \u201c") + "\u201d " + (fillerHits.length === 1 ? "adds" : "add") + " nothing. Try deleting " + (fillerHits.length === 1 ? "it" : "them") + " and see if the sentence stands." });
  }

  /* hard words */
  const hards = [...new Set(a.cleanWords.filter((w) => isHardWord(w) && w.length >= 8))].slice(0, 6);
  if (hards.length) {
    items.push({ kind: "ok", title: "Big words", body: "\u201c" + hards.join("\u201d, \u201c") + "\u201d — each has a shorter friend. Using a plain word isn\u2019t dumbing down; it\u2019s opening a door." });
  }

  /* passive voice (heuristic) */
  const passiveRe = /\b(am|is|are|was|were|be|been|being)\s+(\w+ed)\b/gi;
  const passiveHits = (text.match(passiveRe) || []).slice(0, 5);
  if (passiveHits.length) {
    items.push({ kind: "ok", title: "Passive voice", body: "e.g. \u201c" + passiveHits.join("\u201d, \u201c") + "\u201d. Say who did the thing — \u201cWe closed the office,\u201d not \u201cThe office was closed.\u201d" });
  }

  if (!items.length) {
    items.push({ kind: "good", title: "Looking clear", body: "No obvious fog here. Reading level " + a.grade + " is " + (a.grade <= 8 ? "comfortable for almost everyone." : "workable — a touch more short sentences and it\u2019ll reach everyone.") });
  }

  items.forEach((it) => {
    const li = document.createElement("li");
    li.className = "insight " + it.kind;
    const s = document.createElement("strong");
    s.textContent = it.title;
    li.appendChild(s);
    li.appendChild(document.createTextNode(it.body));
    list.appendChild(li);
  });
  box.hidden = false;
}

/* Preserve capitalization when a lowercase replacement sits at a capital start. */
function maybeCap(match, rep) {
  if (!rep) return rep;
  if (/^[A-Z]/.test(match) && /^[a-z]/.test(rep)) return rep[0].toUpperCase() + rep.slice(1);
  return rep;
}

/* Apply curated simplifications (matches phrases, then single words). */
function applySimplify() {
  const el = document.getElementById("clarity-input");
  let text = el.value;
  let changed = 0;
  for (const phrase of PLAIN_PHRASES) {
    const re = new RegExp("\\b" + phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b", "gi");
    text = text.replace(re, (m) => { changed++; return maybeCap(m, PLAIN.get(phrase)); });
  }
  for (const [from, to] of PLAIN) {
    if (from.includes(" ")) continue;
    const re = new RegExp("\\b" + from + "\\b", "gi");
    text = text.replace(re, (m) => { changed++; return maybeCap(m, to); });
  }
  /* clean up doubled spaces, doubled punctuation, and punctuation spacing */
  text = text.replace(/\s{2,}/g, " ")
    .replace(/\s+([,.;:!?])/g, "$1")
    .replace(/([,.;:!?])\1+/g, "$1")
    .replace(/([,.;:!?])(?=[A-Za-z])/g, "$1 ");
  el.value = text;
  if (changed === 0) {
    flashButton(document.getElementById("btn-simplify"), "Already quite plain!");
  }
  renderClarity();
}

function flashButton(btn, msg) {
  const old = btn.textContent;
  btn.textContent = msg;
  setTimeout(() => { btn.textContent = old; }, 1400);
}

const EXAMPLE_TEXT =
  "We regret to inform you that, due to unforeseen circumstances of an operational nature, the aforementioned service will be temporarily suspended in order to facilitate necessary improvements. " +
  "Utilising state-of-the-art technology, we endeavour to implement robust solutions that leverage synergy across teams to optimize the customer experience going forward. " +
  "At the end of the day, it is important to note that we are literally working around the clock to expedite a resolution. Please do not hesitate to reach out should you have any questions. " +
  "In the event that problems persist, subsequent updates will be disseminated in a timely manner prior to termination of the outage.";

document.getElementById("clarity-input").addEventListener("input", renderClarity);
document.getElementById("btn-simplify").addEventListener("click", applySimplify);
document.getElementById("btn-clear").addEventListener("click", () => {
  document.getElementById("clarity-input").value = "";
  renderClarity();
});
document.getElementById("btn-sample").addEventListener("click", () => {
  document.getElementById("clarity-input").value = EXAMPLE_TEXT;
  renderClarity();
});

/* ============================================================
   Decision Compass
   ============================================================ */
const compassState = { options: [], step: 0 };
const TOTAL_STEPS = 6;

const optionInputs = {
  0: ["c-decision", "c-why"],
  1: ["c-affected"],
  4: ["c-universal", "c-year"],
};

function renderProgress() {
  const cont = document.getElementById("steps-progress");
  cont.innerHTML = "";
  for (let i = 0; i < TOTAL_STEPS; i++) {
    const li = document.createElement("li");
    if (i < compassState.step) li.className = "done";
    else if (i === compassState.step) li.className = "current";
    cont.appendChild(li);
  }
}

function stepIsComplete(idx) {
  if (idx === 2) return compassState.options.length >= 2 && compassState.options.every((o) => o.text.trim());
  if (idx === 3) return compassState.options.length >= 2;
  if (idx === 0) return ["c-decision", "c-why"].every((id) => document.getElementById(id).value.trim());
  if (idx === 1) return document.getElementById("c-affected").value.trim().length > 0;
  if (idx === 4) return ["c-universal", "c-year"].every((id) => document.getElementById(id).value.trim());
  return true;
}

function renderStep() {
  for (let i = 0; i < TOTAL_STEPS; i++) {
    const el = document.getElementById("step-" + i);
    el.hidden = i !== compassState.step;
  }
  renderProgress();
  const next = document.getElementById("btn-next");
  const prev = document.getElementById("btn-prev");
  prev.disabled = compassState.step === 0;
  next.textContent = compassState.step === TOTAL_STEPS - 1 ? "Finish" : "Next →";
  next.disabled = !stepIsComplete(compassState.step);
  next.hidden = compassState.step === TOTAL_STEPS - 1;
  prev.hidden = compassState.step === TOTAL_STEPS - 1;
  if (compassState.step === TOTAL_STEPS - 1) renderSummary();
}

function makeRemoveBtn(onRemove, label) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "remove";
  b.textContent = "✕";
  b.setAttribute("aria-label", label);
  b.addEventListener("click", onRemove);
  return b;
}

function renderOptions() {
  const list = document.getElementById("option-list");
  list.innerHTML = "";
  compassState.options.forEach((opt, i) => {
    const row = document.createElement("div");
    row.className = "option-row";
    const input = document.createElement("input");
    input.type = "text";
    input.value = opt.text;
    input.placeholder = "Option " + (i + 1) + " — the actual thing you could do";
    input.setAttribute("aria-label", "Option " + (i + 1));
    input.addEventListener("input", (e) => {
      compassState.options[i].text = e.target.value;
      refreshNext();
    });
    row.appendChild(input);
    if (compassState.options.length > 2) {
      const x = makeRemoveBtn(() => {
        compassState.options.splice(i, 1);
        renderOptions();
        refreshNext();
      }, "Remove option " + (i + 1));
      row.appendChild(x);
    }
    list.appendChild(row);
  });
}

function renderWeigh() {
  const list = document.getElementById("weigh-list");
  list.innerHTML = "";
  compassState.options.forEach((opt, i) => {
    const item = document.createElement("div");
    item.className = "weigh-item";
    const h = document.createElement("h4");
    h.textContent = opt.text.trim().slice(0, 80) || "Option " + (i + 1);
    item.appendChild(h);

    const mk = (label, key) => {
      const wrap = document.createElement("div");
      wrap.className = "weigh-pair";
      const lb = document.createElement("label");
      lb.textContent = label;
      const inp = document.createElement("input");
      inp.type = "text";
      inp.value = opt[key] || "";
      inp.placeholder = "…";
      inp.addEventListener("input", (e) => { opt[key] = e.target.value; });
      wrap.appendChild(lb);
      wrap.appendChild(inp);
      return wrap;
    };
    item.appendChild(mk("What gets better, and for whom?", "pro"));
    item.appendChild(mk("What gets worse, and for whom?", "con"));
    list.appendChild(item);
  });
}

function refreshNext() {
  document.getElementById("btn-next").disabled = !stepIsComplete(compassState.step);
}

function nextStep() {
  if (compassState.step < TOTAL_STEPS - 1) {
    if (compassState.step === 1) refreshNext();
    compassState.step++;
    if (compassState.step === 3) renderWeigh();
    renderStep();
    document.querySelector(".compass").scrollIntoView({ behavior: "smooth", block: "start" });
  }
}
function prevStep() {
  if (compassState.step > 0) {
    compassState.step--;
    renderStep();
  }
}

function addOption() {
  compassState.options.push({ text: "", pro: "", con: "" });
  renderOptions();
  const inputs = document.querySelectorAll("#option-list input");
  inputs[inputs.length - 1].focus();
  refreshNext();
}

function renderSummary() {
  const s = compassState;
  const lines = [];
  const read = (id) => document.getElementById(id).value.trim();
  const decision = read("c-decision");
  const why = read("c-why");
  const affected = read("c-affected").split("\n").map((s) => s.trim()).filter(Boolean);
  const universal = read("c-universal");
  const year = read("c-year");

  lines.push("◆ MY DECISION");
  lines.push("Decision: " + (decision || "—"));
  lines.push("Why it matters: " + (why || "—"));
  lines.push("");
  lines.push("◆ WHO IT AFFECTS");
  lines.push(affected.length ? affected.map((a, i) => (i + 1) + ". " + a).join("\n") : "—");
  lines.push("");
  lines.push("◆ MY OPTIONS");
  s.options.forEach((o, i) => {
    lines.push((i + 1) + ". " + (o.text || "—"));
    lines.push("   Better: " + (o.pro || "—"));
    lines.push("   Worse:  " + (o.con || "—"));
  });
  lines.push("");
  lines.push("◆ HONESTY TESTS");
  lines.push("Would I want everyone to choose this?  " + (universal || "—"));
  lines.push("Will I be glad in a year?  " + (year || "—"));
  lines.push("");
  lines.push("◆ ONE NEXT STEP");
  lines.push("Decide the one smallest step I can take today toward my choice — or the one fact I still need to learn — and do it now.");

  document.getElementById("compass-summary").textContent = lines.join("\n");
}

async function copySummary() {
  const text = document.getElementById("compass-summary").textContent;
  const note = document.getElementById("copied-note");
  try {
    await navigator.clipboard.writeText(text);
    note.textContent = "Copied — it\u2019s yours to keep, review, and act on.";
  } catch (_) {
    note.textContent = "Copying isn\u2019t allowed here — select the text above and copy it yourself.";
  }
}

document.getElementById("btn-add-option").addEventListener("click", addOption);
document.getElementById("btn-next").addEventListener("click", nextStep);
document.getElementById("btn-prev").addEventListener("click", prevStep);
document.getElementById("btn-copy-summary").addEventListener("click", copySummary);
document.getElementById("btn-restart").addEventListener("click", () => {
  compassState.step = 0;
  compassState.options = [{ text: "", pro: "", con: "" }, { text: "", pro: "", con: "" }];
  ["c-decision", "c-why", "c-affected", "c-universal", "c-year"].forEach((id) => (document.getElementById(id).value = ""));
  renderOptions();
  renderStep();
});

/* live re-validation for text steps */
["c-decision", "c-why", "c-affected", "c-universal", "c-year"].forEach((id) =>
  document.getElementById(id).addEventListener("input", refreshNext)
);

/* ============================================================
   Kind Speech — three lenses
   ============================================================ */
const LENSES = [
  { id: "true", name: "☀  Is it true?", desc: "Can I stand behind every claim, or am I filling gaps with certainty I don\u2019t have?" },
  { id: "necessary", name: "✦  Is it necessary?", desc: "Does this need to be said, by me, right now — or is silence the kinder and more effective reply?" },
  { id: "kind", name: "♡  Is it kind — and is it said kindly?", desc: "Even true and needed words can land as a wound or a bridge. The tone decides." },
];

const KIND_PROMPTS = {
  true: [
    "Contains \u201calways\u201d or \u201cnever\u201d —absolute words that are rarely literally true. Soften to \u201coften\u201d or \u201csometimes.\u201d",
    "Contains \u201cyou always\u201d / \u201cyou never\u201d — this is a character verdict, not a fact. Say the specific behaviour instead.",
  ],
  necessary: [
    "Seems to restate something you\u2019ve already said — check if the point has been made and can now stop.",
    "Has a strong emotional charge — if the goal is to persuade, waiting a few hours rarely hurts and often helps.",
  ],
  kind: [
    "Short, clipped sentences with no warmth — one genuine line of appreciation can carry the whole message better.",
    "Commands without \u201cplease\u201d or a reason — people do hard things more willingly when they understand the why.",
  ],
};

function analyzeKind() {
  const text = document.getElementById("kind-input").value.trim();
  const list = document.querySelector(".lens-list");
  list.innerHTML = "";
  if (!text) return;

  const lc = text.toLowerCase();
  const words = lc.split(/\s+/);
  const shots = LENSES.map((lens) => {
    let state = "kind"; let note = "";
    /* true */
    if (lens.id === "true") {
      if (/\b(always|never)\b/.test(lc)) { state = "warn"; note = KIND_PROMPTS.true[0]; }
      else if (/\byou\s+(always|never|constantly|only)\b/.test(lc)) { state = "warn"; note = KIND_PROMPTS.true[1]; }
      else if (/\b(obviously|everyone knows|clearly|of course)\b/.test(lc)) { state = "warn"; note = "Calls something \u201cobvious\u201d — a subtle way to make dissent feel foolish. State the reasoning instead."; }
      else note = "No absolutes spotted. If you can back every sentence with evidence, this lens passes.";
    }
    /* necessary */
    else if (lens.id === "necessary") {
      if (/\b(sorry but|no offense|not to be rude|i don't mean to|with all due respect)\b/.test(lc)) { state = "warn"; note = "A pre-apology (\u201csorry but\u2026\u201d) usually signals the point is more wound than tool. Find the need underneath and say that plainly."; }
      else if (text.split(/\s+/).length > 120) { state = "warn"; note = "Quite long for a message — length dilutes. One clear point, said once, is stronger than ten points."; }
      else note = "No filler or hedging spotted. It looks like it earns its place.";
    }
    /* kind */
    else {
      const harsh = /\b(stupid|idiot|dumb|useless|worthless|hate|lazy|incompetent|pathetic|fool|moron|screw|shut up|shame on)\b/.test(lc);
      const raw = /[!?]{2,}/.test(text);
      if (harsh) { state = "hurt"; note = "Contains a name for a person, not a description of a problem. Swap the insult for the specific thing that went wrong — \u201cthe report arrived late\u201d instead of \u201cyou\u2019re lazy.\u201d"; }
      else if (raw) { state = "warn"; note = "Stacked punctuation (!!, ?!?) reads as shouting. One mark expresses the point; ten marks make people stop reading."; }
      else if (/\b(must|have to|need to|don't|stop|never)\b/.test(lc) && !/\b(please|thanks|thank you)\b/.test(lc)) { state = "warn"; note = "Commands without a please or a reason. Add why it matters and what you\u2019re asking, not just what to do."; }
      else if (/\b(thanks|thank you|appreciate|grateful|great|good work|well done|nice job)\b/.test(lc)) { state = "kind"; note = "Includes genuine appreciation or positive acknowledgement — that\u2019s the bridge the other two lenses need."; }
      else note = "No insults or shouting. A calm delivery of a hard truth is still kindness.";
    }
    return { lens, state, note };
  });

  shots.forEach(({ lens, state, note }) => {
    const li = document.createElement("li");
    li.className = "lens " + state;
    const h = document.createElement("h3");
    h.textContent = lens.name;
    const v = document.createElement("span");
    v.className = "verdict";
    v.textContent = state === "kind" ? "ok" : state === "warn" ? "watch" : "stop";
    h.appendChild(v);
    const p = document.createElement("p");
    p.textContent = note;
    li.appendChild(h);
    li.appendChild(p);
    list.appendChild(li);
  });
}

const KIND_EXAMPLES = [
  "You ALWAYS forget my meetings. You're obviously not taking this seriously and honestly I'm done with people like you. Sort yourself out immediately or don't bother showing up again.",
  "Sorry but this report is useless. No offense but you clearly didn't read the brief and I need you to redo the entire thing right now.",
  "Hey — the report landed after my deadline yesterday, and I couldn't use it in the deck. It's put me in a tough spot for Friday's review. Could we sit down for ten minutes and figure out a handoff that works for both of us before the next one? I really do appreciate how much work went into it. Thanks.",
];

document.getElementById("kind-input").addEventListener("input", analyzeKind);
document.getElementById("btn-kind-clear").addEventListener("click", () => {
  document.getElementById("kind-input").value = "";
  document.querySelector(".lens-list").innerHTML = "";
  document.getElementById("kind-input").focus();
});
let kindExampleIdx = 0;
document.getElementById("btn-kind-sample").addEventListener("click", () => {
  document.getElementById("kind-input").value = KIND_EXAMPLES[kindExampleIdx++ % KIND_EXAMPLES.length];
  analyzeKind();
});

/* ============================================================
   The Ripple — compounding kindness
   ============================================================ */
const rippleForm = document.getElementById("ripple-form");
const rippleAct = document.getElementById("ripple-act");
const rippleCustomRow = document.getElementById("ripple-custom-row");
const rippleCustomLabel = document.getElementById("ripple-custom-label");
const rippleYears = document.getElementById("ripple-years");
const rippleYearsOut = document.getElementById("ripple-years-out");

rippleAct.addEventListener("change", () => {
  const custom = rippleAct.value === "custom";
  rippleCustomRow.hidden = !custom;
  rippleCustomLabel.hidden = !custom;
  if (custom) document.getElementById("ripple-custom").focus();
  updateRipple();
});
rippleYears.addEventListener("input", () => { rippleYearsOut.textContent = rippleYears.value + (rippleYears.value === "1" ? " year" : " years"); updateRipple(); });
["ripple-custom", "ripple-custom-n"].forEach((id) => document.getElementById(id).addEventListener("input", updateRipple));

function perDay() {
  if (rippleAct.value === "custom") {
    const n = parseInt(document.getElementById("ripple-custom-n").value, 10);
    return isNaN(n) ? 0 : Math.max(0, n);
  }
  return parseFloat(rippleAct.value) || 0;
}

function updateRipple() {
  const days = parseInt(rippleYears.value, 10) * 365;
  const n = perDay();
  const total = n * days;
  const actLabel = rippleAct.value === "custom"
    ? (document.getElementById("ripple-custom").value.trim() || "your small act")
    : rippleAct.options[rippleAct.selectedIndex].text.replace(/\s*\(.*\)$/, "");

  const el = document.getElementById("ripple-result");
  if (n > 0 && total > 0) {
    const per = perDay();
    el.innerHTML = "Over <strong>" + rippleYears.value + " " + (rippleYears.value === "1" ? "year" : "years") + "</strong>, \u201c" + escapeHtml(actLabel) + "\u201d, " + per + " a day, adds up to <span class='num'>&nbsp;" + total.toLocaleString("en-US") + "\u00a0" + (total === 1 ? "time" : "times") + "</span>.";
  } else {
    el.innerHTML = "Pick an act and a pace, and the numbers will follow.";
  }
  drawRipple(n, days, actLabel);
}

function drawRipple(n, days, actLabel) {
  const svg = document.getElementById("ripple-svg");
  const W = 400, H = 300, padL = 46, padR = 16, padT = 20, padB = 46;
  const innerW = W - padL - padR, innerH = H - padT - padB;
  const years = parseInt(rippleYears.value, 10);
  const points = years > 1 ? 40 : 10;
  const max = Math.max(1, n * days);

  let path = "";
  for (let i = 0; i <= points; i++) {
    const t = i / points;
    const x = padL + t * innerW;
    const y = padT + innerH - (t * Math.pow(t, 0.5) / 1) * innerH; // decelerating growth visual: area-ish feel
    path += (i === 0 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1) + " ";
  }

  const area = path + "L" + (padL + innerW).toFixed(1) + " " + (padT + innerH).toFixed(1) + " L" + padL.toFixed(1) + " " + (padT + innerH).toFixed(1) + " Z";

  const grid = [];
  for (let g = 0; g <= 5; g++) {
    const y = padT + (innerH / 5) * g;
    grid.push("<line x1='" + padL + "' y1='" + y.toFixed(1) + "' x2='" + (W - padR) + "' y2='" + y.toFixed(1) + "' class='grid'/>");
  }

  svg.innerHTML =
    "<defs><linearGradient id='fill' x1='0' y1='0' x2='0' y2='1'>" +
    "<stop offset='0%' stop-color='" + accentColor() + "' stop-opacity='0.35'/>" +
    "<stop offset='100%' stop-color='" + accentColor() + "' stop-opacity='0.02'/>" +
    "</linearGradient></defs>" +
    grid.join("") +
    "<path d='" + area + "' fill='url(#fill)'/>" +
    "<path d='" + path + "' fill='none' stroke='" + accentColor() + "' stroke-width='3' stroke-linecap='round'/>" +
    "<circle cx='" + (padL + innerW).toFixed(1) + "' cy='" + (padT + innerH - innerH).toFixed(1) + "' r='5' fill='" + accentColor() + "'/>" +
    "<text x='" + (padL - 8) + "' y='" + (padT + innerH + 18).toFixed(1) + "' class='axis'>0</text>" +
    "<text x='" + (W - padR - 40) + "' y='" + (padT + innerH + 18).toFixed(1) + "' class='axis' text-anchor='end'>" + years + (years === 1 ? " year" : " years") + "</text>" +
    "<text x='" + (padL + 2).toFixed(1) + "' y='" + (H - 6) + "' class='axis-end'>" + max.toLocaleString("en-US") + " in total</text>";

  const cap = document.getElementById("ripple-caption");
  cap.textContent = n > 0
    ? "Each small act looks flat at first — the upward sweep is time, not effort, doing the work."
    : "Add an act to see the curve.";
}

function accentColor() {
  return getComputedStyle(document.documentElement).getPropertyValue("--accent")?.trim() || "#c0562f";
}

rippleForm.addEventListener("submit", (e) => e.preventDefault());
document.getElementById("ripple-act").addEventListener("change", updateRipple);

/* Today's one-degree turn */
const TODAY_ACTS = [
  "Thank one person who\u2019s helped you and never heard it back.",
  "Explain one thing patiently to someone who\u2019s stuck.",
  "Pick up the next three pieces of litter you pass.",
  "Message one person who might be lonely tonight.",
  "Give one specific, honest compliment.",
  "Let someone merge, cut in, or go first — and smile.",
  "Ask a quiet person for their opinion and actually listen.",
  "Say what you mean about one thing, plainly, instead of hinting.",
  "Do one chore that\u2019s normally someone else\u2019s.",
  "Read one thing from the point of view you disagree with.",
];
let todayIdx = Math.floor(Math.random() * TODAY_ACTS.length);
function nextToday() {
  todayIdx = (todayIdx + 1) % TODAY_ACTS.length;
  document.getElementById("today-act").textContent = TODAY_ACTS[todayIdx];
}
document.getElementById("btn-today").addEventListener("click", nextToday);

/* ============================================================
   Init
   ============================================================ */
function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

compassState.options = [{ text: "", pro: "", con: "" }, { text: "", pro: "", con: "" }];
renderOptions();
renderStep();
renderClarity();
analyzeKind();
updateRipple();
document.getElementById("today-act").textContent = TODAY_ACTS[todayIdx];