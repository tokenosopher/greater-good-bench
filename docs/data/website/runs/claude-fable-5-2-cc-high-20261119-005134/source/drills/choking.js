// Drill 02 — choking. Silence is the emergency: five back blows, five thrusts.
import { s, ring, shake, ease } from "../ui.js";
import { Figure, FRONT_SPEC, SIDE_SPEC, pose } from "../figure.js";
import { sfx } from "../audio.js";

// ── Step 1: who needs you? ──────────────────────────────────────────────────────────────

function who(ctx) {
  const { sc } = ctx;
  const svg = ctx.svg("Two people at a table. One is coughing loudly, one is silent with hands at the throat.");
  svg.append(s("ellipse", { class: "floor", cx: 300, cy: 452, rx: 270, ry: 34 }));

  const make = (x, p, label, onPick) => {
    const fig = new Figure(FRONT_SPEC, p);
    const inner = s("g", {}, fig.el);
    const g = s(
      "g",
      { class: "bystander", transform: `translate(${x} 150) scale(1.7)` },
      s("rect", { class: "hit", x: -52, y: -60, width: 104, height: 246, rx: 10 }),
      inner
    );
    g.setAttribute("role", "button");
    g.setAttribute("tabindex", "0");
    g.setAttribute("aria-label", label);
    g.addEventListener("click", onPick);
    g.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onPick();
      }
    });
    svg.append(g);
    return { g, inner, fig };
  };

  let solved = false;
  const a = make(165, pose({ elL: [-36, 24], haL: [-8, -10], head: [-3, -27] }), "Person A: coughing loudly, red in the face", () => {
    if (solved) return;
    shake(a.g);
    ctx.say("Not yet. A loud cough means air is moving, and a cough is stronger than anything you can do. Stay close and say <b>“keep coughing”</b>. Don’t slap their back.", "no");
  });
  const b = make(435, pose({ elL: [-34, 30], haL: [-7, -4], elR: [34, 30], haR: [7, -4] }), "Person B: silent, hands at the throat, cannot speak", () => {
    if (solved) return;
    solved = true;
    b.g.classList.add("is-chosen");
    ctx.done("<b>Silence is the emergency.</b> If they can’t cough, speak or breathe, the airway is fully blocked and they have a few minutes. Ask “Are you choking?” — a nod is enough. Act.");
  });

  // A coughs: jolts and noise words.
  const words = [
    s("text", { class: "noise", x: 62, y: 96, transform: "rotate(-12 62 96)" }, "KHAH!"),
    s("text", { class: "noise", x: 218, y: 78, transform: "rotate(9 218 78)" }, "KHH!"),
    s("text", { class: "noise", x: 232, y: 150, transform: "rotate(-5 232 150)" }, "HACK!"),
  ];
  words.forEach((w) => ((w.style.opacity = 0), svg.append(w)));
  let n = 0;
  const cough = () => {
    const w = words[n++ % words.length];
    sc.tween(
      520,
      (t) => {
        const k = Math.sin(Math.min(1, t * 1.6) * Math.PI);
        a.inner.setAttribute("transform", `translate(${-3 * k} ${5 * k}) rotate(${-5 * k})`);
        w.style.opacity = t < 0.75 ? 1 : (1 - t) * 4;
      },
      ease.linear
    );
  };
  sc.timeout(cough, 300);
  sc.interval(cough, 900);

  // B is silent: a faint tremor only.
  svg.append(s("text", { class: "silence", x: 435, y: 62, "text-anchor": "middle" }, "(no sound)"));
  sc.frame((dt, now) => {
    b.inner.setAttribute("transform", `translate(${Math.sin(now / 45) * 0.7} 0)`);
  });

  svg.append(s("text", { class: "letter", x: 165, y: 492, "text-anchor": "middle" }, "A"), s("text", { class: "letter", x: 435, y: 492, "text-anchor": "middle" }, "B"));
  ctx.say("Tap the person who needs you to step in.", "info");
}

// ── Side-view poses ─────────────────────────────────────────────────────────────────────

const VICTIM_BENT = {
  head: [170, 196],
  neck: [205, 214],
  hip: [322, 292],
  sh: [214, 226],
  elA: [212, 284],
  haA: [186, 250],
  elB: [222, 280],
  haB: [198, 246],
  knA: [318, 374],
  ftA: [316, 452],
  knB: [336, 372],
  ftB: [344, 452],
};

