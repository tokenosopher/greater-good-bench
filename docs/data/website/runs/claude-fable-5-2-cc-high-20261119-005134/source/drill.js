// The drill engine: a stage you act on, a coach panel that tells you why, and a takeaway to keep.
import { h, s, scope, scrollToEl } from "./ui.js";
import { sfx, wake } from "./audio.js";
import { num } from "./state.js";

/** Replace {n} with the visitor's emergency number. */
export const fill = (text) => String(text).replaceAll("{n}", num());

/**
 * def = {
 *   id, num, name, blurb, minutes,
 *   steps: [{ tag, title, text, setup(ctx) }],
 *   keep: [{ word, line }],
 * }
 * ctx = { stage, svg(label), sc, say(text, kind), done(text), actions, hint(text) }
 */
export function runDrill(def, { onExit, onFinish, nextLabel }) {
  let index = 0;
  let stepScope = null;

  const pips = h("ol", { class: "drill-pips", "aria-label": "Steps" });
  const head = h(
    "header",
    { class: "drill-head" },
    h(
      "div",
      { class: "drill-id" },
      h("span", { class: "drill-num" }, def.num),
      h("span", { class: "drill-name" }, def.name)
    ),
    pips,
    h("button", { class: "btn btn-ghost btn-small", type: "button", onclick: () => exit() }, "All drills")
  );

  const stage = h("div", { class: "stage" });
  const kicker = h("p", { class: "step-kicker" });
  const title = h("h2", { class: "step-title", tabindex: "-1" });
  const text = h("p", { class: "step-text" });
  const actions = h("div", { class: "step-actions" });
  const say = h("div", { class: "step-say", role: "status", "aria-live": "polite" });
  const nextBtn = h("button", { class: "btn btn-primary btn-next", type: "button", onclick: () => next() }, "Next");
  const skipBtn = h("button", { class: "btn-link", type: "button", onclick: () => next() }, "Skip this step");
  const foot = h("div", { class: "step-foot" }, nextBtn, skipBtn);
  const panel = h("div", { class: "panel" }, kicker, title, text, actions, say, foot);
  const body = h("div", { class: "drill-body" }, stage, panel);
  const root = h("section", { class: "drill", "data-drill": def.id }, head, body);

  function exit() {
    stepScope?.end();
    onExit();
  }

  function renderPips() {
    pips.replaceChildren(
      ...def.steps.map((st, i) =>
        h(
          "li",
          { class: "pip" + (i < index ? " is-done" : i === index ? " is-now" : ""), "aria-current": i === index ? "step" : null },
          h("span", { class: "pip-n" }, String(i + 1)),
          h("span", { class: "pip-t" }, st.tag)
        )
      )
    );
  }

  function show(i) {
    stepScope?.end();
    stepScope = scope();
    index = i;
    const st = def.steps[i];
    renderPips();
    root.classList.remove("is-keep");
    stage.className = "stage" + (st.stageClass ? " " + st.stageClass : "");
    stage.replaceChildren();
    actions.replaceChildren();
    say.replaceChildren();
    say.className = "step-say";
    kicker.textContent = `Step ${i + 1} of ${def.steps.length} · ${st.tag}`;
    title.textContent = fill(st.title);
    text.innerHTML = fill(st.text);
    nextBtn.disabled = true;
    nextBtn.textContent = i === def.steps.length - 1 ? "What to remember" : "Next step";
    nextBtn.classList.remove("is-ready");
    skipBtn.hidden = false;

    const ctx = {
      stage,
      actions,
      sc: stepScope,
      /** Make the standard 600×500 stage drawing. */
      svg(label, viewBox = "0 0 600 500") {
        const el = s("svg", { class: "stage-svg", viewBox, role: "group", "aria-label": label });
        stage.append(el);
        return el;
      },
      /** Coach feedback. kind: "ok" | "no" | "info" */
      say(message, kind = "info") {
        say.className = "step-say is-" + kind;
        say.replaceChildren(
          h("span", { class: "say-mark", "aria-hidden": "true" }, kind === "ok" ? "✓" : kind === "no" ? "✕" : "→"),
          h("span", { html: fill(message) })
        );
        if (kind === "no") sfx.bad();
      },
      /** Step finished: unlock Next and explain why it matters. */
      done(message) {
        if (stepScope.dead) return;
        if (message) ctx.say(message, "ok");
        sfx.good();
        nextBtn.disabled = false;
        nextBtn.classList.add("is-ready");
        skipBtn.hidden = true;
        stage.classList.add("is-done");
      },
      /** Rewrite the instruction as the step moves on. */
      prompt(newTitle, newText) {
        if (newTitle != null) title.textContent = fill(newTitle);
        if (newText != null) text.innerHTML = fill(newText);
      },
    };
    st.setup(ctx);
    if (i > 0) title.focus({ preventScroll: true });
    scrollToEl(root);
  }

  function next() {
    wake();
    if (index < def.steps.length - 1) show(index + 1);
    else keep();
  }

  function keep() {
    stepScope?.end();
    stepScope = scope();
    index = def.steps.length;
    renderPips();
    root.classList.add("is-keep");
    sfx.win();
    onFinish();
    const card = h(
      "div",
      { class: "keep" },
      h("p", { class: "keep-kicker" }, `${def.num} · ${def.name} · done`),
      h("h2", { class: "keep-title", tabindex: "-1" }, def.keepTitle || "Keep this."),
      h(
        "ol",
        { class: "keep-list" },
        def.keep.map((k, i) =>
          h(
            "li",
            { style: `--i:${i}` },
            h("span", { class: "keep-word" }, k.word),
            h("span", { class: "keep-line", html: fill(k.line) })
          )
        )
      ),
      def.also ? h("div", { class: "keep-also" }, def.also.map((a) => h("p", { html: fill(a) }))) : null,
      h(
        "div",
        { class: "keep-actions" },
        h("button", { class: "btn btn-primary", type: "button", onclick: () => onExit("next") }, nextLabel()),
        h("button", { class: "btn btn-ghost", type: "button", onclick: () => show(0) }, "Do it again"),
        h("button", { class: "btn-link", type: "button", onclick: () => onExit() }, "All drills")
      )
    );
    body.replaceChildren(card);
    card.querySelector(".keep-title").focus({ preventScroll: true });
    scrollToEl(root);
    // Restore the two-pane body if they choose to repeat.
    stepScope.add(() => body.replaceChildren(stage, panel));
  }

  show(0);
  return { el: root, destroy: () => stepScope?.end() };
}

/**
 * A judgement call: a short scenario on the stage, and choices in the panel.
 * options: [{ label, ok, why }]
 */
export function choiceStep({ tag, title, text, scene, quote, options, after }) {
  return {
    tag,
    title,
    text,
    stageClass: "stage--scene",
    setup(ctx) {
      ctx.stage.append(
        h(
          "div",
          { class: "scene" },
          h("p", { class: "scene-label" }, scene || "What do you do?"),
          h("p", { class: "scene-quote", html: fill(quote) })
        )
      );
      let solved = false;
      const buttons = options.map((opt) => {
        const b = h(
          "button",
          {
            class: "btn btn-choice",
            type: "button",
            onclick: () => {
              if (solved) return;
              if (opt.ok) {
                solved = true;
                b.classList.add("is-right");
                buttons.forEach((x) => x !== b && (x.disabled = true));
                ctx.done(opt.why);
                if (after) after(ctx);
              } else {
                b.classList.add("is-wrong");
                b.disabled = true;
                ctx.say(opt.why, "no");
              }
            },
          },
          fill(opt.label)
        );
        return b;
      });
      ctx.actions.append(...buttons);
    },
  };
}
