import { h, s, shake } from "./dom.js";

/* ---------- 1. Emergency number lookup ---------- */

export const NUMBERS = [
  ["Pick where you live…", ""],
  ["Australia", "000", "112 also works from mobiles"],
  ["Brazil", "192", "ambulance (SAMU)"],
  ["Canada", "911"],
  ["China", "120", "ambulance"],
  ["Egypt", "123", "ambulance"],
  ["European Union (any country)", "112"],
  ["India", "112", "or 108 for an ambulance"],
  ["Japan", "119"],
  ["Kenya", "999", "or 112"],
  ["Mexico", "911"],
  ["New Zealand", "111"],
  ["Nigeria", "112"],
  ["Philippines", "911"],
  ["Russia", "112", "or 103 for an ambulance"],
  ["South Africa", "10177", "ambulance · 112 from mobiles"],
  ["South Korea", "119"],
  ["Turkey", "112"],
  ["United Kingdom", "999", "112 also works"],
  ["United States", "911"],
  ["Somewhere else", "?", "Look it up today and save it in your phone as “EMERGENCY”. On many mobile networks, 112 will also connect you."],
];

export function emergencyNumber() {
  const big = h("div", { class: "num-big", "aria-live": "polite" }, "—");
  const note = h("p", { class: "num-note" }, "Choose a country to see its number.");
  const select = h("select", { class: "num-select", "aria-label": "Country" },
    NUMBERS.map(([name], i) => h("option", { value: i }, name)));
  select.addEventListener("change", () => {
    const [, num, extra] = NUMBERS[select.value];
    big.textContent = num || "—";
    note.textContent = extra || (num ? "Say it out loud three times. Then put it in your phone." : "Choose a country to see its number.");
    shake(big);
  });
  return h("div", { class: "num-widget" }, select, big, note);
}

/* ---------- 2. CPR rhythm trainer ---------- */

