// Bystander — ten minutes of practice for the minutes before help arrives.
import { h, s, scope, mmss, clamp, scrollToEl } from "./ui.js";
import { state, subscribe, setCountry, markDone, secondsHere, num, emit } from "./state.js";
import { COUNTRIES, UNKNOWN, byCode } from "./numbers.js";
import { runDrill, fill } from "./drill.js";
import { runEmergency } from "./emergency.js";
import { wake, sfx } from "./audio.js";
import cpr from "./drills/cpr.js";
import choking from "./drills/choking.js";
import bleeding from "./drills/bleeding.js";
import stroke from "./drills/stroke.js";
import recovery from "./drills/recovery.js";
import myths from "./drills/myths.js";

const DRILLS = [cpr, choking, bleeding, stroke, recovery, myths];
const app = document.getElementById("app");
const headerSlot = document.getElementById("header");
let current = null; // { destroy }
let viewName = "home";

// ── Small glyphs for the drill cards ─────────────────────────────────────────────────────

const GLYPHS = {
  cpr: () => [s("path", { d: "M32 54 C8 38 8 16 22 14 c6 -1 9 3 10 7 c1 -4 4 -8 10 -7 C56 16 56 38 32 54 Z" }), s("path", { class: "glyph-cut", d: "M12 32 h12 l4 -8 l6 16 l4 -8 h14" })],
  choking: () => [s("circle", { cx: 32, cy: 16, r: 10 }), s("path", { class: "glyph-stroke", d: "M14 58 V44 Q14 34 26 33 M50 58 V44 Q50 34 38 33" }), s("path", { class: "glyph-stroke", d: "M18 46 L30 31 M46 46 L34 31" })],
  bleeding: () => [s("path", { d: "M32 6 C22 22 14 30 14 40 a18 18 0 0 0 36 0 C50 30 42 22 32 6 Z" })],
  stroke: () => [s("circle", { cx: 32, cy: 32, r: 24 }), s("circle", { class: "glyph-cut-fill", cx: 23, cy: 27, r: 3 }), s("ellipse", { class: "glyph-cut-fill", cx: 41, cy: 29, rx: 3, ry: 1.6 }), s("path", { class: "glyph-cut", d: "M21 39 Q30 46 43 44" })],
  recovery: () => [s("circle", { cx: 12, cy: 38, r: 8 }), s("path", { class: "glyph-stroke", d: "M24 40 H58 M34 40 L42 24 L52 26" })],
  myths: () => [s("path", { class: "glyph-stroke", d: "M10 14 L28 32 M28 14 L10 32" }), s("path", { class: "glyph-stroke", d: "M34 44 L42 52 L56 32" })],
};

const glyph = (id) => s("svg", { class: "glyph", viewBox: "0 0 64 64", "aria-hidden": "true" }, GLYPHS[id]());

// ── Header ──────────────────────────────────────────────────────────────────────────────

function renderHeader() {
  const done = state.done.size;
  headerSlot.replaceChildren(
    h(
      "div",
      { class: "bar" },
      h(
        "button",
        { class: "wordmark", type: "button", onclick: () => go("home"), "aria-label": "Bystander — home" },
        h("span", { class: "wordmark-by" }, "By"),
        h("span", {}, "stander")
      ),
      h(
        "button",
        {
          class: "bar-progress",
          type: "button",
          onclick: () => go(done === DRILLS.length ? "card" : "home", "drills"),
          "aria-label": `${done} of ${DRILLS.length} drills done`,
        },
        h("span", { class: "bar-pips", "aria-hidden": "true" }, DRILLS.map((d) => h("i", { class: state.done.has(d.id) ? "is-done" : "" }))),
        h("span", { class: "bar-count" }, `${done}/${DRILLS.length}`)
      ),
      h(
        "button",
        {
          class: "bar-sound",
          type: "button",
          "aria-pressed": String(state.sound),
          onclick: () => {
            state.sound = !state.sound;
            if (state.sound) {
              wake();
              sfx.tap();
            }
            emit();
          },
        },
        state.sound ? "Sound on" : "Sound off"
      ),
      h(
        "button",
        { class: "btn btn-red bar-em", type: "button", onclick: () => go("emergency") },
        h("span", { class: "em-dot" }),
        h("span", { class: "bar-em-long" }, "Emergency now"),
        h("span", { class: "bar-em-short" }, "Emergency")
      )
    )
  );
}

// ── Home ────────────────────────────────────────────────────────────────────────────────

