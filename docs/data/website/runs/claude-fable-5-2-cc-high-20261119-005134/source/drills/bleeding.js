// Drill 03 — severe bleeding. Press, don't peek, pack on top, tourniquet above.
import { h, s, ring, shake, clamp, ease } from "../ui.js";
import { choiceStep } from "../drill.js";
import { sfx, wake } from "../audio.js";

const HOLD_SECONDS = 8;

function arm(svg, { woundX }) {
  // A forearm lying across the stage: body to the left, hand to the right.
  svg.append(
    s("path", { class: "limb", d: "M-40 180 L456 196 V276 L-40 292 Z" }),
    s("path", { class: "limb-hand", d: "M468 236 H522" }),
    s("path", { class: "limb-thumb", d: "M474 214 L508 176" }),
    s("path", { class: "wound", d: `M${woundX - 24} 250 l12 -22 l8 14 l10 -24 l8 16 l10 -18` })
  );
}

// ── Step 1: press and hold ──────────────────────────────────────────────────────────────

function press(ctx) {
  const { sc, stage } = ctx;
  const lostNum = h("b", {}, "0.0");
  const word = h("div", { class: "hud-word" }, "Bleeding");
  const clockNum = h("b", {}, "0:00");
  const hud = h(
    "div",
    { class: "hud" },
    h("div", { class: "hud-rate" }, lostNum, h("span", {}, "litres lost · about 5 in a body")),
    word,
    h("div", { class: "hud-count" }, clockNum, h("span", {}, "of 10:00 held"))
  );
  stage.append(hud);

  const svg = ctx.svg("A forearm with a deep wound, bleeding onto the floor");
  const pool = s("ellipse", { class: "blood", cx: 300, cy: 438, rx: 10, ry: 4 });
  const stream = s("path", { class: "blood-stream", d: "M300 262 V436" });
  svg.append(pool, stream);
  arm(svg, { woundX: 300 });

  const cloth = s("rect", { class: "cloth", x: 244, y: 180, width: 112, height: 112, rx: 10, transform: "rotate(-6 300 236)" });
  const soak = s("circle", { class: "soak", cx: 300, cy: 240, r: 0 });
  const palm = s(
    "g",
    { class: "palm" },
    s("rect", { class: "hand", x: 258, y: 196, width: 84, height: 62, rx: 22 }),
    s("path", { class: "hand-fingers", d: "M270 196 V160 M290 196 V150 M310 196 V152 M330 196 V164 M258 232 L232 214" })
  );
  const C = 2 * Math.PI * 78;
  const prog = s("circle", { class: "hold-ring", cx: 300, cy: 236, r: 78, "stroke-dasharray": C, "stroke-dashoffset": C, transform: "rotate(-90 300 236)" });
  const dressing = s("g", { opacity: 0 }, cloth, soak, palm, prog);
  svg.append(dressing);

  const target = ring(300, 236, 34, "Press and hold on the wound", () => {});
  target.classList.add("ring--hold");
  svg.append(target);
  const cue = s("text", { class: "cue", x: 300, y: 122, "text-anchor": "middle" }, "PRESS AND HOLD — DON’T LET GO");
  svg.append(cue);

  let holding = false;
  let held = 0;
  let lost = 0.2;
  let finished = false;
  let peeks = 0;

  const start = (e) => {
    if (finished || holding) return;
    e?.preventDefault?.();
    wake();
    holding = true;
    sfx.hit();
    dressing.setAttribute("opacity", 1);
    target.classList.add("is-held");
    word.textContent = "Pressing";
    hud.dataset.kind = "ok";
    cue.textContent = "KEEP PRESSING";
  };
  const stop = () => {
    if (!holding || finished) return;
    holding = false;
    peeks++;
    held = 0;
    dressing.setAttribute("opacity", 0);
    target.classList.remove("is-held");
    word.textContent = "Bleeding again";
    hud.dataset.kind = "no";
    cue.textContent = "PRESS AND HOLD — DON’T LET GO";
    shake(svg);
    ctx.say("<b>You let go.</b> Lifting off to look tears away the clot that was forming, and the clock starts again. Press and keep pressing.", "no");
  };

  target.addEventListener("pointerdown", (e) => {
    target.setPointerCapture?.(e.pointerId);
    start(e);
  });
  target.addEventListener("pointerup", stop);
  target.addEventListener("pointercancel", stop);
  target.addEventListener("contextmenu", (e) => e.preventDefault());
  target.addEventListener("keydown", (e) => {
    if ((e.key === " " || e.key === "Enter") && !e.repeat) start(e);
  });
  target.addEventListener("keyup", (e) => {
    if (e.key === " " || e.key === "Enter") stop();
  });
  target.addEventListener("blur", stop);

  ctx.say("Press on the wound and hold. Mouse, finger, or Space bar.", "info");

  sc.frame((dt, now) => {
    if (finished) return;
    if (holding) {
      held += dt;
      const p = clamp(held / HOLD_SECONDS, 0, 1);
      prog.setAttribute("stroke-dashoffset", C * (1 - p));
      soak.setAttribute("r", 8 + 30 * p);
      clockNum.textContent = Math.floor(p * 10) + ":" + String(Math.floor((p * 600) % 60)).padStart(2, "0");
      stream.style.opacity = 0;
      if (p >= 1) {
        finished = true;
        clockNum.textContent = "10:00";
        word.textContent = "Held";
        cue.textContent = "";
        target.classList.add("is-complete");
        state_done();
      }
    } else {
      lost = Math.min(2.6, lost + dt * 0.055);
      stream.style.opacity = 1;
      stream.setAttribute("stroke-dashoffset", -now / 9);
      clockNum.textContent = "0:00";
    }
    lostNum.textContent = lost.toFixed(1);
    const k = lost / 2.6;
    pool.setAttribute("rx", 16 + 230 * Math.sqrt(k));
    pool.setAttribute("ry", 5 + 34 * Math.sqrt(k));
    if (lost > 1.5 && !holding) {
      word.textContent = "Critical";
    }
  });

  function state_done() {
    ctx.done(
      (peeks ? "That’s it — no peeking this time. " : "Rock steady. ") +
        "Firm, direct pressure stops most bleeding, even bad bleeding. Use any cloth, or your bare hands. Lean your body weight into it and <b>hold for a full 10 minutes</b>, or until help takes over."
    );
  }
}