export function cprTrainer(onDone) {
  const GOAL = 30;
  let taps = [];
  let good = 0;
  let done = false;
  let audio = null;
  let metro = null;

  const bpmEl = h("div", { class: "bpm" }, h("span", { class: "bpm-n" }, "—"), h("span", { class: "bpm-u" }, "pushes / min"));
  const needle = h("div", { class: "needle" });
  const gauge = h("div", { class: "gauge", "aria-hidden": "true" },
    h("div", { class: "zone" }), needle,
    h("span", { class: "tick", style: "left:0%" }, "60"),
    h("span", { class: "tick", style: "left:40%" }, "100"),
    h("span", { class: "tick", style: "left:60%" }, "120"),
    h("span", { class: "tick", style: "left:100%" }, "160"));
  const msg = h("p", { class: "feedback", "aria-live": "polite" }, "Tap the chest (or press the space bar) to the beat. Aim for 100–120 a minute.");
  const bar = h("div", { class: "progress-fill" });
  const progress = h("div", { class: "progress", role: "progressbar", "aria-valuemin": 0, "aria-valuemax": GOAL, "aria-valuenow": 0 }, bar);

  const chest = h("button", { class: "chest", type: "button", "aria-label": "Push on the chest" },
    h("span", { class: "hands" }, svgHands()),
    h("span", { class: "chest-label" }, "PUSH"));

  const beat = h("div", { class: "beat-dot", title: "110 per minute" });
  const metroBtn = h("button", { class: "btn small ghost", type: "button" }, "♪ Turn on beat");

  function press(e) {
    if (e) e.preventDefault();
    const now = performance.now();
    if (taps.length && now - taps[taps.length - 1] > 2000) {
      taps = [];
      msg.textContent = "You paused. In real life, every pause stops blood reaching the brain — keep going.";
      msg.className = "feedback bad";
    }
    taps.push(now);
    if (taps.length > 7) taps.shift();
    chest.classList.remove("pushed");
    void chest.offsetWidth;
    chest.classList.add("pushed");
    if (taps.length < 4) return;

    const intervals = taps.slice(1).map((t, i) => t - taps[i]);
    const avg = intervals.reduce((a, b) => a + b, 0) / intervals.length;
    const bpm = Math.round(60000 / avg);
    bpmEl.firstChild.textContent = bpm;
    const pct = Math.max(0, Math.min(100, ((bpm - 60) / 100) * 100));
    needle.style.left = pct + "%";

    const inZone = bpm >= 100 && bpm <= 120;
    gauge.classList.toggle("ok", inZone);
    if (done) return;
    if (inZone) {
      good++;
      msg.textContent = "Perfect pace — keep it steady.";
      msg.className = "feedback good";
    } else if (bpm < 100) {
      msg.textContent = "A little faster.";
      msg.className = "feedback bad";
    } else {
      msg.textContent = "Slightly slower — let the chest come all the way back up.";
      msg.className = "feedback bad";
    }
    const g = Math.min(good, GOAL);
    bar.style.width = (g / GOAL) * 100 + "%";
    progress.setAttribute("aria-valuenow", g);
    if (!done && good >= GOAL) {
      done = true;
      msg.textContent = "✓ 30 good compressions. That's the rhythm that keeps a brain alive. Real CPR is tiring — swap with someone every 2 minutes if you can.";
      msg.className = "feedback good";
      onDone();
    }
  }

  chest.addEventListener("pointerdown", press);
  chest.addEventListener("click", (e) => { if (e.detail === 0) press(e); }); // keyboard Enter
  chest.addEventListener("keydown", (e) => {
    if (e.code === "Space") { e.preventDefault(); if (!e.repeat) press(); }
  });

  metroBtn.addEventListener("click", () => {
    if (metro) {
      clearInterval(metro);
      metro = null;
      metroBtn.textContent = "♪ Turn on beat";
      return;
    }
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      audio.resume();
    } catch { audio = null; }
    const tick = () => {
      beat.classList.remove("on"); void beat.offsetWidth; beat.classList.add("on");
      if (!audio) return;
      const o = audio.createOscillator();
      const g = audio.createGain();
      o.frequency.value = 880;
      g.gain.setValueAtTime(0.25, audio.currentTime);
      g.gain.exponentialRampToValueAtTime(0.001, audio.currentTime + 0.07);
      o.connect(g).connect(audio.destination);
      o.start();
      o.stop(audio.currentTime + 0.08);
    };
    tick();
    metro = setInterval(tick, 60000 / 110);
    metroBtn.textContent = "♪ Turn off beat";
  });

  return h("div", { class: "cpr" },
    h("div", { class: "cpr-main" }, chest,
      h("div", { class: "cpr-side" }, bpmEl, gauge,
        h("div", { class: "metro" }, metroBtn, beat,
          h("span", { class: "hint" }, "Tip: the beat of “Stayin’ Alive” is about right.")))),
    h("div", { class: "cpr-progress" }, h("span", null, "Good compressions"), progress),
    msg);
}

function svgHands() {
  // Two stacked hands, heel down, seen from above.
  return s("svg", { viewBox: "0 0 64 64", width: 60, height: 60, "aria-hidden": "true" },
    s("circle", { cx: 32, cy: 32, r: 28, fill: "none", stroke: "currentColor", "stroke-width": 2, "stroke-dasharray": "4 5", opacity: ".5" }),
    s("path", { d: "M20 40 q-2 -14 4 -20 l3 6 l2 -10 l4 0 l1 10 l2 -9 l4 1 l-1 10 l3 -6 l3 2 q2 12 -6 18 z", fill: "currentColor", opacity: ".85" }));
}

/* ---------- 4. Stroke: face demo ---------- */

export function strokeFaces() {
  const face = (droop) => {
    const mouth = s("path", { class: "mouth", d: "M40 74 Q60 76 80 74", fill: "none", stroke: "#3b2a22", "stroke-width": 4, "stroke-linecap": "round" });
    const eyeR = s("ellipse", { class: "eye", cx: 76, cy: 50, rx: 5, ry: droop ? 4 : 5, fill: "#3b2a22" });
    const svg = s("svg", { viewBox: "0 0 120 120", class: "face" + (droop ? " droop" : ""), "aria-hidden": "true" },
      s("circle", { cx: 60, cy: 60, r: 48, fill: "#f2c9a5" }),
      s("path", { d: "M18 46 Q22 10 60 12 Q98 10 102 46 Q90 26 60 28 Q30 26 18 46z", fill: "#5a3b2c" }),
      s("ellipse", { cx: 44, cy: 50, rx: 5, ry: 5, fill: "#3b2a22" }),
      eyeR, mouth);
    svg._smile = (on) => {
      if (!on) mouth.setAttribute("d", "M40 74 Q60 76 80 74");
      else if (droop) mouth.setAttribute("d", "M38 70 Q52 86 66 82 Q76 80 82 84");
      else mouth.setAttribute("d", "M38 70 Q60 92 82 70");
    };
    return svg;
  };
  const a = face(false), b = face(true);
  const btn = h("button", { class: "btn small", type: "button" }, "😀 Ask them to smile");
  let on = false;
  btn.addEventListener("click", () => {
    on = !on;
    a._smile(on); b._smile(on);
    btn.textContent = on ? "Relax face" : "😀 Ask them to smile";
  });
  return h("div", { class: "faces" },
    h("figure", null, a, h("figcaption", null, "Even smile")),
    h("figure", null, b, h("figcaption", { class: "warn" }, "One side droops → call")),
    btn);
}

