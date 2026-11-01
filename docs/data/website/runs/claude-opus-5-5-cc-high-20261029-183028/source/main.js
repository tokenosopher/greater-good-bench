import { h } from "./dom.js";
import { lessons, habits } from "./lessons.js";

const learned = new Set(); // kept in memory only, nothing is stored or sent
const app = document.getElementById("app");

/* ---------- Hero ---------- */

const hero = h("header", { class: "hero" },
  h("div", { class: "hero-inner" },
    h("p", { class: "eyebrow" }, "Free · No sign-up · Works offline · Nothing you do here is stored or sent"),
    h("h1", null, "The Ten-Minute ", h("em", null, "Lifesaver")),
    h("p", { class: "lede" },
      "In an emergency, the person most likely to save a life is whoever is already there. ",
      "Usually that's someone ordinary: a parent, a coworker, a stranger. It could be you."),
    h("p", { class: "lede soft" },
      "Here are ten skills that take about a minute each to learn. Together they cover many of the most common ways people die suddenly and needlessly. Each one has a short practice so it sticks."),
    h("div", { class: "hero-actions" },
      h("a", { class: "btn big", href: "#lesson-call" }, "Start learning →"),
      h("button", { class: "btn big ghost", type: "button", onClick: () => openEmergency() }, "🚨 Emergency right now?")),
    h("ol", { class: "hero-index" },
      lessons.map((l, i) => h("li", null, h("a", { href: "#lesson-" + l.id }, h("span", { class: "ix" }, String(i + 1).padStart(2, "0")), l.title))))));

/* ---------- Progress bar ---------- */

const countEl = h("span", { class: "count" }, "0");
const dots = lessons.map((l, i) =>
  h("a", { class: "dot", href: "#lesson-" + l.id, title: l.title, "aria-label": `${i + 1}. ${l.title}` }, l.icon));
const topbar = h("nav", { class: "topbar", "aria-label": "Lessons" },
  h("span", { class: "brand" }, "Ten-Minute Lifesaver"),
  h("span", { class: "dots" }, dots),
  h("span", { class: "tally" }, countEl, " / ", lessons.length, " learned"),
  h("button", { class: "sos", type: "button", onClick: () => openEmergency() }, "🚨 Emergency"));

/* ---------- Lessons ---------- */

const sections = lessons.map((l, i) => {
  const badge = h("span", { class: "badge" }, "Practice");
  const section = h("section", { class: "lesson", id: "lesson-" + l.id },
    h("div", { class: "lesson-head" },
      h("span", { class: "lesson-num" }, String(i + 1).padStart(2, "0")),
      h("div", null,
        h("h2", null, h("span", { class: "icon", "aria-hidden": "true" }, l.icon), " ", l.title),
        h("p", { class: "stat" }, l.stat))),
    h("div", { class: "lesson-body" },
      h("div", { class: "learn" },
        h("h3", null, "What to do"),
        l.fast && h("div", { class: "fast" }, l.fast.map(([L, word, text]) =>
          h("div", { class: "fast-card" }, h("span", { class: "fast-l" }, L), h("strong", null, word), h("p", null, text)))),
        h("ol", { class: "steps" }, l.steps.map((st) => h("li", { html: st }))),
        l.note && h("p", { class: "note" }, l.note)),
      h("div", { class: "practice" },
        h("h3", null, "Try it ", badge),
        l.practice(() => complete(l.id, section, badge)))),
    h("div", { class: "lesson-foot" },
      i < lessons.length - 1
        ? h("a", { class: "next-link", href: "#lesson-" + lessons[i + 1].id }, `Next: ${lessons[i + 1].title} →`)
        : h("a", { class: "next-link", href: "#finish" }, "Finish: pass it on →")));
  return section;
});

function complete(id, section, badge) {
  if (learned.has(id)) return;
  learned.add(id);
  section.classList.add("learned");
  badge.textContent = "✓ Learned";
  const idx = lessons.findIndex((l) => l.id === id);
  dots[idx].classList.add("on");
  countEl.textContent = learned.size;
  updateFinish();
}

/* ---------- Everyday habits ---------- */

const habitsSection = h("section", { class: "habits" },
  h("h2", null, "Six habits that quietly save the most lives"),
  h("p", { class: "sub" }, "Emergencies are rarer when we do the boring things."),
  h("div", { class: "habit-grid" }, habits.map(([icon, title, text]) =>
    h("div", { class: "habit" }, h("span", { class: "habit-icon", "aria-hidden": "true" }, icon), h("strong", null, title), h("p", null, text)))));

