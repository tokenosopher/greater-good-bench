// Drill 01 — a person collapses. Check, call, push, shock.
import { h, s, ring, shake, clamp, ease } from "../ui.js";
import { Figure, FRONT_SPEC, FRONT, pose } from "../figure.js";
import { sfx, metronome, wake } from "../audio.js";
import { state, num } from "../state.js";

const RATE_MIN = 100;
const RATE_MAX = 120;
const GOAL = 30;

// ── Step 1: check ───────────────────────────────────────────────────────────────────────

function check(ctx) {
  const { sc } = ctx;
  const svg = ctx.svg("A person lying on the ground, seen from above");
  svg.append(s("ellipse", { class: "floor", cx: 300, cy: 276, rx: 278, ry: 128 }));
  const body = s("g", { transform: "translate(177 270) rotate(-90) scale(2.1)" });
  const fig = new Figure(FRONT_SPEC, FRONT);
  const wrap = s("g", {}, body);
  body.append(fig.el);
  svg.append(wrap);

  const shout = s("text", { class: "shout", x: 300, y: 96, "text-anchor": "middle" }, "“ARE YOU OKAY?”");
  shout.style.opacity = 0;
  svg.append(shout);

  const gasp = s(
    "g",
    { class: "gasp", opacity: 0 },
    s("path", { d: "M66 236 q-16 -10 -30 -4" }),
    s("path", { d: "M60 270 h-34" }),
    s("path", { d: "M66 304 q-16 10 -30 4" }),
    s("text", { x: 52, y: 350, "text-anchor": "middle" }, "…gasp…")
  );
  svg.append(gasp);

  let taps = 0;
  const rings = [];
  const onTap = () => {
    taps++;
    sfx.hit();
    shout.style.opacity = 1;
    shout.classList.remove("pop");
    void shout.getBBox();
    shout.classList.add("pop");
    sc.tween(260, (t) => wrap.setAttribute("transform", `translate(0 ${Math.sin(t * Math.PI * 3) * 5 * (1 - t)})`));
    if (taps === 1) ctx.say("Again. Firm taps, loud voice.", "info");
    if (taps >= 2) {
      rings.forEach((r) => r.remove());
      sc.timeout(listen, 700);
    }
  };
  rings.push(ring(185, 316, 26, "Tap the near shoulder", onTap), ring(185, 224, 26, "Tap the far shoulder", onTap));
  svg.append(...rings);

  function listen() {
    shout.style.opacity = 0.25;
    ctx.prompt(
      "No response. Is this breathing?",
      "Watch the chest for up to 10 seconds. You are looking for <b>normal</b> breathing — steady, quiet, regular."
    );
    ctx.say("Nothing. No movement, no answer.", "info");
    const torso = fig.nodes[2].p;
    const doGasp = () => {
      sc.tween(
        520,
        (t) => {
          const k = Math.sin(t * Math.PI);
          torso.setAttribute("stroke-width", 14 + 6 * k);
          gasp.setAttribute("opacity", k);
        },
        ease.linear
      );
    };
    sc.timeout(doGasp, 500);
    sc.interval(doGasp, 3400);

    const yes = h("button", { class: "btn btn-choice", type: "button" }, "Yes — they’re breathing");
    const no = h("button", { class: "btn btn-choice", type: "button" }, "No — that’s not normal breathing");
    yes.onclick = () => {
      yes.classList.add("is-wrong");
      yes.disabled = true;
      ctx.say(
        "Look again: one snoring gasp every few seconds, then nothing. That is <b>agonal gasping</b>. It is common in the first minutes after a heart stops, and it fools people into waiting.",
        "no"
      );
    };
    no.onclick = () => {
      no.classList.add("is-right");
      yes.disabled = true;
      ctx.done(
        "Right. <b>No response + no normal breathing = cardiac arrest.</b> Occasional gasps don’t count. If you’re not sure, act as if it is."
      );
    };
    ctx.actions.append(yes, no);
  }
}