/* ---------- 6. Bleeding: press and hold ---------- */

export function bleedingPress(onDone) {
  const HOLD = 6000;
  let pressing = false, started = false, done = false;
  let held = 0, pool = 14, last = 0;

  const blood = s("ellipse", { cx: 150, cy: 92, rx: 14, ry: 6, fill: "#b3121b", opacity: ".85" });
  const handG = s("g", { class: "press-hand", opacity: 0 },
    s("rect", { x: 118, y: 40, width: 64, height: 30, rx: 12, fill: "#e8b48f" }),
    s("rect", { x: 112, y: 54, width: 76, height: 16, rx: 6, fill: "#f4f1ea", stroke: "#cfc8b8" }));
  const svg = s("svg", { viewBox: "0 0 300 130", class: "arm", "aria-hidden": "true" },
    s("rect", { x: 10, y: 60, width: 280, height: 34, rx: 17, fill: "#e8b48f" }),
    s("path", { d: "M138 74 l24 4", stroke: "#7d0a10", "stroke-width": 5, "stroke-linecap": "round" }),
    blood, handG);

  const ring = h("div", { class: "hold-ring" }, h("span", null, "Press & hold"));
  const btn = h("button", { class: "hold-btn", type: "button", "aria-label": "Press and hold on the wound" }, ring);
  const msg = h("p", { class: "feedback", "aria-live": "polite" }, "Press and hold the button (or space bar) to put pressure on the wound. Don't let go.");

  function down(e) {
    if (e) e.preventDefault();
    if (done) return;
    pressing = true; started = true;
    btn.classList.add("down");
    handG.setAttribute("opacity", 1);
    msg.textContent = "Push hard. Keep pushing…";
    msg.className = "feedback";
  }
  function up() {
    if (!pressing || done) return;
    pressing = false;
    btn.classList.remove("down");
    handG.setAttribute("opacity", 0);
    if (held > 300) {
      msg.textContent = "You let go — the bleeding restarts. Don't lift to check. Press again and hold.";
      msg.className = "feedback bad";
    }
    held = 0;
  }
  btn.addEventListener("pointerdown", down);
  btn.addEventListener("pointerup", up);
  btn.addEventListener("pointerleave", up);
  btn.addEventListener("pointercancel", up);
  btn.addEventListener("contextmenu", (e) => e.preventDefault());
  btn.addEventListener("keydown", (e) => { if (e.code === "Space" || e.code === "Enter") { if (!e.repeat) down(e); else e.preventDefault(); } });
  btn.addEventListener("keyup", (e) => { if (e.code === "Space" || e.code === "Enter") up(); });

  function frame(t) {
    const dt = last ? Math.min(100, t - last) : 0;
    last = t;
    if (started && !done) {
      if (pressing) { held += dt; pool = Math.max(14, pool - dt * 0.004); }
      else pool = Math.min(120, pool + dt * 0.03);
    }
    blood.setAttribute("rx", pool);
    blood.setAttribute("ry", 6 + pool * 0.12);
    const p = Math.min(1, held / HOLD);
    ring.style.setProperty("--p", p * 360 + "deg");
    if (!done && p >= 1) {
      done = true;
      pressing = false;
      btn.classList.remove("down");
      btn.classList.add("complete");
      ring.firstChild.textContent = "✓ Held";
      msg.textContent = "✓ The bleeding is controlled. In real life, keep this up until help takes over — it can take 10 minutes or more. If blood soaks through, add cloth on top; don't remove the first layer.";
      msg.className = "feedback good";
      onDone();
    }
    if (svg.isConnected || !started) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  return h("div", { class: "bleed" }, svg, btn, msg);
}

/* ---------- 8. ORS mixer ---------- */

export function orsMixer(onDone) {
  let sugar = 0, salt = 0; // salt counted in half-teaspoons
  let done = false;
  const sugarN = h("output", null, "0");
  const saltN = h("output", null, "0");
  const spoons = h("div", { class: "spoons", "aria-hidden": "true" });
  const msg = h("p", { class: "feedback", "aria-live": "polite" }, "Your jug has 1 liter of clean water. Add sugar and salt, then check.");

  const fmtSalt = (n) => n === 0 ? "0" : n === 1 ? "½" : n % 2 ? `${(n - 1) / 2}½` : `${n / 2}`;

  function render() {
    sugarN.textContent = sugar;
    saltN.textContent = fmtSalt(salt);
    spoons.replaceChildren(
      ...Array.from({ length: sugar }, () => h("span", { class: "grain sugar" })),
      ...Array.from({ length: salt }, () => h("span", { class: "grain salt" })));
  }

  const stepper = (label, sub, out, get, set, max) => h("div", { class: "stepper" },
    h("div", { class: "stepper-label" }, h("strong", null, label), h("small", null, sub)),
    h("div", { class: "stepper-ctrl" },
      h("button", { type: "button", class: "round", "aria-label": `Less ${label}`, onClick: () => { set(Math.max(0, get() - 1)); render(); } }, "−"),
      out,
      h("button", { type: "button", class: "round", "aria-label": `More ${label}`, onClick: () => { set(Math.min(max, get() + 1)); render(); } }, "+")));

  const check = h("button", { class: "btn", type: "button" }, "Check my mix");
  check.addEventListener("click", () => {
    let text, ok = false;
    if (salt > 1) text = "Too salty — that can be dangerous, especially for a baby. Use only ½ level teaspoon of salt.";
    else if (salt === 0) text = "It needs salt: diarrhea drains the body's salts as well as water.";
    else if (sugar < 6) text = "Not enough sugar. Sugar helps the gut absorb the salt and water.";
    else if (sugar > 6) text = "Too sweet. Too much sugar can make diarrhea worse. Use exactly 6 level teaspoons.";
    else { ok = true; text = "✓ Perfect: 1 liter water · 6 level teaspoons sugar · ½ level teaspoon salt. Stir until dissolved. Make a fresh batch every day."; }
    msg.textContent = text;
    msg.className = "feedback " + (ok ? "good" : "bad");
    if (!ok) shake(check);
    if (ok && !done) { done = true; onDone(); }
  });

  render();
  return h("div", { class: "ors" },
    h("div", { class: "jug" }, h("div", { class: "water" }, spoons), h("span", { class: "jug-label" }, "1 L water")),
    h("div", { class: "ors-ctrls" },
      stepper("Sugar", "level teaspoons", sugarN, () => sugar, (v) => (sugar = v), 12),
      stepper("Salt", "level teaspoons", saltN, () => salt, (v) => (salt = v), 6),
      check, msg));
}

/* ---------- 9. Drowning: spot the swimmer ---------- */

export function drowningScene(onDone) {
  const swimmers = [
    { id: "A", x: 70, desc: "Splashing and shouting with a friend", why: "Noisy splashing and shouting usually means play. People who are drowning can't call out." },
    { id: "B", x: 190, desc: "Swimming steady strokes across the pool", why: "Steady forward strokes mean they're in control." },
    { id: "C", x: 310, desc: "Upright and silent, head tilted back, mouth at the waterline, arms pressing down at the sides", why: "✓ That's drowning. It's quiet: they can't breathe enough to shout, and their arms push down on the water instead of waving. It can take as little as 20–60 seconds. Act now: reach or throw something that floats.", correct: true },
    { id: "D", x: 430, desc: "Floating on their back, relaxed", why: "Floating on the back, breathing easily, is a safe resting position." },
  ];
  let done = false;
  const msg = h("p", { class: "feedback", "aria-live": "polite" }, "Which swimmer needs help right now? Tap them.");
  const water = s("svg", { viewBox: "0 0 500 170", class: "pool", role: "img", "aria-label": "Four people in a swimming pool" });
  water.append(
    s("rect", { x: 0, y: 0, width: 500, height: 170, rx: 14, fill: "#7cc8e8" }),
    s("path", { class: "wave", d: "M0 70 Q25 62 50 70 T100 70 T150 70 T200 70 T250 70 T300 70 T350 70 T400 70 T450 70 T500 70 T550 70 V170 H0z", fill: "#3fa3cf", opacity: ".55" }));

  const figure = (sw) => {
    const g = s("g", { class: "swimmer sw-" + sw.id, tabindex: 0, role: "button", "aria-label": `Swimmer ${sw.id}: ${sw.desc}` });
    if (sw.id === "A") {
      g.append(
        s("circle", { cx: sw.x - 14, cy: 64, r: 11, fill: "#8a5a3c" }),
        s("circle", { cx: sw.x + 16, cy: 66, r: 11, fill: "#e0b089" }),
        s("path", { d: `M${sw.x - 30} 58 l-10 -18 M${sw.x + 32} 60 l12 -16`, stroke: "#8a5a3c", "stroke-width": 6, "stroke-linecap": "round" }),
        s("g", { class: "splash" },
          s("circle", { cx: sw.x - 38, cy: 44, r: 4, fill: "#fff" }), s("circle", { cx: sw.x + 44, cy: 46, r: 5, fill: "#fff" }),
          s("circle", { cx: sw.x, cy: 46, r: 3, fill: "#fff" })),
        s("text", { x: sw.x, y: 30, "text-anchor": "middle", class: "shout" }, "Haha! Marco!"));
    } else if (sw.id === "B") {
      g.append(s("g", { class: "lap" },
        s("ellipse", { cx: sw.x, cy: 76, rx: 30, ry: 6, fill: "#c98b62" }),
        s("circle", { cx: sw.x + 32, cy: 72, r: 9, fill: "#4a3020" }),
        s("path", { class: "stroke-arm", d: `M${sw.x + 10} 72 q 10 -24 26 -14`, stroke: "#c98b62", "stroke-width": 6, fill: "none", "stroke-linecap": "round" })));
    } else if (sw.id === "C") {
      g.append(s("g", { class: "bob" },
        s("rect", { x: sw.x - 9, y: 70, width: 18, height: 60, rx: 9, fill: "#d9a07a", opacity: ".55" }),
        s("g", { transform: `rotate(-28 ${sw.x} 68)` },
          s("ellipse", { cx: sw.x, cy: 62, rx: 11, ry: 12, fill: "#d9a07a" }),
          s("path", { d: `M${sw.x + 10} 60 l5 2 l-5 3`, fill: "#d9a07a" }),
          s("path", { d: `M${sw.x - 10} 60 q 2 -14 16 -12`, stroke: "#2c1c14", "stroke-width": 7, fill: "none" })),
        s("path", { class: "press-arms", d: `M${sw.x - 8} 82 l-22 6 M${sw.x + 8} 82 l22 6`, stroke: "#d9a07a", "stroke-width": 6, opacity: ".6", "stroke-linecap": "round" })));
    } else {
      g.append(
        s("ellipse", { cx: sw.x, cy: 70, rx: 32, ry: 6, fill: "#f0c39c" }),
        s("circle", { cx: sw.x - 34, cy: 66, r: 9, fill: "#f0c39c" }),
        s("path", { d: `M${sw.x - 40} 60 q 6 -6 12 0`, stroke: "#6b4a2a", "stroke-width": 4, fill: "none" }));
    }
    g.append(s("text", { x: sw.x, y: 160, "text-anchor": "middle", class: "sw-label" }, sw.id));
    return g;
  };

  const cards = h("div", { class: "sw-cards" });
  const pick = (sw, node, card) => {
    if (done) return;
    msg.textContent = sw.why;
    msg.className = "feedback " + (sw.correct ? "good" : "bad");
    card.classList.add(sw.correct ? "right" : "wrong");
    if (sw.correct) { done = true; node.classList.add("found"); onDone(); }
    else shake(card);
  };
  for (const sw of swimmers) {
    const node = figure(sw);
    const card = h("button", { class: "option sw-card", type: "button" }, h("b", null, sw.id), " ", sw.desc);
    node.addEventListener("click", () => pick(sw, node, card));
    node.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(sw, node, card); } });
    card.addEventListener("click", () => pick(sw, node, card));
    water.append(node);
    cards.append(card);
  }
  return h("div", { class: "drown" }, water, cards, msg);
}
