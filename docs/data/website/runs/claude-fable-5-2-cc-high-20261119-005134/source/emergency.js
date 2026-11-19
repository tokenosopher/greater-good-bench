// Emergency mode: no teaching, no animation to wait for. Big words, in order, and a beat to push to.
import { h, scope, mmss } from "./ui.js";
import { fill } from "./drill.js";
import { metronome, wake } from "./audio.js";
import { state, num } from "./state.js";

const SITUATIONS = [
  {
    id: "cpr",
    name: "Not responding, not breathing",
    hint: "Collapsed. No normal breathing, or only gasping.",
    beat: true,
    steps: [
      "<b>Call {n}.</b> Speaker on. Send someone for an <b>AED</b>.",
      "Lay them flat on their back on the floor. Kneel beside the chest.",
      "Heel of your hand on the <b>centre of the chest</b>, other hand on top. Arms straight.",
      "<b>Push hard and fast</b> on every beat. 5–6 cm down. Let the chest come all the way back up.",
      "AED arrives: switch it on and <b>do what it says</b>.",
      "<b>Don’t stop</b> until help takes over or they start breathing normally.",
    ],
    notes: [
      "<b>Child, baby, or pulled from water:</b> if you can, give 2 breaths after every 30 pushes. One hand for a child, two fingers for a baby; press down a third of the chest.",
    ],
  },
  {
    id: "choking",
    name: "Choking",
    hint: "Can’t cough, can’t speak, can’t breathe.",
    steps: [
      "Coughing loudly? Tell them: <b>keep coughing</b>. Don’t hit their back yet.",
      "Silent or can’t breathe: <b>lean them forward</b>. Give <b>5 hard blows</b> between the shoulder blades with the heel of your hand.",
      "Still stuck: stand behind. Fist just above the navel. <b>5 sharp thrusts, in and up.</b>",
      "<b>Repeat 5 blows, 5 thrusts.</b> Get someone to call {n}.",
      "They go limp: lower them to the floor and start CPR.",
    ],
    notes: [
      "<b>Baby under 1:</b> face-down along your forearm, head low. 5 back blows. Turn over: 5 chest thrusts with two fingers. No abdominal thrusts.",
      "<b>Pregnant or very large:</b> thrust on the breastbone instead of the belly.",
    ],
    link: { to: "cpr", label: "They’ve gone limp → CPR" },
  },
  {
    id: "bleeding",
    name: "Bleeding heavily",
    hint: "Blood spurting, pooling or soaking through.",
    steps: [
      "<b>Press hard, directly on the wound.</b> Any cloth, or your bare hands. Lean your weight in.",
      "<b>Call {n}</b> — or have someone else call while you press.",
      "<b>Don’t lift to look.</b> Soaked through? Put more on top and press harder.",
      "Arm or leg that won’t stop: <b>tourniquet 5–7 cm above the wound</b>, not on a joint. Twist until the bleeding stops. Note the time.",
      "Lay them down. Keep them warm. Keep pressing until help takes over.",
    ],
    notes: ["<b>Object stuck in the wound:</b> leave it in. Press around it."],
  },
  {
    id: "stroke",
    name: "Stroke signs",
    hint: "Face drooping, arm weak, speech strange.",
    steps: [
      "<b>Face:</b> ask them to smile. Does one side droop?",
      "<b>Arms:</b> ask them to raise both. Does one drift down?",
      "<b>Speech:</b> ask for a simple sentence. Slurred or jumbled?",
      "<b>Any one sign: call {n} now.</b> Say “stroke”.",
      "<b>Note the time</b> the symptoms started. Tell the crew.",
      "No food, no drink, no medicine. Stay with them — even if it passes.",
    ],
  },
  {
    id: "heart",
    name: "Chest pain",
    hint: "Possible heart attack. Awake and talking.",
    steps: [
      "<b>Call {n}.</b> Say “suspected heart attack”.",
      "<b>Sit them down</b>, leaning back against something, knees bent. No walking about.",
      "Not allergic to aspirin? Have them <b>chew one regular aspirin</b> (about 300 mg).",
      "Loosen tight clothing. Keep them calm and still. Send someone to find an AED, just in case.",
      "If they collapse and stop breathing normally: start CPR.",
    ],
    notes: ["Signs can be quiet: pressure or tightness, pain in the arm, jaw or back, breathlessness, nausea, cold sweat."],
    link: { to: "cpr", label: "They’ve collapsed → CPR" },
  },
  {
    id: "recovery",
    name: "Unconscious but breathing",
    hint: "Won’t wake up. Breathing normally.",
    steps: [
      "<b>Call {n}.</b>",
      "Kneel beside them. <b>Near arm</b> out at a right angle.",
      "<b>Far hand</b> across, back of it against their near cheek. Hold it there.",
      "<b>Far knee</b> up, foot flat. Pull the knee towards you to roll them onto their side.",
      "<b>Tilt the head back.</b> Mouth angled toward the floor.",
      "<b>Watch the breathing.</b> If it stops: onto their back, start CPR.",
    ],
    link: { to: "cpr", label: "Breathing has stopped → CPR" },
  },
  {
    id: "seizure",
    name: "Seizure",
    hint: "On the ground, stiff or jerking.",
    steps: [
      "<b>Don’t hold them down.</b> Put nothing in the mouth.",
      "Move hard and sharp things away. <b>Cushion the head.</b>",
      "<b>Time it.</b> Loosen anything tight at the neck.",
      "When the jerking stops: roll them onto their side and stay with them.",
      "<b>Call {n}</b> if it lasts over 5 minutes, happens again, it’s their first, they’re hurt or pregnant, or they don’t come round.",
    ],
  },
  {
    id: "burn",
    name: "Burn",
    hint: "Heat, steam, chemical or electrical.",
    steps: [
      "<b>Cool running water for 20 minutes.</b> Cool, not icy. Start now.",
      "Take off rings, watches and clothing near the burn — unless it’s stuck to the skin.",
      "Cover loosely with <b>cling film</b> or a clean, non-fluffy cloth.",
      "<b>No ice, butter, creams or toothpaste.</b> Don’t pop blisters.",
      "<b>Call {n}</b> if it’s bigger than their hand, deep, on the face, hands or genitals, chemical or electrical, or it’s a child.",
    ],
  },
];

