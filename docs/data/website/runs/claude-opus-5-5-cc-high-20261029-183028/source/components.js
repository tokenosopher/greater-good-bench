import { h, shuffle, shake } from "./dom.js";

// Multiple-choice questions, one at a time. Wrong answers explain and allow retry.
export function quiz(questions, onDone) {
  const root = h("div", { class: "quiz" });
  let index = 0;

  function show() {
    const q = questions[index];
    const feedback = h("p", { class: "feedback", "aria-live": "polite" });
    const opts = h("div", { class: "options" });
    let solved = false;
    for (const opt of shuffle(q.options)) {
      const btn = h("button", { class: "option", type: "button" }, opt.t);
      btn.addEventListener("click", () => {
        if (solved) return;
        feedback.textContent = opt.why || (opt.correct ? "Right." : "Not quite — try again.");
        feedback.className = "feedback " + (opt.correct ? "good" : "bad");
        if (opt.correct) {
          solved = true;
          btn.classList.add("right");
          opts.classList.add("solved");
          const last = index === questions.length - 1;
          feedback.append(
            h("button", {
              class: "btn small next", type: "button",
              onClick: () => { if (last) finish(); else { index++; show(); } },
            }, last ? "Finish ✓" : "Next question →")
          );
        } else {
          btn.classList.add("wrong");
          btn.disabled = true;
          shake(btn);
        }
      });
      opts.append(btn);
    }
    root.replaceChildren(
      h("p", { class: "q-count" }, `Question ${index + 1} of ${questions.length}`),
      h("p", { class: "q" }, q.q),
      opts,
      feedback
    );
  }

  function finish() {
    root.replaceChildren(h("p", { class: "feedback good big" }, "✓ All correct. You've got this one."));
    onDone();
  }

  show();
  return root;
}

// Sort each item into one of two bins (e.g. Do / Don't).
export function sorter({ items, labels = ["Do", "Don't"] }, onDone) {
  const root = h("div", { class: "sorter" });
  let remaining = items.length;
  for (const item of shuffle(items)) {
    const why = h("p", { class: "why", "aria-live": "polite" });
    const row = h("div", { class: "sort-row" });
    const btns = labels.map((label, i) => {
      const b = h("button", { class: "chip " + (i === 0 ? "yes" : "no"), type: "button" }, label);
      b.addEventListener("click", () => {
        if (row.classList.contains("done")) return;
        const correct = (i === 0) === item.ok;
        why.textContent = item.why;
        if (correct) {
          row.classList.add("done", item.ok ? "is-yes" : "is-no");
          b.classList.add("picked");
          why.className = "why good";
          if (--remaining === 0) onDone();
        } else {
          why.className = "why bad";
          shake(row);
        }
      });
      return b;
    });
    row.append(h("span", { class: "sort-label" }, item.t), h("span", { class: "sort-btns" }, btns), why);
    root.append(row);
  }
  return root;
}

// Put steps in the right order by tapping them in sequence.
export function sequence(steps, onDone) {
  const placed = h("ol", { class: "seq-placed" });
  const pool = h("div", { class: "seq-pool" });
  const hint = h("p", { class: "feedback", "aria-live": "polite" }, "Tap the first step.");
  let next = 0;
  for (const i of shuffle(steps.map((_, i) => i))) {
    const b = h("button", { class: "seq-chip", type: "button" }, steps[i]);
    b.addEventListener("click", () => {
      if (i === next) {
        b.remove();
        placed.append(h("li", null, steps[i]));
        next++;
        if (next === steps.length) {
          hint.textContent = "✓ That's the order. Practice it in your head once more.";
          hint.className = "feedback good";
          onDone();
        } else {
          hint.textContent = "Good. What comes next?";
          hint.className = "feedback";
        }
      } else {
        hint.textContent = "Not yet — what has to happen before that?";
        hint.className = "feedback bad";
        shake(b);
      }
    });
    pool.append(b);
  }
  return h("div", { class: "sequence" }, placed, pool, hint);
}

// A chat where you choose what to say.
export function dialogue(turns, ending, onDone) {
  const thread = h("div", { class: "thread", "aria-live": "polite" });
  const choices = h("div", { class: "choices" });
  const feedback = h("p", { class: "feedback" });
  let t = 0;

  function bubble(text, who) {
    thread.append(h("div", { class: "bubble " + who }, text));
  }

  function step() {
    const turn = turns[t];
    bubble(turn.them, "them");
    choices.replaceChildren();
    for (const c of shuffle(turn.choices)) {
      const b = h("button", { class: "option", type: "button" }, c.t);
      b.addEventListener("click", () => {
        if (c.correct) {
          bubble(c.t, "me");
          feedback.textContent = c.why;
          feedback.className = "feedback good";
          t++;
          if (t < turns.length) setTimeout(step, 450);
          else {
            choices.replaceChildren();
            setTimeout(() => { bubble(ending, "them"); onDone(); }, 450);
          }
          choices.replaceChildren();
        } else {
          feedback.textContent = c.why;
          feedback.className = "feedback bad";
          b.disabled = true;
          b.classList.add("wrong");
          shake(b);
        }
      });
      choices.append(b);
    }
  }

  step();
  return h("div", { class: "dialogue" }, thread, choices, feedback);
}
