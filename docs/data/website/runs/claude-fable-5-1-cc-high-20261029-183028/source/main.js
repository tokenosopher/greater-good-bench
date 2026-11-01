import { LESSONS, QUICK, FINAL_QUIZ } from "./lessons.js";
import { REGIONS, DEFAULT_REGION } from "./regions.js";
import * as D from "./drills.js";
import { el } from "./util.js";

const state = {
  region: REGIONS.find((r) => r.id === DEFAULT_REGION),
  learned: new Set(),   // lesson ids marked learned (session only; storage is unavailable offline)
  drilled: new Set(),   // drill credits
  bestScore: null,
  view: { name: "home" },
};
const leaveFns = [];
const main = document.getElementById("main");
const toastEl = el("div", { class: "toast", role: "status", "aria-live": "polite" });
document.body.append(toastEl);
let toastT = null;

const ctx = {
  sub,
  toast(msg) { toastEl.textContent = msg; toastEl.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => toastEl.classList.remove("show"), 1800); },
  onLeave(fn) { leaveFns.push(fn); },
  credit(key) { state.drilled.add(key); },
};

function sub(text) {
  const crisis = state.region.crisis ? `${state.region.crisis}, or find one at findahelpline.com` : "a local crisis line (search “crisis line” + your country, or findahelpline.com)";
  return text.replaceAll("{{N}}", state.region.num).replaceAll("{{C}}", crisis);
}

/* ---------- region ---------- */
const regionSel = document.getElementById("region");
REGIONS.forEach((r) => regionSel.append(el("option", { value: r.id }, r.name)));
try {
  const lang = (navigator.language || "").toLowerCase();
  const guess = { "en-us": "us", "en-ca": "us", "fr-ca": "us", "en-gb": "uk", "en-au": "au", "en-nz": "nz", "en-in": "in", "hi": "in", "ja": "jp", "zh-cn": "cn", "ko": "kr", "pt-br": "br", "es-mx": "mx", "en-za": "za", "tr": "tr", "ru": "ru", "uk": "ua", "de": "eu", "fr": "eu", "es": "eu", "it": "eu", "nl": "eu", "pl": "eu", "sv": "eu", "da": "eu", "fi": "eu", "pt": "eu", "el": "eu", "cs": "eu", "hu": "eu", "ro": "eu", "en-ie": "ie" };
  const id = guess[lang] || guess[lang.split("-")[0]];
  if (id) state.region = REGIONS.find((r) => r.id === id);
} catch (e) {}
regionSel.value = state.region.id;
regionSel.onchange = () => { state.region = REGIONS.find((r) => r.id === regionSel.value); updatePill(); render(); };
function updatePill() { document.getElementById("emergency-pill").textContent = `Emergency: ${state.region.num}`; }
document.getElementById("brand").onclick = () => go({ name: "home" });

/* ---------- navigation ---------- */
function go(view) {
  state.view = view;
  render();
  window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  main.focus({ preventScroll: true });
}
function render() {
  while (leaveFns.length) { try { leaveFns.pop()(); } catch (e) {} }
  main.innerHTML = "";
  const v = state.view;
  if (v.name === "home") main.append(home());
  else if (v.name === "lesson") main.append(lesson(LESSONS.find((l) => l.id === v.id)));
  else if (v.name === "quick") main.append(quickCards());
  else if (v.name === "final") main.append(finalQuiz());
  else if (v.name === "share") main.append(share());
}