// ── Step 2: call ────────────────────────────────────────────────────────────────────────

function call(ctx) {
  const { sc } = ctx;
  const svg = ctx.svg("Five bystanders standing around a collapsed person");
  svg.append(s("ellipse", { class: "floor", cx: 300, cy: 430, rx: 250, ry: 58 }));
  const victim = s("g", { transform: "translate(213 428) rotate(-90) scale(1.3)" });
  victim.append(new Figure(FRONT_SPEC, FRONT).el);
  svg.append(victim);

  const variants = [
    pose({ elL: [-36, 26], haL: [-12, -8] }), // hand to mouth
    pose({}),
    pose({ elL: [-30, 36], haL: [-4, 44], elR: [30, 36], haR: [4, 50] }), // arms crossed
    pose({ elR: [40, 12], haR: [20, -34], elL: [-40, 12], haL: [-20, -34] }), // hands on head
    pose({ elR: [34, 34], haR: [22, 62] }),
  ];
  const xs = [84, 192, 300, 408, 516];
  const ys = [112, 92, 104, 90, 110];
  let phase = 0;
  let caller = -1;

  const people = xs.map((x, i) => {
    const fig = new Figure(FRONT_SPEC, variants[i]);
    const dots = s("text", { class: "thought", x: 0, y: -62, "text-anchor": "middle" }, "…");
    const tag = s("text", { class: "tag", x: 0, y: 206, "text-anchor": "middle" }, "");
    const g = s(
      "g",
      { class: "bystander", transform: `translate(${x} ${ys[i]})` },
      s("rect", { class: "hit", x: -48, y: -74, width: 96, height: 290, rx: 12 }),
      fig.el,
      dots,
      tag
    );
    g.setAttribute("role", "button");
    g.setAttribute("tabindex", "0");
    g.setAttribute("aria-label", `Bystander ${i + 1}`);
    const act = () => pick(i);
    g.addEventListener("click", act);
    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        act();
      }
    });
    svg.append(g);
    return { g, fig, dots, tag, x, y: ys[i] };
  });

  ctx.say("Step one: choose a person to make the call.", "info");

  function pick(i) {
    const p = people[i];
    if (phase === 0) {
      phase = 1;
      caller = i;
      sfx.tap();
      p.g.classList.add("is-chosen");
      p.dots.textContent = "";
      p.tag.textContent = "CALLING " + num();
      p.fig.to({ elR: [38, 10], haR: [20, -26], elL: [-32, 40], haL: [-34, 76] }, 350, sc);
      ctx.prompt("Now send one for a defibrillator.", "Point at someone else: <b>“You — find an AED and bring it here.”</b> Shops, stations, gyms and offices often have one on the wall.");
      ctx.say("One person, one job. They’re dialling.", "ok");
    } else if (phase === 1) {
      if (i === caller) {
        shake(p.g);
        ctx.say("They’re on the phone. Pick someone else.", "no");
        return;
      }
      phase = 2;
      sfx.tap();
      p.g.classList.add("is-chosen");
      p.dots.textContent = "";
      p.tag.textContent = "FETCHING AED";
      const dir = p.x > 300 ? 1 : -1;
      const run = pose({
        elL: [-34, 28],
        haL: [-52, 44],
        elR: [38, 30],
        haR: [50, 6],
        knL: [-30, 118],
        ftL: [-56, 150],
        knR: [30, 120],
        ftR: [22, 170],
      });
      svg.append(p.g);
      p.fig.to(run, 220, sc).then(() =>
        sc.tween(
          900,
          (t) => {
            p.g.setAttribute("transform", `translate(${p.x + dir * 300 * t} ${p.y - Math.abs(Math.sin(t * 14)) * 6})`);
            p.g.style.opacity = 1 - Math.max(0, t - 0.25) / 0.5;
          },
          ease.inOut
        )
      );
      people.forEach((q) => q.g.setAttribute("tabindex", "-1"));
      sc.timeout(
        () =>
          ctx.done(
            "“Somebody call an ambulance!” gets nobody — everyone waits for someone else. A finger pointed at one person gets it done. <b>Alone?</b> Call {n} on speaker yourself and start pushing."
          ),
        900
      );
    }
  }
}

