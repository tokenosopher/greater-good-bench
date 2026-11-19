// Drill 06 — ten things "everybody knows". Seven of them get people killed.
import { h, scope, scrollToEl } from "../ui.js";
import { fill } from "../drill.js";
import { sfx, wake } from "../audio.js";
import { state } from "../state.js";

const CLAIMS = [
  {
    claim: "A drowning person shouts and waves for help.",
    truth: false,
    why: "Drowning is <b>quiet</b>. They can’t shout — they can’t even breathe. Look for a head low in the water, mouth at the surface, body upright, no kicking, no sound.",
    act: "Reach with something or throw something that floats. Don’t jump in unless you’re trained.",
    word: "Drowning",
  },
  {
    claim: "Put butter, toothpaste or ice on a burn.",
    truth: false,
    why: "Grease traps the heat in. Ice damages the skin further.",
    act: "Cool running water for <b>20 minutes</b>. Then cover loosely with cling film or a clean cloth.",
    word: "Burn",
  },
  {
    claim: "Anyone can use a defibrillator, with no training at all.",
    truth: true,
    why: "An AED speaks its instructions aloud and decides for itself whether to shock. It will not shock a heart that doesn’t need it.",
    act: "Find out today where the nearest one is to your home and your work.",
    word: "AED",
  },
  {
    claim: "If you’re not sure someone needs CPR, it’s safer to wait.",
    truth: false,
    why: "Someone unresponsive and not breathing normally is dying. Serious harm from CPR on a person who turned out not to need it is very rare. Waiting is what kills.",
    act: "If in doubt, push.",
    word: "Doubt",
  },
  {
    claim: "A heart attack always feels like crushing chest pain.",
    truth: false,
    why: "It can be pressure or tightness, pain in the arm, jaw or back, breathlessness, nausea, a cold sweat, or sudden exhaustion — more often so in women.",
    act: "Call {n}. Sit them down and keep them still. If they’re not allergic, have them chew one regular aspirin.",
    word: "Heart attack",
  },
  {
    claim: "For an adult who suddenly collapses, pushing on the chest without mouth-to-mouth still works.",
    truth: true,
    why: "In the first minutes their blood still carries oxygen; it just isn’t moving. Hands-only CPR moves it.",
    act: "Don’t let mouth-to-mouth put you off. Push. (Children and drowning victims need breaths too, if you can.)",
    word: "Hands only",
  },
  {
    claim: "Nosebleed? Tilt the head back.",
    truth: false,
    why: "That sends blood down the throat and into the stomach.",
    act: "Lean <b>forward</b>. Pinch the soft part of the nose for 10 minutes without letting go.",
    word: "Nosebleed",
  },
  {
    claim: "If someone swallows something poisonous, make them vomit.",
    truth: false,
    why: "Coming back up, it can burn the throat a second time or end up in the lungs.",
    act: "Call {n} or a poison centre. Keep the bottle or packet to show them.",
    word: "Poison",
  },
  {
    claim: "Someone who is very hot, confused and has stopped sweating needs cooling immediately — even with cold water or ice.",
    truth: true,
    why: "That is heatstroke, and it cooks the brain. Fast cooling is the treatment; minutes matter.",
    act: "Call {n}. Shade. Strip off layers. Soak them, fan them, pack ice at neck, armpits and groin.",
    word: "Heatstroke",
  },
  {
    claim: "Snakebite: cut the wound and suck out the venom.",
    truth: false,
    why: "It removes almost no venom and adds a second injury. Tight tourniquets and ice make it worse too.",
    act: "Keep them still and calm, keep the limb still, and get to a hospital fast.",
    word: "Snakebite",
  },
];