const RESCUER_BLOW = {
  head: [392, 124],
  neck: [404, 160],
  hip: [434, 292],
  sh: [404, 178],
  elB: [342, 240],
  haB: [262, 268], // supporting arm across their chest
  elA: [372, 126],
  haA: [330, 92], // striking arm, raised
  knA: [430, 374],
  ftA: [436, 452],
  knB: [452, 372],
  ftB: [470, 452],
};

const STRIKE = { elA: [346, 190], haA: [272, 198] };

function backBlows(ctx) {
  const { sc } = ctx;
  const svg = ctx.svg("Side view: you stand behind a choking person who is bent forward");
  svg.append(s("line", { class: "ground", x1: 40, y1: 466, x2: 560, y2: 466 }));
  const you = new Figure(SIDE_SPEC, RESCUER_BLOW, "is-you");
  const them = new Figure(SIDE_SPEC, VICTIM_BENT);
  const themWrap = s("g", {}, them.el);
  // Draw the far (supporting) arm of the rescuer behind the victim.
  svg.append(you.el, themWrap);
  // Bring the striking arm above the victim.
  const strikeArm = you.nodes[you.nodes.length - 1];
  const top = s("g", { class: "fig is-you" }, strikeArm.halo, strikeArm.p);
  svg.append(top);

  const counter = s("text", { class: "big-count", x: 572, y: 74, "text-anchor": "end" }, "0/5");
  const label = s("text", { class: "you-label", x: 394, y: 78, "text-anchor": "middle" }, "YOU");
  svg.append(counter, label);

  let n = 0;
  let busy = false;
  const target = ring(262, 204, 24, "Strike between the shoulder blades", async () => {
    if (busy || n >= 5) return;
    busy = true;
    await you.to(STRIKE, 90, sc, ease.linear);
    sfx.hit();
    n++;
    counter.textContent = n + "/5";
    counter.classList.remove("pop");
    void counter.getBBox();
    counter.classList.add("pop");
    sc.tween(240, (t) => themWrap.setAttribute("transform", `translate(${-9 * Math.sin(t * Math.PI)} ${7 * Math.sin(t * Math.PI)})`), ease.linear);
    await you.to({ elA: RESCUER_BLOW.elA, haA: RESCUER_BLOW.haA }, 200, sc, ease.out);
    busy = false;
    if (n === 5) {
      target.remove();
      ctx.done("Five. Still stuck. Each blow is a separate attempt to knock it loose — hard, with the heel of your hand — not a pat. Now switch to thrusts.");
    }
  });
  svg.append(target);
  ctx.say("Tap the target five times. Make each one count.", "info");
}

// ── Step 3: abdominal thrusts ───────────────────────────────────────────────────────────

const VICTIM_UP = {
  head: [262, 124],
  neck: [272, 160],
  hip: [296, 296],
  sh: [272, 178],
  elA: [238, 214],
  haA: [256, 164],
  elB: [246, 218],
  haB: [262, 170],
  knA: [294, 376],
  ftA: [292, 452],
  knB: [306, 376],
  ftB: [314, 452],
};

const RESCUER_HUG = {
  head: [344, 112],
  neck: [352, 150],
  hip: [374, 296],
  sh: [350, 172],
  elA: [318, 252],
  haA: [246, 258],
  elB: [326, 256],
  haB: [252, 264],
  knA: [366, 376],
  ftA: [366, 452],
  knB: [392, 374],
  ftB: [408, 452],
};