/* ---------- views ---------- */
function home() {
  const pct = Math.round((state.learned.size / LESSONS.length) * 100);
  const wrap = el("div");
  wrap.append(el("section", { class: "hero" }, [
    el("h1", {}, "Seven things that save lives."),
    el("p", { class: "lede" }, [
      "Most people who die suddenly — from cardiac arrest, choking, stroke, bleeding, or despair — die within reach of someone who could have helped, but didn't know how. ",
      el("strong", {}, "Ten minutes here, and you'll know how."),
      " Free. Works offline. No sign-up. Please pass it on.",
    ]),
    el("div", { class: "facts" }, [
      fact("2–3×", "the chance of surviving a cardiac arrest when a bystander starts CPR right away"),
      fact("< 40%", "of people in cardiac arrest get CPR from a bystander — mostly because nobody present knew how"),
      fact("5 min", "is how long it can take to bleed to death from a limb wound — an ambulance rarely arrives faster"),
      fact("1 in 3", "people will witness a medical emergency in their lifetime. The question is what you'll do."),
    ]),
  ]));
  wrap.append(el("div", { class: "progress" }, [
    el("span", {}, `${state.learned.size} of ${LESSONS.length} learned`),
    el("div", { class: "bar" }, [el("i", { style: `width:${pct}%` })]),
    el("span", {}, "~15 min total"),
  ]));
  const grid = el("div", { class: "grid" });
  LESSONS.forEach((l) => {
    const c = el("button", { class: `card${state.learned.has(l.id) ? " done" : ""}` }, [
      el("span", { class: "n" }, l.n),
      el("h3", {}, l.title),
      el("p", {}, l.short),
      el("span", { class: "time" }, `${l.minutes} min · interactive`),
    ]);
    c.onclick = () => go({ name: "lesson", id: l.id });
    grid.append(c);
  });
  const quick = el("button", { class: "card wide" }, [el("span", { class: "icon", "aria-hidden": "true" }, "＋"), el("div", {}, [el("h3", {}, "Eight more, in one minute each"), el("p", {}, "Seizure, allergic reaction, overdose, drowning, burns, low blood sugar, heatstroke, handwashing.")])]);
  quick.onclick = () => go({ name: "quick" });
  const fq = el("button", { class: "card wide quiz-card" }, [el("span", { class: "icon", "aria-hidden": "true" }, "?"), el("div", {}, [el("h3", {}, "Test yourself: 10 scenarios"), el("p", {}, state.bestScore == null ? "Would you know what to do? Find out in three minutes." : `Your best: ${state.bestScore} / ${FINAL_QUIZ.length}. Try to beat it.`)])]);
  fq.onclick = () => go({ name: "final" });
  const sh = el("button", { class: "card wide share-card" }, [el("span", { class: "icon", "aria-hidden": "true" }, "→"), el("div", {}, [el("h3", {}, "Pass it on"), el("p", {}, "A one-page cheat sheet to print, and a message to send to the people you'd want nearby.")])]);
  sh.onclick = () => go({ name: "share" });
  grid.append(quick, fq, sh);
  wrap.append(grid);
  wrap.append(el("section", { class: "section", style: "border-left:5px solid var(--blue)" }, [
    el("h2", {}, "Why this page"),
    el("p", {}, "If you could put one thing in front of every person on Earth, what would do the most good? Not a product, not an opinion — a few minutes of knowledge that turns a bystander into the person who acts. Cardiac arrest, choking, stroke, haemorrhage and suicide together take millions of lives a year, and in each case the outcome often depends on whoever happens to be standing closest. These skills are old, proven, and simple. They are just not evenly distributed. This page tries to fix that."),
    el("p", {}, "Learn them. Then send this to one person who'd want to know. That's the whole plan."),
  ]));
  return wrap;
}
function fact(n, t) { return el("div", { class: "fact" }, [el("b", {}, n), el("span", {}, t)]); }