// ── Step 3: tourniquet ──────────────────────────────────────────────────────────────────

function tourniquet(ctx) {
  const { sc } = ctx;
  const svg = ctx.svg("An arm from shoulder to hand, with a wound on the forearm");
  svg.append(s("ellipse", { class: "blood", cx: 390, cy: 420, rx: 150, ry: 26 }));
  svg.append(s("path", { class: "blood-stream", d: "M390 262 V418" }));
  arm(svg, { woundX: 390 });
  svg.append(
    s("path", { class: "crease", d: "M222 196 q10 40 0 80" }),
    s("text", { class: "side-note", x: 60, y: 160 }, "← TO THE HEART"),
    s("text", { class: "side-note", x: 222, y: 330, "text-anchor": "middle" }, "ELBOW"),
    s("text", { class: "side-note", x: 390, y: 330, "text-anchor": "middle" }, "WOUND")
  );

  const spots = [
    { x: 222, label: "On the elbow", why: "Never on a joint — the strap can’t squeeze an artery against a hinge. Go above or below the joint." },
    { x: 312, ok: true, label: "A hand’s width above the wound, between wound and heart" },
    { x: 390, label: "Directly on the wound", why: "Not on the wound itself. A tourniquet goes <b>above</b> it, to shut off the supply." },
    { x: 448, label: "Below the wound, towards the hand", why: "Blood arrives from the heart side. Tighten there and the wound keeps pouring. Go <b>between the wound and the heart</b>." },
  ];
  const rings = spots.map((sp) =>
    ring(sp.x, 236, 22, sp.label, () => {
      if (!sp.ok) {
        shake(svg);
        ctx.say(sp.why, "no");
        return;
      }
      rings.forEach((r) => r.remove());
      apply(sp.x);
    })
  );
  svg.append(...rings);
  ctx.say("Tap where the tourniquet goes.", "info");

  async function apply(x) {
    sfx.tap();
    const strap = s("path", { class: "strap", d: `M${x} 180 V292` });
    const rod = s("path", { class: "rod", d: `M${x - 34} 236 H${x + 34}`, transform: `rotate(0 ${x} 236)` });
    svg.append(strap, rod);
    const stream = svg.querySelector(".blood-stream");
    await sc.tween(
      1300,
      (t) => {
        rod.setAttribute("transform", `rotate(${t * 540 + 20} ${x} 236)`);
        strap.setAttribute("stroke-width", 22 - 6 * t);
        stream.style.opacity = 1 - t;
      },
      ease.inOut
    );
    const now = new Date();
    const stamp = String(now.getHours()).padStart(2, "0") + ":" + String(now.getMinutes()).padStart(2, "0");
    svg.append(s("text", { class: "stamp", x: x, y: 150, "text-anchor": "middle" }, "T " + stamp));
    ctx.done(
      "5–7 cm above the wound, never on a joint. <b>Twist until the bleeding stops</b> — it will hurt, and that is correct. Write the time on it or on their skin. Do not loosen it; that’s for the hospital. If unsure where: go high on the limb, and tight."
    );
  }
}