function survivalClock(sc) {
  const time = h("b", { class: "clock-time" }, "0:00");
  const pct = h("b", { class: "clock-pct" }, "0%");
  const line = h("p", { class: "clock-line" });
  const cells = Array.from({ length: 10 }, (_, i) => {
    const fillEl = h("i", {});
    return { el: h("div", { class: "clock-cell" + (i === 7 ? " is-amb" : "") }, fillEl, h("span", {}, String(i + 1))), fillEl };
  });
  const el = h(
    "aside",
    { class: "clock", "aria-label": "Survival clock" },
    h("p", { class: "clock-top" }, h("span", { class: "live-dot" }), "You opened this page", time, "ago"),
    line,
    h("div", { class: "clock-bar", "aria-hidden": "true" }, cells.map((c) => c.el)),
    h(
      "div",
      { class: "clock-marks", "aria-hidden": "true" },
      h("span", { class: "m0" }, "Heart stops"),
      h("span", { class: "m5" }, "Brain injury begins"),
      h("span", { class: "m8" }, "Ambulance, on a good day")
    ),
    h("p", { class: "clock-note" }, "Each block is one minute without CPR: roughly 10% of the chance of survival, gone.")
  );
  const tick = () => {
    const sec = secondsHere();
    time.textContent = mmss(sec);
    const lost = clamp(Math.round((sec / 60) * 10), 0, 100);
    pct.textContent = lost + "%";
    if (lost < 96) {
      line.replaceChildren("If a heart had stopped at that moment and nobody had started CPR, about ", pct, " of that person’s chance of surviving would already be gone.");
    } else {
      line.replaceChildren("If a heart had stopped at that moment and nobody had started CPR, there would be almost no chance left. The ambulance would just be pulling up.");
    }
    cells.forEach((c, i) => {
      const left = clamp(1 - (sec / 60 - i), 0, 1);
      c.fillEl.style.transform = `scaleX(${left})`;
      c.el.classList.toggle("is-empty", left === 0);
      c.el.classList.toggle("is-now", left > 0 && left < 1);
    });
  };
  tick();
  sc.interval(tick, 250);
  return el;
}

function numberBox() {
  const select = h(
    "select",
    { class: "num-select", "aria-label": "Your country", onchange: (e) => setCountry(e.target.value ? byCode(e.target.value) : UNKNOWN) },
    COUNTRIES.map((c) => h("option", { value: c.code, selected: c.code === state.country.code }, c.name)),
    h("option", { value: "", selected: state.country.code === "" }, "Somewhere else")
  );
  const c = state.country;
  return h(
    "section",
    { class: "numbox", id: "number" },
    h(
      "div",
      { class: "numbox-left" },
      h("p", { class: "label" }, "The first thing to know"),
      h("h2", { class: "h-section" }, "Your emergency number."),
      h(
        "p",
        { class: "numbox-text" },
        c.code
          ? state.guessed
            ? `Going by your device’s time zone: ${c.name}. If that’s wrong, change it — every instruction on this page will use your number.`
            : `Set to ${c.name}. Every instruction on this page now uses this number.`
          : "We couldn’t tell where you are. Pick your country, or use 112: most mobile phones redirect it to the local emergency service."
      ),
      h("label", { class: "num-pick" }, h("span", { class: "label" }, "Country"), select)
    ),
    h(
      "div",
      { class: "numbox-right" },
      h("div", { class: "num-big" }, c.n),
      h("p", { class: "num-alt" }, c.alt ? (c.code ? `Also works: ${c.alt}` : c.alt) : "Ambulance · medical emergency"),
      h("p", { class: "num-fine" }, "Numbers change. Check yours once, today, while nothing is wrong.")
    )
  );
}