export function runEmergency({ onExit }) {
  const sc = scope();
  let pageScope = null;
  wake();

  // Keep the screen on if the browser allows it.
  let lock = null;
  try {
    navigator.wakeLock
      ?.request("screen")
      .then((l) => (lock = l))
      .catch(() => {});
  } catch (e) {
    /* optional */
  }
  sc.add(() => {
    try {
      lock?.release();
    } catch (e) {
      /* optional */
    }
    try {
      window.speechSynthesis?.cancel();
    } catch (e) {
      /* optional */
    }
  });

  const callBar = () =>
    h(
      "a",
      { class: "em-call", href: "tel:" + num().replace(/\D/g, ""), "aria-label": "Call " + num() },
      h("span", { class: "em-call-label" }, "Call"),
      h("span", { class: "em-call-num" }, num()),
      h("span", { class: "em-call-note" }, "Speaker on. Stay on the line.")
    );

  const main = h("div", { class: "em-main" });
  const backBtn = h("button", { class: "btn btn-em-ghost btn-small", type: "button" }, "Exit");
  const top = h("header", { class: "em-top" }, h("div", { class: "em-title" }, h("span", { class: "em-dot" }), "Emergency"), backBtn);
  const root = h("section", { class: "em" }, top, main);

  function list() {
    pageScope?.end();
    pageScope = null;
    backBtn.textContent = "Exit to training";
    backBtn.onclick = () => {
      sc.end();
      onExit();
    };
    main.replaceChildren(
      callBar(),
      h("h1", { class: "em-h", tabindex: "-1" }, "What is happening?"),
      h(
        "div",
        { class: "em-grid" },
        SITUATIONS.map((sit, i) =>
          h(
            "button",
            { class: "em-tile", type: "button", onclick: () => open(sit.id) },
            h("span", { class: "em-tile-n" }, String(i + 1)),
            h("span", { class: "em-tile-name" }, sit.name),
            h("span", { class: "em-tile-hint" }, sit.hint)
          )
        )
      ),
      h("p", { class: "em-foot" }, "Not sure? Call anyway. The call-taker will tell you what to do.")
    );
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  function open(id) {
    pageScope?.end();
    pageScope = scope();
    const ps = pageScope;
    const sit = SITUATIONS.find((x) => x.id === id);
    backBtn.textContent = "← All situations";
    backBtn.onclick = list;

    const extras = [];
    if (sit.beat) extras.push(beatBox(ps));

    const speakBtn = canSpeak()
      ? h(
          "button",
          {
            class: "btn btn-em-ghost btn-small",
            type: "button",
            onclick: () => speak(sit),
          },
          "Read steps aloud"
        )
      : null;

    const parts = [
      callBar(),
      h("div", { class: "em-page-head" }, h("h1", { class: "em-h", tabindex: "-1" }, sit.name), speakBtn),
      h("div", { class: "em-cols" + (sit.beat ? " has-beat" : "") }, h("ol", { class: "em-steps" }, sit.steps.map((st) => h("li", {}, h("span", { html: fill(st) })))), extras),
      sit.notes ? h("div", { class: "em-notes" }, sit.notes.map((n) => h("p", { html: fill(n) }))) : null,
      sit.link ? h("button", { class: "btn btn-em-red", type: "button", onclick: () => open(sit.link.to) }, sit.link.label) : null,
    ];
    main.replaceChildren(...parts.filter(Boolean));
    main.querySelector(".em-h").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
    ps.add(() => {
      try {
        window.speechSynthesis?.cancel();
      } catch (e) {
        /* optional */
      }
    });
  }

  function beatBox(ps) {
    const count = h("span", { class: "beat-count" }, "1");
    const disc = h("div", { class: "beat-disc" }, count);
    const clock = h("b", {}, "0:00");
    const banner = h("p", { class: "beat-banner" }, "Push on every beat");
    const toggle = h("button", { class: "btn btn-em-ghost btn-small", type: "button" }, "Pause beat");
    const box = h(
      "div",
      { class: "beat-box" },
      disc,
      h("p", { class: "beat-clock" }, clock, h("span", {}, " of CPR · 110 a minute")),
      banner,
      toggle
    );
    const startAt = performance.now();
    const metro = metronome({
      bpm: 110,
      accentEvery: 30,
      audible: () => state.sound,
      onBeat: (n) => {
        count.textContent = String((n % 30) + 1);
        disc.classList.remove("is-beat");
        void disc.offsetWidth;
        disc.classList.add("is-beat");
      },
    });
    metro.start();
    ps.add(() => metro.stop());
    toggle.onclick = () => {
      if (metro.running) {
        metro.stop();
        toggle.textContent = "Resume beat";
      } else {
        wake();
        metro.start();
        toggle.textContent = "Pause beat";
      }
    };
    ps.interval(() => {
      const sec = (performance.now() - startAt) / 1000;
      clock.textContent = mmss(sec);
      const inCycle = sec % 120;
      if (sec > 110 && (inCycle > 110 || inCycle < 10)) {
        banner.textContent = "2 minutes — swap pusher if you can";
        banner.classList.add("is-alert");
      } else {
        banner.textContent = "Push on every beat";
        banner.classList.remove("is-alert");
      }
    }, 250);
    return box;
  }

  function canSpeak() {
    try {
      return typeof window.speechSynthesis?.speak === "function" && typeof window.SpeechSynthesisUtterance === "function";
    } catch (e) {
      return false;
    }
  }

  function speak(sit) {
    try {
      const synth = window.speechSynthesis;
      synth.cancel();
      const strip = (html) => fill(html).replace(/<[^>]+>/g, "").replace(/→/g, ", then ");
      sit.steps.forEach((st, i) => {
        const u = new SpeechSynthesisUtterance(`Step ${i + 1}. ${strip(st)}`);
        u.rate = 0.95;
        synth.speak(u);
      });
    } catch (e) {
      /* optional */
    }
  }

  list();
  return {
    el: root,
    destroy: () => {
      pageScope?.end();
      sc.end();
    },
  };
}