// ── Step 3: push ────────────────────────────────────────────────────────────────────────

function torsoCloseUp(svg) {
  const g = s("g", { transform: "translate(300 150) scale(3)" });
  const fig = new Figure(FRONT_SPEC, pose({ elL: [-36, 40], haL: [-42, 76], elR: [36, 40], haR: [42, 76] }));
  g.append(fig.el);
  svg.append(g);
  return { g, fig };
}

function handsGlyph() {
  return s(
    "g",
    { class: "hands" },
    s("rect", { class: "hand hand-under", x: -34, y: -19, width: 68, height: 38, rx: 16, transform: "rotate(24)" }),
    s("rect", { class: "hand", x: -34, y: -19, width: 68, height: 38, rx: 16, transform: "rotate(-24)" }),
    s("path", { class: "hand-lines", d: "M-12 -8 l20 9 M-16 1 l20 9" })
  );
}

function push(ctx) {
  const { sc, stage } = ctx;

  const rateNum = h("b", {}, "—");
  const word = h("div", { class: "hud-word" }, "Place your hands");
  const count = h("b", {}, "0");
  const hud = h(
    "div",
    { class: "hud" },
    h("div", { class: "hud-rate" }, rateNum, h("span", {}, "pushes a minute")),
    word,
    h("div", { class: "hud-count" }, count, h("span", {}, `of ${GOAL} on tempo`))
  );
  stage.append(hud);

  const svg = ctx.svg("A chest seen from above");
  const { g: torsoG } = torsoCloseUp(svg);

  // Tempo strip: every push lands as a dot; the band is 100–120 a minute.
  const strip = s("svg", { class: "tempo", viewBox: "0 0 600 84", role: "img", "aria-label": "Tempo of your last pushes" });
  const yFor = (bpm) => 78 - ((clamp(bpm, 70, 150) - 70) / 80) * 72;
  strip.append(
    s("rect", { class: "tempo-band", x: 46, y: yFor(RATE_MAX), width: 548, height: yFor(RATE_MIN) - yFor(RATE_MAX), rx: 4 }),
    s("text", { class: "tempo-label", x: 38, y: yFor(RATE_MAX) + 5, "text-anchor": "end" }, "120"),
    s("text", { class: "tempo-label", x: 38, y: yFor(RATE_MIN) + 5, "text-anchor": "end" }, "100"),
    s("text", { class: "tempo-edge", x: 590, y: 13, "text-anchor": "end" }, "too fast"),
    s("text", { class: "tempo-edge", x: 590, y: 80, "text-anchor": "end" }, "too slow")
  );
  const dotsG = s("g", {});
  strip.append(dotsG);
  stage.append(strip);

  // Phase A: where do the hands go?
  const spots = [
    { x: 300, y: 164, label: "High on the chest, near the throat", why: "Too high. That’s the top of the breastbone, near the throat." },
    { x: 366, y: 216, label: "Left side of the chest, over the heart", why: "Not over the heart on the left. The heart sits behind the breastbone — go for the <b>centre</b>." },
    { x: 300, y: 236, label: "Centre of the chest", ok: true },
    { x: 300, y: 336, label: "Stomach", why: "Too low — that’s the stomach. Pushing there does nothing for the heart." },
  ];
  const rings = spots.map((sp) =>
    ring(sp.x, sp.y, 18, sp.label, () => {
      if (sp.ok) {
        rings.forEach((r) => r.remove());
        begin();
      } else {
        shake(svg);
        ctx.say(sp.why, "no");
      }
    })
  );
  svg.append(...rings);
  ctx.say("First: where do your hands go? Tap the spot.", "info");

  // Phase B: compressions.
  const beatRing = s("circle", { class: "beat-ring", cx: 300, cy: 236, r: 46, opacity: 0 });
  const ripple = s("circle", { class: "ripple", cx: 300, cy: 236, r: 40, opacity: 0 });
  const hands = handsGlyph();
  const handsWrap = s("g", { transform: "translate(300 236)" }, hands);
  const cue = s("text", { class: "cue", x: 300, y: 478, "text-anchor": "middle" }, "TAP THE CHEST — OR PRESS SPACE");

  let active = false;
  let finished = false;
  let last = 0;
  let intervals = [];
  let all = [];
  let inZone = 0;
  let pushes = 0;
  let metro = null;
  let beatOn = true;
  let pressT = 0;

  function begin() {
    active = true;
    svg.append(beatRing, ripple, handsWrap, cue);
    svg.classList.add("is-pushable");
    word.textContent = "Push to the beat";
    ctx.prompt(
      "Push. Hard. Fast.",
      "Tap the chest in time with the beat — <b>100 to 120 pushes a minute</b>. Land " +
        GOAL +
        " on tempo. Halfway through, the beat goes silent and you keep it going alone."
    );
    ctx.say("Dead centre. Heel of one hand, the other on top, arms locked straight.", "ok");
    metro = metronome({
      bpm: 110,
      audible: () => beatOn,
      onBeat: () => {
        if (!beatOn) return;
        sc.tween(380, (t) => {
          beatRing.setAttribute("r", 46 + 34 * t);
          beatRing.setAttribute("opacity", 0.9 * (1 - t));
        });
      },
    });
    metro.start();
    sc.add(() => metro.stop());
  }

  function setWord(text, kind) {
    word.textContent = text;
    word.dataset.kind = kind || "";
  }

  function compress() {
    if (!active || finished) return;
    const now = performance.now();
    pushes++;
    sfx.thump();
    pressT = 1;
    cue.style.opacity = 0;
    const gap = now - last;
    last = now;
    if (pushes === 1 || gap > 1500) {
      intervals = [];
      if (pushes > 1) setWord("Keep going", "");
      return;
    }
    intervals.push(gap);
    if (intervals.length > 3) intervals.shift();
    const recent = intervals.slice(-2);
    const bpm = 60000 / (recent.reduce((a, b) => a + b, 0) / recent.length);
    all.push(60000 / gap);
    const ok = bpm >= RATE_MIN - 4 && bpm <= RATE_MAX + 4;
    rateNum.textContent = String(Math.round(bpm));
    hud.dataset.kind = ok ? "ok" : "no";
    if (ok) {
      inZone++;
      setWord(beatOn ? "Good — hold that" : "Good — it’s all you now", "ok");
    } else if (bpm < RATE_MIN) setWord("Faster", "no");
    else setWord("Slower", "no");
    count.textContent = String(Math.min(GOAL, inZone));

    // Plot the dot and scroll older ones left.
    dotsG.append(s("circle", { class: "tempo-dot " + (ok ? "is-ok" : "is-no"), cy: yFor(bpm), r: 6.5 }));
    const dots = [...dotsG.children];
    if (dots.length > 28) dots.shift().remove();
    dots.forEach((d, i) => d.setAttribute("cx", 582 - (dots.length - 1 - i) * 19.4));

    if (beatOn && inZone >= GOAL / 2) {
      beatOn = false;
      beatRing.setAttribute("opacity", 0);
      ctx.say("<b>The beat is gone.</b> Keep the same tempo from memory — this is what it’s like for real.", "info");
    }
    if (inZone >= GOAL) finish();
  }

  function finish() {
    finished = true;
    metro?.stop();
    svg.classList.remove("is-pushable");
    const avg = Math.round(all.reduce((a, b) => a + b, 0) / all.length);
    const steady = Math.round((inZone / all.length) * 100);
    state.results.cpr = { avg, steady };
    setWord("That’s CPR", "ok");
    ctx.done(
      `${GOAL} pushes on tempo, averaging <b>${avg} a minute</b>. For real: push <b>5–6 cm deep</b> — harder than feels polite — let the chest spring back up, and don’t stop. It’s exhausting; swap with someone every 2 minutes.`
    );
  }

  svg.addEventListener("pointerdown", (e) => {
    if (!active || finished) return;
    e.preventDefault();
    wake();
    compress();
  });
  sc.on(window, "keydown", (e) => {
    if (e.code !== "Space" || !active || finished) return;
    e.preventDefault();
    if (!e.repeat) compress();
  });

  sc.frame((dt, now) => {
    if (!active) return;
    pressT = Math.max(0, pressT - dt * 6.5);
    const k = ease.out(pressT);
    hands.setAttribute("transform", `scale(${1 - 0.16 * k})`);
    torsoG.setAttribute("transform", `translate(300 ${150 + 3 * k}) scale(${3 + 0.03 * k} ${3 - 0.05 * k})`);
    ripple.setAttribute("r", 40 + 60 * (1 - pressT));
    ripple.setAttribute("opacity", pressT * 0.5);
    if (!finished && pushes > 1 && now - last > 1900) {
      setWord("Don’t stop", "no");
      hud.dataset.kind = "no";
    }
  });
}

