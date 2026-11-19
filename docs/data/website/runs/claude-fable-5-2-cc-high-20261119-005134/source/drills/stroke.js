// Drill 04 — stroke. Face, Arms, Speech, Time.
import { h, s, lerp, ease } from "../ui.js";
import { choiceStep, fill } from "../drill.js";
import { sfx } from "../audio.js";

function fastTest(ctx) {
  const { sc, stage } = ctx;
  const svg = ctx.svg("A person facing you, head and shoulders");

  // Bust
  const armL = s("path", { class: "fig-limb", "stroke-width": 40 });
  const armR = s("path", { class: "fig-limb", "stroke-width": 40 });
  const body = s("path", { class: "fig-body", "stroke-width": 44, d: "M214 338 H386 L372 540 H228 Z" });
  const neck = s("path", { class: "fig-limb", "stroke-width": 52, d: "M300 262 V316" });
  const head = s("circle", { class: "fig-head", cx: 300, cy: 178, r: 96 });
  const eyeL = s("ellipse", { class: "face", cx: 264, cy: 160, rx: 9, ry: 11 });
  const eyeR = s("ellipse", { class: "face", cx: 336, cy: 160, rx: 9, ry: 11 });
  const browL = s("path", { class: "face-line", d: "M248 136 L280 132" });
  const browR = s("path", { class: "face-line" });
  const mouth = s("path", { class: "face-line face-mouth" });
  svg.append(s("g", { class: "fig" }, armL, armR, body, neck, head), eyeL, eyeR, browL, browR, mouth);

  const bubble = s(
    "g",
    { class: "bubble", opacity: 0 },
    s("path", { d: "M398 40 h170 a14 14 0 0 1 14 14 v62 a14 14 0 0 1 -14 14 h-120 l-34 26 l8 -26 h-24 a14 14 0 0 1 -14 -14 v-62 a14 14 0 0 1 14 -14 z" }),
    s("text", { x: 404, y: 80 }, ""),
    s("text", { x: 404, y: 110 }, "")
  );
  svg.append(bubble);

  const face = { smile: 0, droop: 0 };
  const arms = { l: 0, r: 0, drift: 0 };
  function draw() {
    const sm = face.smile;
    const d = face.droop * (0.3 + 0.7 * sm);
    const Lx = 256 - 6 * sm;
    const Ly = 226 - 14 * sm;
    const Rx = 344 + 6 * sm * (1 - d) - 4 * d;
    const Ry = 226 - 14 * sm * (1 - d) + 26 * d;
    const Cx = 300 - 10 * d;
    const Cy = 232 + 30 * sm - 6 * d;
    mouth.setAttribute("d", `M${Lx} ${Ly} Q${Cx} ${Cy} ${Rx} ${Ry}`);
    eyeR.setAttribute("ry", 11 - 6 * d);
    eyeR.setAttribute("cy", 160 + 5 * d);
    browR.setAttribute("d", `M320 ${132 + 7 * d} L352 ${136 + 13 * d}`);
    // Arms: 0 = hanging, 1 = held out.
    const a = (side, up, drift) => {
      const sx = 300 + side * 88;
      const downE = [300 + side * 120, 440];
      const downH = [300 + side * 124, 560];
      const upE = [300 + side * 166, 300];
      const upH = [300 + side * 246, 252];
      const driftE = [300 + side * 158, 388];
      const driftH = [300 + side * 214, 470];
      let E = [lerp(downE[0], upE[0], up), lerp(downE[1], upE[1], up)];
      let H = [lerp(downH[0], upH[0], up), lerp(downH[1], upH[1], up)];
      E = [lerp(E[0], driftE[0], drift), lerp(E[1], driftE[1], drift)];
      H = [lerp(H[0], driftH[0], drift), lerp(H[1], driftH[1], drift)];
      return `M${sx} 340 L${E[0]} ${E[1]} L${H[0]} ${H[1]}`;
    };
    armL.setAttribute("d", a(-1, arms.l, 0));
    armR.setAttribute("d", a(1, arms.r, arms.drift));
  }
  draw();

  // The four letters, lighting up as each test is run.
  const cells = [
    ["F", "Face", "One side droops"],
    ["A", "Arms", "One drifts down"],
    ["S", "Speech", "Slurred or strange"],
    ["T", "Time", "Call {n} now"],
  ].map(([letter, wordText, finding]) => {
    const el = h(
      "div",
      { class: "fast-cell" },
      h("span", { class: "fast-letter" }, letter),
      h("span", { class: "fast-word" }, wordText),
      h("span", { class: "fast-find" }, fill(finding))
    );
    return el;
  });
  stage.append(h("div", { class: "fast" }, cells));

  let doneCount = 0;
  const light = (i) => {
    cells[i].classList.add("is-on");
    sfx.tap();
    doneCount++;
    if (doneCount === 3) {
      sc.timeout(() => {
        cells[3].classList.add("is-on", "is-time");
        ctx.done(
          "<b>Any one of those signs is enough.</b> Call {n}, say “stroke”, and note the time the symptoms started — the treatments that reverse a stroke only work in the first few hours. Every minute untreated costs about two million brain cells."
        );
      }, 900);
    }
  };

  const tests = [
    {
      label: "“Can you smile for me?”",
      run: async (b) => {
        face.droop = 1;
        await sc.tween(900, (t) => ((face.smile = t), draw()), ease.inOut);
        ctx.say("One side of the mouth doesn’t lift, and that eyelid sags. That’s <b>F — Face</b>.", "info");
        light(0);
      },
    },
    {
      label: "“Raise both arms and hold them.”",
      run: async () => {
        await sc.tween(700, (t) => ((arms.l = t), (arms.r = t), draw()), ease.inOut);
        await sc.wait(500);
        await sc.tween(1500, (t) => ((arms.drift = t), draw()), ease.inOut);
        ctx.say("One arm sinks and they can’t stop it. That’s <b>A — Arms</b>.", "info");
        light(1);
      },
    },
    {
      label: "“Say: the sky is blue today.”",
      run: async () => {
        bubble.setAttribute("opacity", 1);
        const lines = ["Th’ ssky… izz", "boo… t’ddday…"];
        const [t1, t2] = bubble.querySelectorAll("text");
        for (const [node, line] of [
          [t1, lines[0]],
          [t2, lines[1]],
        ]) {
          for (let i = 1; i <= line.length; i++) {
            node.textContent = line.slice(0, i);
            await sc.wait(65);
          }
        }
        ctx.say("Slurred, jumbled, or they can’t find the words. That’s <b>S — Speech</b>.", "info");
        light(2);
      },
    },
  ];

  let busy = false;
  const buttons = tests.map((t) => {
    const b = h("button", { class: "btn btn-choice", type: "button" }, t.label);
    b.onclick = async () => {
      if (busy) return;
      busy = true;
      b.disabled = true;
      b.classList.add("is-right");
      await t.run(b);
      busy = false;
    };
    return b;
  });
  ctx.actions.append(...buttons);
  ctx.say("Ask all three. Watch closely.", "info");
}