function thrusts(ctx) {
  const { sc } = ctx;
  const svg = ctx.svg("Side view: you stand behind the choking person with your arms around them");
  svg.append(s("line", { class: "ground", x1: 40, y1: 466, x2: 560, y2: 466 }));
  const them = new Figure(SIDE_SPEC, VICTIM_UP);
  const you = new Figure(SIDE_SPEC, { ...RESCUER_HUG, elA: [330, 236], haA: [306, 268], elB: [336, 240], haB: [312, 272] }, "is-you");
  const themWrap = s("g", {}, them.el);
  svg.append(you.el, themWrap);
  const arm = you.nodes[you.nodes.length - 1];
  const top = s("g", { class: "fig is-you" }, arm.halo, arm.p);
  svg.append(top);
  const counter = s("text", { class: "big-count", x: 572, y: 74, "text-anchor": "end" }, "");
  svg.append(counter, s("text", { class: "you-label", x: 346, y: 66, "text-anchor": "middle" }, "YOU"));

  const spots = [
    { x: 240, y: 198, label: "On the breastbone", why: "Too high for an adult — that’s the breastbone. Go lower, into the soft part." },
    { x: 246, y: 258, label: "Just above the navel, below the ribs", ok: true },
    { x: 254, y: 312, label: "Below the navel", why: "Too low. You want the soft spot <b>between the navel and the ribs</b>, to drive air up from the lungs." },
  ];
  const rings = spots.map((sp) =>
    ring(sp.x, sp.y, 20, sp.label, () => {
      if (!sp.ok) {
        shake(svg);
        ctx.say(sp.why, "no");
        return;
      }
      rings.forEach((r) => r.remove());
      grip();
    })
  );
  svg.append(...rings);
  ctx.say("Where does your fist go? Tap the spot.", "info");

  async function grip() {
    await you.to({ elA: RESCUER_HUG.elA, haA: RESCUER_HUG.haA, elB: RESCUER_HUG.elB, haB: RESCUER_HUG.haB }, 320, sc);
    ctx.prompt("In and up. Five times.", "Fist just above the navel, other hand on top. Pull sharply <b>inwards and upwards</b>, as if trying to lift them off the ground.");
    ctx.say("That’s the spot. Now thrust: tap five times.", "ok");
    counter.textContent = "0/5";
    let n = 0;
    let busy = false;
    const target = ring(246, 258, 24, "Thrust inwards and upwards", async () => {
      if (busy || n >= 5) return;
      busy = true;
      sfx.hit();
      n++;
      counter.textContent = n + "/5";
      counter.classList.remove("pop");
      void counter.getBBox();
      counter.classList.add("pop");
      you.to({ haA: [264, 240], haB: [270, 246], elA: [326, 244], elB: [334, 248] }, 80, sc, ease.linear);
      await sc.tween(260, (t) => themWrap.setAttribute("transform", `translate(${6 * Math.sin(t * Math.PI)} ${-10 * Math.sin(t * Math.PI)})`), ease.linear);
      you.to({ haA: RESCUER_HUG.haA, haB: RESCUER_HUG.haB, elA: RESCUER_HUG.elA, elB: RESCUER_HUG.elB }, 160, sc);
      busy = false;
      if (n === 5) {
        target.remove();
        pop();
      }
    });
    svg.append(target);
  }

  function pop() {
    const bit = s("circle", { class: "morsel", r: 9, cx: 236, cy: 132 });
    svg.append(bit);
    sfx.good();
    sc.tween(
      900,
      (t) => {
        bit.setAttribute("cx", 236 - 150 * t);
        bit.setAttribute("cy", 132 - 70 * Math.sin(t * Math.PI) + 300 * t * t);
      },
      ease.linear
    );
    them.to({ elA: [262, 238], haA: [240, 290], elB: [270, 240], haB: [250, 292] }, 500, sc);
    ctx.done(
      "It’s out. In real life, <b>keep alternating 5 blows and 5 thrusts</b> until it clears. Have someone call {n}. If they go limp: lower them to the floor and start CPR. Anyone who’s had thrusts should see a doctor afterwards."
    );
  }
}

export default {
  id: "choking",
  num: "02",
  name: "Choking",
  blurb: "Silence is the emergency. Five blows, five thrusts.",
  minutes: 1,
  steps: [
    {
      tag: "Spot it",
      title: "Who needs you?",
      text: "Dinner. Two people have something caught in their throat at the same moment. <b>One of them is in real danger.</b>",
      setup: who,
    },
    {
      tag: "5 blows",
      title: "Five back blows.",
      text: "Stand to the side and slightly behind. Support their chest with one hand and <b>lean them well forward</b>, so whatever comes loose falls out instead of further in. Hit hard between the shoulder blades with the heel of your hand.",
      setup: backBlows,
    },
    {
      tag: "5 thrusts",
      title: "Five abdominal thrusts.",
      text: "Stand behind them and wrap your arms around their waist. First: where does your fist go?",
      setup: thrusts,
    },
  ],
  keepTitle: "Five and five.",
  keep: [
    { word: "Coughing", line: "Leave them be. Say “keep coughing.” Stay close." },
    { word: "Silent", line: "Lean them forward. 5 hard blows between the shoulder blades." },
    { word: "Still stuck", line: "5 thrusts: fist above the navel, pull in and up. Repeat 5 and 5." },
    { word: "Goes limp", line: "Onto the floor. Call {n}. Start CPR." },
  ],
  also: [
    "<b>Baby under one:</b> face-down along your forearm, head lower than chest, 5 back blows. Turn over, 5 chest thrusts with two fingers. Never abdominal thrusts.",
    "<b>Pregnant, or too large to reach around:</b> thrust on the breastbone instead. <b>Alone and choking:</b> drive your upper belly onto the back of a chair.",
  ],
};