export default {
  id: "bleeding",
  num: "03",
  name: "Bleeding",
  blurb: "A person can bleed to death in five minutes. Your hands are the bandage.",
  minutes: 1,
  steps: [
    {
      tag: "Press",
      title: "Press hard. Stay there.",
      text: `Blood is pouring from a deep cut. Someone is calling {n}. A person can bleed to death in <b>five minutes</b> — long before an ambulance. Press on the wound and hold for ${HOLD_SECONDS} seconds; here, that stands for ten minutes.`,
      stageClass: "stage--push",
      setup: press,
    },
    choiceStep({
      tag: "Soaked",
      title: "The cloth is soaked through.",
      text: "Blood is coming through the shirt you’re pressing with.",
      scene: "Three minutes in",
      quote: "The cloth under your hands is red and wet. Blood is starting to seep between your fingers.",
      options: [
        { label: "Take it off and put on a fresh one", why: "That pulls the forming clot away with it — you’re back to zero. Leave it where it is." },
        { label: "Put another on top and press harder", ok: true, why: "Yes. <b>Never remove, only add.</b> More cloth on top, more weight behind it. If the wound is deep and wide, pack cloth into it and press on that." },
        { label: "Lift a corner to check on it", why: "Don’t peek. If it’s soaking through, you already know the answer: more pressure." },
      ],
    }),
    {
      tag: "Tourniquet",
      title: "It won’t stop.",
      text: "It’s an arm, and pressure isn’t enough. Time for a tourniquet: a proper one if there is one, otherwise a wide strip of cloth twisted tight with a stick. <b>Where does it go?</b>",
      setup: tourniquet,
    },
  ],
  keepTitle: "Press. Don’t peek.",
  keep: [
    { word: "Press", line: "Hard, straight onto the wound. Cloth or bare hands. Ten minutes." },
    { word: "Don’t peek", line: "Soaked through? Add more on top. Never lift it off." },
    { word: "Tourniquet", line: "Arm or leg that won’t stop: 5–7 cm above the wound, not on a joint, twisted tight." },
    { word: "Time", line: "Note when it went on. Call {n}. Keep them lying down and warm." },
  ],
  also: [
    "<b>Something stuck in the wound?</b> Leave it in — it may be plugging the hole. Press around it, not on it.",
  ],
};