/* ---------- Finish: card + pass it on ---------- */

const finishTitle = h("h2", null);
const finishSub = h("p", { class: "sub" });
function updateFinish() {
  const n = learned.size;
  if (n === lessons.length) {
    finishTitle.textContent = "You can now save a life.";
    finishSub.textContent = "All ten skills practiced. Most people never learn them. Now help someone else learn them too.";
    document.body.classList.add("all-done");
  } else {
    finishTitle.textContent = "Pass it on.";
    finishSub.textContent = n
      ? `You've practiced ${n} of ${lessons.length}. The ones you haven't tried are marked above, each takes about a minute.`
      : "Keep this card in your head, and send this page to the people you love.";
  }
}
updateFinish();

const card = h("div", { class: "card", id: "card" },
  h("div", { class: "card-head" }, h("strong", null, "Ten-Minute Lifesaver"), h("span", null, "Remember")),
  h("ol", null, lessons.map((l) => h("li", null, h("span", { "aria-hidden": "true" }, l.icon), " ", l.remember))));

// The multiplier: one person teaching a few others, who each do the same.
const perEl = h("output", null, "3");
const roundsEl = h("output", null, "5");
const reachEl = h("div", { class: "reach-n" });
const reachNote = h("p", { class: "reach-note" });
const per = h("input", { type: "range", min: 1, max: 5, value: 3, "aria-label": "People each person teaches" });
const rounds = h("input", { type: "range", min: 1, max: 20, value: 5, "aria-label": "Rounds of sharing" });
const WORLD = 8.1e9;
function updateReach() {
  const p = +per.value, r = +rounds.value;
  perEl.textContent = p; roundsEl.textContent = r;
  let total = 0, wave = 1;
  for (let i = 0; i < r; i++) { wave *= p; total += wave; }
  total = Math.min(total, WORLD);
  reachEl.textContent = total >= WORLD ? "Everyone on Earth" : fmt(total) + (total === 1 ? " person" : " people");
  reachNote.textContent = total >= WORLD
    ? "8 billion people, every one of them ready to help."
    : total >= 1e6 ? "That's a whole city, every person ready to help."
    : total >= 1000 ? "Enough to fill a stadium with people who know what to do."
    : "Each of them could one day be the person who's there.";
}
const fmt = (n) => n >= 1e9 ? (n / 1e9).toFixed(1) + " billion" : n >= 1e6 ? (n / 1e6).toFixed(1) + " million" : Math.round(n).toLocaleString("en");
per.addEventListener("input", updateReach);
rounds.addEventListener("input", updateReach);
updateReach();

const shareText = `I just learned 10 life-saving skills in about 10 minutes. Here's the short version:\n\n${lessons.map((l, i) => `${i + 1}. ${l.title}: ${l.remember}`).join("\n")}\n\nPlease learn them too, then pass it on.`;
const shareBox = h("textarea", { class: "share-text", readonly: true, rows: 6, "aria-label": "Message to share" }, shareText);
const copyBtn = h("button", { class: "btn", type: "button" }, "Copy message");
copyBtn.addEventListener("click", async () => {
  let ok = false;
  try { await navigator.clipboard.writeText(shareText); ok = true; } catch {}
  if (!ok) {
    try { shareBox.focus(); shareBox.select(); ok = document.execCommand("copy"); } catch {}
  }
  copyBtn.textContent = ok ? "✓ Copied" : "Selected, press Ctrl/⌘+C";
  if (!ok) { shareBox.focus(); shareBox.select(); }
  setTimeout(() => (copyBtn.textContent = "Copy message"), 2500);
});

const finish = h("section", { class: "finish", id: "finish" },
  finishTitle, finishSub,
  h("div", { class: "finish-grid" },
    h("div", null, card,
      h("button", { class: "btn ghost small", type: "button", onClick: () => { try { window.print(); } catch {} } }, "🖨 Print this card")),
    h("div", { class: "reach" },
      h("h3", null, "What if everyone shared it?"),
      h("label", null, "You teach ", perEl, " people, they each teach that many, and so on"),
      per,
      h("label", null, "for ", roundsEl, " rounds"),
      rounds,
      reachEl, reachNote,
      h("h3", { class: "mt" }, "Send it to someone"),
      shareBox, copyBtn)));