// ── Step 4: shock ───────────────────────────────────────────────────────────────────────

function shock(ctx) {
  const { sc, stage } = ctx;
  const voice = h("div", { class: "aed-voice" }, h("span", { class: "aed-led" }), h("span", { class: "aed-text" }, "AED ON. “Attach pads to the patient’s bare chest.”"));
  stage.append(voice);
  const say = (t) => (voice.querySelector(".aed-text").textContent = t);

  const svg = ctx.svg("A bare chest seen from above, with places a pad could go");
  const { g: torsoG } = torsoCloseUp(svg);
  svg.append(
    s("text", { class: "side-note", x: 150, y: 150, "text-anchor": "middle" }, "THEIR RIGHT"),
    s("text", { class: "side-note", x: 450, y: 150, "text-anchor": "middle" }, "THEIR LEFT")
  );

  const zones = [
    { x: 254, y: 200, ok: true, label: "Upper chest on their right, below the collarbone" },
    { x: 346, y: 200, label: "Upper chest on their left", why: "Both pads up high leaves the heart outside the path. One goes <b>upper right</b>, one <b>lower left</b> — so the current crosses the heart." },
    { x: 246, y: 284, label: "Lower ribs on their right", why: "Wrong side for the lower pad. It goes on their <b>left</b> side, under the armpit." },
    { x: 356, y: 284, ok: true, label: "Side of the chest on their left, below the armpit" },
    { x: 300, y: 366, label: "Stomach", why: "Not the stomach. The two pads need the heart between them." },
  ];
  let placed = 0;
  const zoneEls = zones.map((z) => {
    const g = s(
      "g",
      { class: "pad-zone", transform: `translate(${z.x} ${z.y})` },
      s("rect", { class: "pad-outline", x: -34, y: -27, width: 68, height: 54, rx: 9 }),
      s("rect", { class: "ring-hit", x: -40, y: -33, width: 80, height: 66, rx: 9 })
    );
    g.setAttribute("role", "button");
    g.setAttribute("tabindex", "0");
    g.setAttribute("aria-label", z.label);
    const act = () => {
      if (g.classList.contains("is-placed") || placed >= 2) return;
      if (!z.ok) {
        shake(g);
        ctx.say(z.why, "no");
        return;
      }
      sfx.tap();
      g.classList.add("is-placed");
      g.append(s("path", { class: "pad-bolt", d: "M4 -17 L-9 3 H0 L-4 17 L9 -3 H0 Z" }));
      placed++;
      if (placed === 1) ctx.say("One on. And the other?", "ok");
      if (placed === 2) analyse();
    };
    g.addEventListener("click", act);
    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        act();
      }
    });
    svg.append(g);
    return g;
  });

  ctx.say("Two pads. Tap the two places they go.", "info");

  async function analyse() {
    zoneEls.forEach((g) => !g.classList.contains("is-placed") && g.remove());
    ctx.say("Pads on. The pictures printed on real pads show exactly this.", "ok");
    say("“Analysing heart rhythm. Do not touch the patient.”");
    voice.classList.add("is-busy");
    await sc.wait(2200);
    voice.classList.remove("is-busy");
    say("“Shock advised. Stand clear. Press the flashing button.”");
    ctx.prompt("Everyone clear. Press it.", "Nobody touching the person — look, and say “stand clear” out loud. Then press the flashing button.");
    const btn = h("button", { class: "shock-btn", type: "button", "aria-label": "Deliver shock" }, s("svg", { viewBox: "-20 -24 40 48", "aria-hidden": "true" }, s("path", { d: "M5 -22 L-13 4 H-1 L-6 22 L13 -5 H1 Z" })));
    stage.append(btn);
    btn.focus({ preventScroll: true });
    btn.onclick = async () => {
      btn.remove();
      sfx.shock();
      stage.classList.add("flash");
      sc.tween(420, (t) => torsoG.setAttribute("transform", `translate(300 ${150 - Math.sin(t * Math.PI) * 14}) scale(3)`), ease.linear);
      await sc.wait(500);
      stage.classList.remove("flash");
      say("“Shock delivered. Continue CPR.”");
      ctx.done(
        "Straight back to pushing. <b>An AED only shocks a heart that needs it</b> — you cannot hurt someone with one, and it needs no training. It will re-check every 2 minutes."
      );
    };
  }
}