function home(arg) {
  const sc = scope();
  const first = DRILLS.find((d) => !state.done.has(d.id));
  const startLabel = state.done.size === 0 ? "Start the ten minutes" : first ? `Continue: ${first.num} ${first.name}` : "See your card";

  const hero = h(
    "section",
    { class: "hero" },
    h(
      "p",
      { class: "defn" },
      h("b", {}, "by·stand·er"),
      h("i", {}, "noun"),
      h("s", {}, "a person who is present but does not take part."),
      h("span", { class: "defn-new" }, "the first person who can help.")
    ),
    h(
      "h1",
      { class: "hero-title" },
      h("span", {}, "The ambulance is "),
      h("span", { class: "red" }, "8 minutes"),
      h("span", {}, " away. "),
      h("span", { class: "hero-line2" }, "You’re already there.")
    ),
    h(
      "div",
      { class: "hero-row" },
      h(
        "div",
        { class: "hero-copy" },
        h(
          "p",
          { class: "lede" },
          "When a heart stops, a throat blocks or an artery opens, what happens next is decided before the professionals arrive — by whoever happens to be standing nearest. Six short drills. No sign-up. You practise with your own hands."
        ),
        h(
          "div",
          { class: "hero-cta" },
          h("button", { class: "btn btn-primary btn-big", type: "button", onclick: () => (first ? go("drill", first.id) : go("card")) }, startLabel, h("span", { class: "arrow", "aria-hidden": "true" }, "→")),
          h("button", { class: "btn btn-red btn-big", type: "button", onclick: () => go("emergency") }, h("span", { class: "em-dot" }), "It’s happening now")
        )
      ),
      survivalClock(sc)
    )
  );

  const drills = h(
    "section",
    { class: "drills", id: "drills" },
    h(
      "div",
      { class: "section-head" },
      h("p", { class: "label" }, "The training"),
      h("h2", { class: "h-section" }, "Six drills. About ten minutes."),
      h("p", { class: "section-sub" }, "Do them in order or pick the one that frightens you most. Each ends with four words to remember.")
    ),
    h(
      "ol",
      { class: "cards" },
      DRILLS.map((d) =>
        h(
          "li",
          {},
          h(
            "button",
            { class: "card" + (state.done.has(d.id) ? " is-done" : ""), type: "button", onclick: () => go("drill", d.id) },
            h("span", { class: "card-num" }, d.num),
            glyph(d.id),
            h("span", { class: "card-name" }, d.name),
            h("span", { class: "card-blurb" }, d.blurb),
            h("span", { class: "card-meta" }, state.done.has(d.id) ? "Done · do it again" : `${d.minutes} min`, h("span", { class: "arrow", "aria-hidden": "true" }, "→"))
          )
        )
      )
    )
  );

  const facts = h(
    "section",
    { class: "facts" },
    [
      ["7 in 10", "cardiac arrests outside hospital happen at home. The life you save will most likely be someone you love."],
      ["2–3×", "the odds of survival when a bystander starts CPR straight away, compared with waiting for the ambulance."],
      ["5 min", "is all it can take to bleed to death from a major wound, or to suffer brain damage without oxygen."],
    ].map(([n, t]) => h("div", { class: "fact" }, h("b", {}, n), h("p", {}, t)))
  );

  const foot = h(
    "footer",
    { class: "foot" },
    h(
      "p",
      {},
      "Bystander follows the public first-aid guidance of the international resuscitation councils (ILCOR, the American Heart Association, the European Resuscitation Council) and the Red Cross and Red Crescent movement. It is a first lesson, not a certificate: a hands-on class with a manikin will teach your arms what a screen can’t."
    ),
    h("p", {}, "Works offline. Stores nothing. Tracks nothing. Share it freely.")
  );

  const el = h("main", { class: "home" }, hero, drills, numberBox(), facts, foot);
  sc.add(
    subscribe(() => {
      // Country changed: rebuild just the number box.
      const old = el.querySelector(".numbox");
      if (old) old.replaceWith(numberBox());
    })
  );
  if (arg === "drills") requestAnimationFrame(() => scrollToEl(drills));
  return { el, destroy: () => sc.end() };
}

// ── Drill routing ───────────────────────────────────────────────────────────────────────

function nextAfter(id) {
  const i = DRILLS.findIndex((d) => d.id === id);
  const order = [...DRILLS.slice(i + 1), ...DRILLS.slice(0, i)];
  return order.find((d) => !state.done.has(d.id) && d.id !== id) || null;
}

function drill(id) {
  const def = DRILLS.find((d) => d.id === id) || DRILLS[0];
  const opts = {
    onExit: (to) => {
      if (to === "next") {
        const n = nextAfter(def.id);
        n ? go("drill", n.id) : go("card");
      } else go("home", "drills");
    },
    onFinish: () => markDone(def.id),
    nextLabel: () => {
      const n = nextAfter(def.id);
      return n ? `Next: ${n.num} ${n.name} →` : "See your card →";
    },
  };
  const view = def.custom ? def.custom(opts) : runDrill(def, opts);
  const el = h("main", { class: "drill-wrap" }, view.el);
  return { el, destroy: view.destroy };
}

// ── The closing card ────────────────────────────────────────────────────────────────────

function sandboxed() {
  try {
    void window.localStorage;
    return window.self !== window.top;
  } catch (e) {
    return true;
  }
}