const footer = h("footer", { class: "footer" },
  h("p", null, h("strong", null, "This page is not a substitute for hands-on training. "),
    "It follows widely used guidance from the WHO, Red Cross / Red Crescent, the American Heart Association and the European Resuscitation Council, but local advice can differ. ",
    "Always call your emergency number and follow the dispatcher's instructions. If you can, take an in-person first-aid course. It's one of the best afternoons you'll ever spend."),
  h("p", { class: "fine" }, "Figures are rounded global estimates (WHO and others) and are given to show scale."));

/* ---------- Emergency overlay ---------- */

const EMERG = [
  ["cpr", "Collapsed, not breathing normally"],
  ["choke", "Choking"],
  ["bleed", "Bleeding heavily"],
  ["stroke", "Face drooping, weak arm, slurred speech"],
  ["heart", "Chest pain or pressure"],
  ["burn", "Burn"],
  ["drown", "In the water / pulled from water"],
  ["ask", "Someone talking about suicide"],
  ["ors", "Child with diarrhea"],
];
const overlayBody = h("div", { class: "ov-body" });
const overlay = h("div", { class: "overlay", role: "dialog", "aria-modal": "true", "aria-label": "Emergency quick guide", hidden: true },
  h("div", { class: "ov-panel" },
    h("div", { class: "ov-top" },
      h("strong", null, "🚨 Emergency quick guide"),
      h("button", { class: "ov-close", type: "button", "aria-label": "Close", onClick: closeEmergency }, "✕")),
    overlayBody));

function emergencyMenu() {
  overlayBody.replaceChildren(
    h("div", { class: "ov-call" }, "1. Call your emergency number", h("small", null, "112 · 911 · 999 · 000 … Put it on speaker.")),
    h("p", { class: "ov-q" }, "2. What's happening?"),
    h("div", { class: "ov-grid" }, EMERG.map(([id, label]) => {
      const l = lessons.find((x) => x.id === id);
      return h("button", { class: "ov-btn", type: "button", onClick: () => emergencyDetail(l) }, h("span", { "aria-hidden": "true" }, l.icon), label);
    })));
}

function emergencyDetail(l) {
  overlayBody.replaceChildren(...[
    h("button", { class: "ov-back", type: "button", onClick: emergencyMenu }, "← Back"),
    h("h2", null, l.icon, " ", l.title),
    l.id !== "ors" && l.id !== "ask" && h("div", { class: "ov-call slim" }, "Call your emergency number (speaker on)"),
    l.id === "cpr" && h("div", { class: "ov-metro" }, h("div", { class: "pulse" }, "PUSH"), h("p", null, "Push down each time the circle pulses: 110 a minute.")),
    l.fast && h("div", { class: "fast" }, l.fast.map(([L, word, text]) =>
      h("div", { class: "fast-card" }, h("span", { class: "fast-l" }, L), h("strong", null, word), h("p", null, text)))),
    h("ol", { class: "steps big" }, l.steps.map((st) => h("li", { html: st }))),
    l.note && h("p", { class: "note" }, l.note)].filter(Boolean));
  overlayBody.scrollTop = 0;
}

let lastFocus = null;
function openEmergency() {
  lastFocus = document.activeElement;
  emergencyMenu();
  overlay.hidden = false;
  document.body.classList.add("noscroll");
  overlay.querySelector(".ov-close").focus();
}
function closeEmergency() {
  overlay.hidden = true;
  document.body.classList.remove("noscroll");
  if (lastFocus) lastFocus.focus();
}
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !overlay.hidden) closeEmergency(); });
overlay.addEventListener("click", (e) => { if (e.target === overlay) closeEmergency(); });

/* ---------- Mount ---------- */

app.append(hero, topbar, h("main", null, sections, habitsSection, finish), footer, overlay);

// Show the progress bar once the hero scrolls away; highlight the lesson in view.
const heroObs = new IntersectionObserver(([e]) => topbar.classList.toggle("show", !e.isIntersecting), { threshold: 0.05 });
heroObs.observe(hero);
const secObs = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    const idx = sections.indexOf(e.target);
    dots.forEach((d, i) => d.classList.toggle("here", i === idx));
  }
}, { rootMargin: "-45% 0px -50% 0px" });
sections.forEach((sct) => secObs.observe(sct));

// In-page links scroll smoothly without touching the URL (works inside sandboxed iframes).
document.addEventListener("click", (e) => {
  const a = e.target.closest('a[href^="#"]');
  if (!a) return;
  const target = document.getElementById(a.getAttribute("href").slice(1));
  if (!target) return;
  e.preventDefault();
  target.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
});