export default {
  id: "cpr",
  num: "01",
  name: "Collapse",
  blurb: "Their heart has stopped. Yours is racing. Check, call, push, shock.",
  minutes: 3,
  steps: [
    {
      tag: "Check",
      title: "Tap. Shout.",
      text: "Someone has just dropped to the floor in front of you. Tap both shoulders firmly and shout at them.",
      setup: check,
    },
    {
      tag: "Call",
      title: "Point at one person.",
      text: "A crowd has gathered. Each of them assumes someone else has already phoned. <b>Nobody has.</b> Choose one person: “You — call {n}. Put it on speaker.”",
      setup: call,
    },
    {
      tag: "Push",
      title: "Hands on the chest.",
      text: "Until a defibrillator arrives, <b>you are their heartbeat</b>. Your pushes are the only thing moving blood to the brain.",
      stageClass: "stage--push",
      setup: push,
    },
    {
      tag: "Shock",
      title: "The AED arrives.",
      text: "Open the lid or press the green button. <b>It talks.</b> It tells you every step. Keep pushing while someone else sticks the pads on.",
      stageClass: "stage--aed",
      setup: shock,
    },
  ],
  keepTitle: "Check. Call. Push. Shock.",
  keep: [
    { word: "Check", line: "No response and no normal breathing. Gasping doesn’t count." },
    { word: "Call", line: "{n}, on speaker. Point at one person to fetch an AED." },
    { word: "Push", line: "Centre of the chest. 100–120 a minute, 5–6 cm deep. Don’t stop." },
    { word: "Shock", line: "Switch the AED on and do exactly what it says." },
  ],
  also: [
    "<b>Child or baby, or someone pulled from water?</b> Air matters more. If you can, give 2 breaths after every 30 pushes. One hand for a child, two fingers for a baby, pressing a third of the chest’s depth.",
    "Without CPR, the chance of surviving falls about 10% each minute. With it, the odds double or triple.",
  ],
};