function lesson(l) {
  const idx = LESSONS.indexOf(l);
  const wrap = el("div");
  const back = el("button", { class: "back" }, "← All skills");
  back.onclick = () => go({ name: "home" });
  wrap.append(el("div", { class: "lesson-head" }, [back, el("span", { class: "kicker" }, `${l.n} of ${LESSONS.length} · ${l.minutes} min`)]));
  wrap.append(el("h1", {}, l.title));
  wrap.append(el("p", { class: "summary" }, sub(l.why)));

  wrap.append(el("section", { class: "section recognize" }, [
    el("h2", {}, "Recognise it"),
    el("ul", { class: "signs" }, l.recognize.map(([b, s]) => el("li", {}, [el("b", {}, sub(b)), el("span", {}, sub(s))]))),
  ]));
  wrap.append(el("section", { class: "section do" }, [
    el("h2", {}, "What to do"),
    el("div", { class: "callout" }, `Emergency number: ${state.region.num}. Put the phone on speaker and do what the dispatcher says.`),
    el("ol", { class: "steps" }, l.steps.map(([b, s]) => el("li", {}, [el("div", {}, [el("b", {}, sub(b)), el("span", {}, sub(s))])]))),
  ]));
  wrap.append(el("section", { class: "section dont" }, [
    el("h2", {}, "Don't"),
    el("ul", { class: "dont-list" }, l.dont.map((d) => el("li", {}, sub(d)))),
  ]));

  const drillEl =
    l.drill === "metronome" ? D.metronome(ctx) :
    l.drill === "flow" ? D.flow(ctx, l.flow) :
    l.drill === "pressure" ? D.pressure(ctx) :
    l.drill === "signs" ? D.signs(ctx, l.signsDrill) :
    l.drill === "order" ? D.order(ctx, l.orderDrill) :
    l.drill === "respond" ? D.respond(ctx, l.respondDrill) : null;
  const drillTitle = { metronome: "Practise the rhythm", flow: "Walk through it", pressure: "Feel it", signs: "Would you call?", order: "Do it in order", respond: "What would you say?" }[l.drill];
  wrap.append(el("section", { class: "section drill" }, [el("h2", {}, drillTitle), drillEl]));

  wrap.append(el("section", { class: "section check" }, [
    el("h2", {}, "Quick check"),
    D.quiz(ctx, l.check),
  ]));

  const learned = el("button", { class: `btn big ${state.learned.has(l.id) ? "green" : ""}` }, state.learned.has(l.id) ? "✓ Learned" : "I've got this — mark as learned");
  learned.onclick = () => { state.learned.add(l.id); learned.textContent = "✓ Learned"; learned.classList.add("green"); ctx.toast(state.learned.size === LESSONS.length ? "All seven. Now pass it on." : `${state.learned.size} of ${LESSONS.length} learned`); };
  const nav = el("div", { class: "nav-bottom" }, [learned]);
  const next = LESSONS[idx + 1];
  const nextBtn = el("button", { class: "btn secondary" }, next ? `Next: ${next.title} →` : "Test yourself →");
  nextBtn.onclick = () => go(next ? { name: "lesson", id: next.id } : { name: "final" });
  nav.append(nextBtn);
  wrap.append(nav);
  return wrap;
}

function quickCards() {
  const wrap = el("div");
  const back = el("button", { class: "back" }, "← All skills");
  back.onclick = () => go({ name: "home" });
  wrap.append(el("div", { class: "lesson-head" }, [back]));
  wrap.append(el("h1", {}, "Eight more worth knowing"));
  wrap.append(el("p", { class: "summary" }, "Less common, but you'll recognise them when they happen. Read each once."));
  wrap.append(el("div", { class: "mini-grid" }, QUICK.map((q) => el("div", { class: "mini" }, [el("h3", {}, q.t), el("ul", {}, q.pts.map((p, i) => el("li", {}, i === 0 ? el("b", {}, sub(p)) : sub(p))))]))));
  const nav = el("div", { class: "nav-bottom" });
  const b = el("button", { class: "btn" }, "Test yourself →"); b.onclick = () => go({ name: "final" });
  nav.append(back.cloneNode(true), b); nav.firstChild.onclick = () => go({ name: "home" });
  wrap.append(nav);
  return wrap;
}

function finalQuiz() {
  const wrap = el("div");
  const back = el("button", { class: "back" }, "← All skills");
  back.onclick = () => go({ name: "home" });
  wrap.append(el("div", { class: "lesson-head" }, [back]));
  wrap.append(el("h1", {}, "Would you know what to do?"));
  wrap.append(el("p", { class: "summary" }, "Ten situations. No tricks, just the things that actually come up."));
  wrap.append(el("section", { class: "section drill" }, [D.quiz(ctx, FINAL_QUIZ, {
    onDone(score) {
      if (state.bestScore == null || score > state.bestScore) state.bestScore = score;
      const b = el("button", { class: "btn", style: "margin-left:8px" }, "Pass it on →");
      b.onclick = () => go({ name: "share" });
      wrap.querySelector(".score")?.after(b);
    },
  })]));
  return wrap;
}