export default {
  id: "stroke",
  num: "04",
  name: "Stroke",
  blurb: "Three questions that take ten seconds, and a clock you can’t see.",
  minutes: 1,
  steps: [
    {
      tag: "Test",
      title: "Something’s off.",
      text: "Your friend stops mid-sentence and looks confused. They say they’re fine. <b>Ask them three things.</b>",
      stageClass: "stage--fast",
      setup: fastTest,
    },
    choiceStep({
      tag: "Decide",
      title: "And then it passes.",
      text: "Do you still make the call?",
      scene: "Ten minutes later",
      quote: "“Look — my arm’s fine again. I can talk. Honestly, it’s nothing. Don’t make a fuss. I’ll just lie down for a bit.”",
      options: [
        { label: "Let them rest and check on them in an hour", why: "This is how people lose the treatment window. A stroke that “passes” is often a warning: the big one tends to follow within hours or days." },
        { label: "Call {n} anyway", ok: true, why: "Yes. Symptoms that vanish are a <b>mini-stroke (TIA)</b> — an emergency in its own right. Call, and tell them exactly when it started." },
        { label: "Give them an aspirin and some water", why: "No food, no drink, no pills. Swallowing may not work properly, and aspirin makes a bleeding stroke worse. Just call." },
      ],
    }),
  ],
  keepTitle: "Face. Arms. Speech. Time.",
  keep: [
    { word: "Face", line: "Ask for a smile. Does one side droop?" },
    { word: "Arms", line: "Both arms up. Does one drift down?" },
    { word: "Speech", line: "A simple sentence. Slurred? Jumbled? Nothing?" },
    { word: "Time", line: "One sign is enough. Call {n}. Note when it started." },
  ],
  also: [
    "Also sudden: loss of vision, loss of balance, numbness on one side, or the worst headache of their life. <b>Sudden is the word.</b> Don’t give food, drink or medicine, and don’t let them talk you out of calling.",
  ],
};
