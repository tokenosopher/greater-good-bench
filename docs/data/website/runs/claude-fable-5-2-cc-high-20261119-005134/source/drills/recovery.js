// Drill 05 — out cold but breathing. The recovery position, and what not to do in a seizure.
import { s, ring, ease } from "../ui.js";
import { Figure, FRONT_SPEC, FRONT } from "../figure.js";
import { choiceStep } from "../drill.js";
import { sfx } from "../audio.js";

const SCALE = 2;
const OX = 168;
const OY = 236;
/** Figure coordinates → stage coordinates (the figure lies head-left, near side towards you). */
const at = ([x, y]) => [OX + y * SCALE, OY - x * SCALE];

const P1 = { elL: [-50, 8], haL: [-54, -26] };
const P2 = { elR: [6, 30], haR: [-13, -9] };
const P3 = { knR: [19, 108], ftR: [17, 132] };
const P4 = {
  head: [-5, -30],
  shL: [-15, 5],
  shR: [-3, 3],
  hipL: [-15, 78],
  hipR: [-5, 78],
  elL: [-50, 10],
  haL: [-54, -24],
  elR: [-30, 22],
  haR: [-15, -15],
  knR: [-50, 80],
  ftR: [-53, 124],
  knL: [-14, 126],
  ftL: [-12, 174],
};
const P5 = { head: [-1, -35] };

function roll(ctx) {
  const { sc } = ctx;
  const svg = ctx.svg("A person lying on their back, seen from above. You kneel at the bottom of the picture.");
  svg.append(s("ellipse", { class: "floor", cx: 300, cy: 250, rx: 282, ry: 150 }));
  const g = s("g", { transform: `translate(${OX} ${OY}) rotate(-90) scale(${SCALE})` });
  const fig = new Figure(FRONT_SPEC, FRONT);
  g.append(fig.el);
  svg.append(g);

  // You, kneeling beside them.
  svg.append(
    s("path", { class: "you-line", d: "M150 430 H450" }),
    s("path", { class: "you-top", d: "M300 408 l13 18 h-26 z" }),
    s("text", { class: "you-label", x: 300, y: 462, "text-anchor": "middle" }, "YOU KNEEL HERE")
  );

  // Calm, regular breathing — the opposite of the gasps in drill 01.
  const breath = s(
    "g",
    { class: "gasp breath" },
    s("path", { d: "M70 214 q-14 -8 -26 -3" }),
    s("path", { d: "M64 240 h-28" }),
    s("path", { d: "M70 266 q-14 8 -26 3" })
  );
  svg.append(breath);
  const torso = fig.nodes[2].p;
  sc.frame((dt, now) => {
    const k = (Math.sin(now / 520) + 1) / 2;
    breath.setAttribute("opacity", 0.15 + 0.6 * k);
    torso.setAttribute("stroke-width", 14 + 2.2 * k);
  });

  const stepNo = s("text", { class: "big-count", x: 560, y: 70, "text-anchor": "end" }, "1/5");
  svg.append(stepNo);

  const moves = [
    {
      point: () => fig.pose.haL,
      label: "Move the near arm out",
      title: "Near arm: out of the way.",
      text: "Kneel beside them. Take the arm nearest you and lay it out at a right angle, elbow bent, palm up.",
      to: P1,
    },
    {
      point: () => fig.pose.haR,
      label: "Bring the far hand to the near cheek",
      title: "Far hand: to their cheek.",
      text: "Bring the far arm across the chest and hold the back of that hand against the cheek nearest you. It will cushion the head.",
      to: P2,
    },
    {
      point: () => fig.pose.knR,
      label: "Pull the far knee up",
      title: "Far knee: up.",
      text: "With your other hand, pull the far knee up until the foot is flat on the floor. That bent leg is your lever.",
      to: P3,
    },
    {
      point: () => fig.pose.knR,
      label: "Pull the knee to roll them towards you",
      title: "Pull the knee. Roll them to you.",
      text: "Keep their hand pressed to their cheek and pull on the raised knee. They roll onto their side — it takes far less strength than you’d think.",
      to: P4,
      ms: 900,
    },
    {
      point: () => fig.pose.head,
      label: "Tilt the head back",
      title: "Head back. Mouth down.",
      text: "Gently tilt the head back to open the airway, with the mouth angled toward the floor so anything in it drains out.",
      to: P5,
    },
  ];

  let i = 0;
  let current = null;
  function arm() {
    const m = moves[i];
    stepNo.textContent = `${i + 1}/5`;
    ctx.prompt(m.title, m.text);
    const [x, y] = at(m.point());
    current = ring(x, y, 22, m.label, async () => {
      current.remove();
      sfx.tap();
      await fig.to(m.to, m.ms || 550, sc, ease.inOut);
      i++;
      if (i < moves.length) arm();
      else finish();
    });
    svg.append(current);
    if (i > 0) current.focus({ preventScroll: true });
  }
  arm();
  ctx.say("Tap the glowing spot to make each move.", "info");

  function finish() {
    ctx.done(
      "On their back, the tongue or vomit can silently block the airway. On their side, it can’t. Call {n}, <b>keep watching the breathing</b>, and if it stops, roll them back and start CPR."
    );
  }
}

export default {
  id: "recovery",
  num: "05",
  name: "Out cold",
  blurb: "Unresponsive, but breathing. Five moves that keep an airway open.",
  minutes: 2,
  steps: [
    {
      tag: "Roll",
      title: "Near arm: out of the way.",
      text: "",
      setup: roll,
    },
    choiceStep({
      tag: "Seizure",
      title: "They start to shake.",
      text: "A different day. Someone drops to the floor, rigid, then jerking. Their eyes are open but nobody’s home.",
      scene: "On a station platform",
      quote: "A stranger is on the ground, convulsing. Someone shouts: “Hold him down! Put a wallet between his teeth, he’ll swallow his tongue!”",
      options: [
        { label: "Hold them still so they don’t hurt themselves", why: "Restraining a seizure injures both of you and doesn’t shorten it. Let it run." },
        { label: "Put something soft between their teeth", why: "Never put anything in the mouth. Nobody can swallow their tongue — but they can break teeth or bite through your fingers." },
        {
          label: "Clear space, cushion the head, time it",
          ok: true,
          why: "Yes. Move hard things away, put something soft under the head, and <b>check the time</b>. When the jerking stops, roll them into the recovery position. Call {n} if it lasts over 5 minutes, repeats, it’s their first, or they don’t come round.",
        },
      ],
    }),
  ],
  keepTitle: "Breathing? On their side.",
  keep: [
    { word: "Breathing", line: "Unresponsive but breathing normally: don’t leave them on their back." },
    { word: "Roll", line: "Near arm out. Far hand to cheek. Far knee up. Pull the knee towards you." },
    { word: "Airway", line: "Head tilted back, mouth angled down. Call {n}. Watch every breath." },
    { word: "Seizure", line: "Don’t restrain. Nothing in the mouth. Cushion, time it, then roll." },
  ],
  also: [
    "This is also what to do for someone dangerously drunk, overdosed, or who has fainted and isn’t waking. <b>If breathing stops, it’s drill 01.</b>",
  ],
};