function share() {
  const wrap = el("div");
  const back = el("button", { class: "back" }, "← All skills");
  back.onclick = () => go({ name: "home" });
  wrap.append(el("div", { class: "lesson-head" }, [back]));
  wrap.append(el("h1", {}, "Pass it on"));
  wrap.append(el("p", { class: "summary" }, "Knowledge like this only works if it's where the emergency is. Put the sheet on a fridge. Send the message to three people. Then, when you can, take a real course — one afternoon, and you'll never forget it."));

  const sheet = el("div", { class: "sheet" }, [
    el("h2", {}, `Emergency: ${state.region.num} — put it on speaker`),
    item("Not breathing / only gasping", `Call ${state.region.num}. Push hard and fast on the centre of the chest, 100–120/min, 5 cm deep. Don't stop. AED as soon as it arrives.`),
    item("Choking, silent", "5 back blows between the shoulder blades, 5 abdominal thrusts above the navel. Repeat. If they go limp: CPR."),
    item("Stroke — FAST", `Face droops? Arms drift? Speech slurred? Time: call ${state.region.num}. Note when it started. No food, drink or aspirin.`),
    item("Severe bleeding", "Press hard directly on the wound. Don't let go, don't peek. Add cloth on top. Limb won't stop? Tourniquet above it, note the time."),
    item("Heart attack", `Chest pressure, sweat, breathless, nausea, dread. Call ${state.region.num}. Sit them down. Chew one aspirin if not allergic and the dispatcher agrees.`),
    item("Unconscious but breathing", "Recovery position: arm out, hand to cheek, knee up, roll towards you, tilt head back. Check breathing every minute."),
    item("Someone talks about ending it", `Ask directly: “Are you thinking about suicide?” Listen. Remove the means. Call a crisis line together${state.region.crisis ? ` — ${state.region.crisis}` : ""}. Follow up tomorrow.`),
    el("p", { style: "margin:12px 0 0;color:var(--muted);font-size:.85rem" }, "Not a substitute for training. Follow your dispatcher. ifeveryoneknew — share freely."),
  ]);
  wrap.append(sheet);
  const printBtn = el("button", { class: "btn" }, "Print this sheet");
  printBtn.onclick = () => { try { window.print(); } catch (e) { ctx.toast("Printing isn't available here — use your browser's print menu."); } };

  const msg = `I just spent 10 minutes learning the 7 things that save lives when someone collapses, chokes, has a stroke, bleeds badly, or talks about giving up. It's free and takes 10 minutes. I'd want you to know this if it were me on the floor:\n\n• Not breathing: call ${state.region.num}, push hard and fast on the centre of the chest (100–120/min), don't stop.\n• Choking and silent: 5 back blows, 5 abdominal thrusts, repeat.\n• Stroke: Face droop, Arm drift, Speech slurred → call ${state.region.num}, note the time.\n• Bleeding: press hard, don't let go.\n• Someone hopeless: ask directly about suicide, stay, call a crisis line together.\n\nPlease learn it and pass it on.`;
  const ta = el("textarea", { class: "share", readonly: "true", "aria-label": "Message to share" }, msg);
  const copyBtn = el("button", { class: "btn green" }, "Copy message");
  copyBtn.onclick = async () => {
    try { await navigator.clipboard.writeText(msg); ctx.toast("Copied. Send it to three people."); }
    catch (e) { ta.focus(); ta.select(); try { document.execCommand("copy"); ctx.toast("Copied. Send it to three people."); } catch (e2) { ctx.toast("Select the text and copy it manually."); } }
  };
  wrap.append(el("section", { class: "section", style: "border-left:5px solid var(--green)" }, [
    el("h2", {}, "A message to send"),
    ta,
    el("div", { class: "row", style: "margin-top:10px" }, [copyBtn, printBtn]),
  ]));
  wrap.append(el("section", { class: "section", style: "border-left:5px solid var(--blue)" }, [
    el("h2", {}, "Three more things that are worth your afternoon"),
    el("ul", { class: "dont-list" }, [
      el("li", {}, "Take a certified first-aid / CPR course (Red Cross, St John, your national resuscitation council, many employers and community centres run them free). Hands on a manikin is what makes it stick."),
      el("li", {}, "Find out where the nearest AED is at work, at the gym, and on your street. Some countries have apps that alert trained bystanders to nearby cardiac arrests — sign up."),
      el("li", {}, "Register as an organ donor, and tell your family. One donor can save up to eight lives."),
    ]),
  ]));
  return wrap;
}
function item(b, s) { return el("div", { class: "item" }, [el("b", {}, b), el("span", {}, s)]); }

updatePill();
render();