function card() {
  const sc = scope();
  const sec = secondsHere();
  const all = state.done.size === DRILLS.length;
  const mythKeep = [
    { word: "Burn", line: "Cool running water, 20 minutes. No ice, no butter." },
    { word: "Drowning", line: "It’s silent. Reach or throw — don’t go in." },
    { word: "Heart attack", line: "Call {n}. Sit still. Chew an aspirin if not allergic." },
    { word: "Heatstroke", line: "Hot and confused: cool them fast, any way you can." },
  ];
  const panels = DRILLS.map((d) => ({ d, keep: d.keep || mythKeep }));

  const todo = [
    ["Find your nearest defibrillator.", "At home and at work. Look for a green sign with a white heart. Knowing where it is saves the minutes that matter."],
    ["Show this to one person.", "These skills spread hand to hand. The person you teach may be the one standing next to you when it’s your turn."],
    ["Book a hands-on class.", "A screen can teach you when and how. Only a manikin teaches your arms how hard. Your local Red Cross or Red Crescent runs them."],
  ];

  const el = h(
    "main",
    { class: "cardview" },
    h(
      "section",
      { class: "card-hero" },
      h("p", { class: "label" }, all ? "Six of six" : `${state.done.size} of six drills done`),
      h(
        "h1",
        { class: "hero-title hero-title--card", tabindex: "-1" },
        h("span", {}, "You’ve been here "),
        h("span", { class: "red" }, mmss(sec)),
        h("span", {}, ".")
      ),
      h(
        "p",
        { class: "lede" },
        sec >= 360
          ? "That’s about how long an ambulance takes to arrive. An hour ago those minutes would have been spent waiting. Now you know what to do with them."
          : "An ambulance takes longer than that to arrive. You now know what to do with the minutes in between."
      ),
      state.results.cpr
        ? h("p", { class: "card-result" }, "Your CPR tempo: ", h("b", {}, `${state.results.cpr.avg} a minute`), ". The target is 100 to 120.")
        : null,
      !all ? h("button", { class: "btn btn-primary", type: "button", onclick: () => go("home", "drills") }, "Finish the other drills →") : null
    ),
    h(
      "section",
      { class: "pocket", "aria-label": "Pocket card" },
      h(
        "div",
        { class: "pocket-head" },
        h("span", { class: "wordmark wordmark--static" }, h("span", { class: "wordmark-by" }, "By"), h("span", {}, "stander")),
        h("span", { class: "pocket-call" }, "Call ", h("b", {}, num()))
      ),
      h(
        "div",
        { class: "pocket-grid" },
        panels.map(({ d, keep }) =>
          h(
            "article",
            { class: "pocket-panel" + (state.done.has(d.id) ? "" : " is-todo") },
            h("h3", {}, h("span", {}, d.num), d.name),
            h("ul", {}, keep.map((k) => h("li", {}, h("b", {}, k.word), h("span", { html: fill(k.line) }))))
          )
        )
      )
    ),
    h(
      "section",
      { class: "todo" },
      h("div", { class: "section-head" }, h("p", { class: "label" }, "Before you close this tab"), h("h2", { class: "h-section" }, "Three things that make it real.")),
      h(
        "ol",
        { class: "todo-list" },
        todo.map(([t, d]) => {
          const box = h("input", { type: "checkbox" });
          return h("li", {}, h("label", {}, box, h("span", { class: "todo-box", "aria-hidden": "true" }), h("span", { class: "todo-text" }, h("b", {}, t), h("span", {}, d))));
        })
      ),
      h(
        "div",
        { class: "todo-actions" },
        sandboxed() ? null : h("button", { class: "btn btn-primary", type: "button", onclick: () => window.print() }, "Print the card"),
        h("button", { class: "btn btn-ghost", type: "button", onclick: () => go("home", "drills") }, "Back to the drills")
      )
    )
  );
  return { el, destroy: () => sc.end() };
}

// ── Router ──────────────────────────────────────────────────────────────────────────────

function go(name, arg) {
  wake();
  current?.destroy?.();
  viewName = name;
  let view;
  if (name === "drill") view = drill(arg);
  else if (name === "card") view = card();
  else if (name === "emergency") {
    const em = runEmergency({ onExit: () => go("home") });
    view = { el: em.el, destroy: em.destroy };
  } else view = home(arg);
  current = view;
  document.body.dataset.view = name;
  app.replaceChildren(view.el);
  if (!(name === "home" && arg === "drills")) window.scrollTo({ top: 0, behavior: "instant" });
  const focusTarget = view.el.querySelector("h1[tabindex], h2[tabindex]");
  if (focusTarget && name !== "home") focusTarget.focus({ preventScroll: true });
}

subscribe(() => renderHeader());
renderHeader();
go("home");