export function runMyths({ onExit, onFinish, nextLabel }) {
  const sc = scope();
  let i = 0;
  let score = 0;
  let answered = false;

  const progress = h("p", { class: "myth-progress" });
  const head = h(
    "header",
    { class: "drill-head" },
    h("div", { class: "drill-id" }, h("span", { class: "drill-num" }, "06"), h("span", { class: "drill-name" }, "Ten myths")),
    progress,
    h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => exit() }, "All drills")
  );
  const body = h("div", { class: "myth-body" });
  const root = h("section", { class: "drill drill--myths", "data-drill": "myths" }, head, body);

  function exit(to) {
    sc.end();
    onExit(to);
  }

  function show() {
    answered = false;
    const c = CLAIMS[i];
    progress.textContent = `${i + 1} / ${CLAIMS.length} · ${score} right`;
    const stamp = h("div", { class: "stamp-mark", "aria-hidden": "true" });
    const claim = h("h2", { class: "myth-claim", tabindex: "-1" }, "“" + c.claim + "”");
    const mythBtn = h("button", { class: "btn btn-verdict btn-myth", type: "button" }, h("span", {}, "Myth"), h("kbd", {}, "M"));
    const trueBtn = h("button", { class: "btn btn-verdict btn-true", type: "button" }, h("span", {}, "True"), h("kbd", {}, "T"));
    const reveal = h("div", { class: "myth-reveal", role: "status", "aria-live": "polite" });
    const card = h(
      "div",
      { class: "myth-card" },
      h("p", { class: "step-kicker" }, `Claim ${i + 1} of ${CLAIMS.length}`),
      h("div", { class: "myth-claim-wrap" }, claim, stamp),
      h("div", { class: "myth-buttons" }, mythBtn, trueBtn),
      reveal
    );

    const answer = (guess) => {
      if (answered) return;
      answered = true;
      wake();
      const right = guess === c.truth;
      if (right) score++;
      right ? sfx.good() : sfx.bad();
      progress.textContent = `${i + 1} / ${CLAIMS.length} · ${score} right`;
      stamp.textContent = c.truth ? "True" : "Myth";
      stamp.className = "stamp-mark is-on " + (c.truth ? "is-true" : "is-myth");
      card.classList.add("is-answered", right ? "is-right" : "is-wrong");
      mythBtn.disabled = trueBtn.disabled = true;
      (guess ? trueBtn : mythBtn).classList.add("is-picked");
      const nextBtn = h(
        "button",
        { class: "btn btn-primary is-ready", type: "button", onclick: () => advance() },
        i === CLAIMS.length - 1 ? "See your score" : "Next claim"
      );
      reveal.replaceChildren(
        h("p", { class: "myth-result " + (right ? "is-right" : "is-wrong") }, right ? "You’re right." : c.truth ? "Actually, it’s true." : "Actually, that’s a myth."),
        h("p", { class: "myth-why", html: fill(c.why) }),
        h("p", { class: "myth-act" }, h("span", { class: "myth-act-label" }, "Do this"), h("span", { html: fill(c.act) })),
        nextBtn
      );
      nextBtn.focus({ preventScroll: true });
    };
    mythBtn.onclick = () => answer(false);
    trueBtn.onclick = () => answer(true);
    body.replaceChildren(card);
    if (i > 0) claim.focus({ preventScroll: true });
    scrollToEl(root);
    current = answer;
  }

  let current = null;
  sc.on(window, "keydown", (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (!answered && current) {
      if (k === "m" || k === "arrowleft") current(false);
      if (k === "t" || k === "arrowright") current(true);
    }
  });

  function advance() {
    i++;
    if (i < CLAIMS.length) show();
    else finish();
  }

  function finish() {
    current = null;
    state.results.myths = score;
    progress.textContent = `${score} / ${CLAIMS.length} right`;
    sfx.win();
    onFinish();
    const verdict =
      score === 10
        ? "Flawless. You’d be the calmest person in the room."
        : score >= 7
          ? "Most people score lower. The ones you missed are the ones worth rereading."
          : "That’s normal — these myths are everywhere. Now you know better than most.";
    const card = h(
      "div",
      { class: "keep" },
      h("p", { class: "keep-kicker" }, "06 · Ten myths · done"),
      h("h2", { class: "keep-title", tabindex: "-1" }, `${score} out of ten.`),
      h("p", { class: "keep-lede" }, verdict),
      h(
        "ol",
        { class: "keep-list keep-list--dense" },
        CLAIMS.map((c, n) => h("li", { style: `--i:${n}` }, h("span", { class: "keep-word" }, c.word), h("span", { class: "keep-line", html: fill(c.act) })))
      ),
      h(
        "div",
        { class: "keep-actions" },
        h("button", { class: "btn btn-primary", type: "button", onclick: () => exit("next") }, nextLabel()),
        h(
          "button",
          {
            class: "btn btn-ghost",
            type: "button",
            onclick: () => {
              i = 0;
              score = 0;
              show();
            },
          },
          "Do it again"
        ),
        h("button", { class: "btn-link", type: "button", onclick: () => exit() }, "All drills")
      )
    );
    body.replaceChildren(card);
    card.querySelector(".keep-title").focus({ preventScroll: true });
    scrollToEl(root);
  }

  show();
  return { el: root, destroy: () => sc.end() };
}

export default {
  id: "myths",
  num: "06",
  name: "Ten myths",
  blurb: "Burns, drowning, poison, heat. What “everybody knows” — and what’s true.",
  minutes: 2,
  custom: runMyths,
};
