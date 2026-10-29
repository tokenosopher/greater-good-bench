// Prompt requests: a "Request a prompt" form on the home page and the list of requested prompts, each with the
// `art-crit run` command that would make it a page. Local only: `art-crit serve` keeps them in requests.json next to
// docs/ (never published), and the published site has no api/requests, so nothing here is shown there.

import { el, getJSON } from "./dom.js";
import { fmtDateShort, fmtDate } from "./fmt.js";
import { kindUi } from "./output.js";

const KINDS = [
  ["media", "Images or video the agent saves (SVG, PNG, MP4…)"],
  ["godot", "A Godot project, played in the browser"],
  ["web", "A web page with JS modules, packaged into one file"],
  ["blender", "A 3D model and renders made in Blender (viewable in 3D)"],
  ["text", "Writing the agent saves as one Markdown file (an essay, a story…)"],
];

// Shown only when served by `art-crit serve` on this machine (it answers api/local with requests: true).
async function available() {
  if (!["localhost", "127.0.0.1", "[::1]"].includes(location.hostname)) return false;
  try {
    const res = await fetch("api/local", { cache: "no-store" });
    return res.ok && (await res.json()).requests === true;
  } catch {
    return false;
  }
}

async function send(body) {
  const res = await fetch("api/requests", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data.requests;
}

// A POSIX-shell word: 'it'\''s' for "it's".
const shellWord = (s) => `'${s.replaceAll("'", `'\\''`)}'`;

export function runCommand({ prompt, kind, title, set }) {
  return ["uv run art-crit run", `-k ${kind}`, title ? `-t ${shellWord(title)}` : null, set ? `-s ${set}` : null, shellWord(prompt || "…")]
    .filter(Boolean)
    .join(" ");
}

// `actions` gets the "Request a prompt" button, `list` the requested prompts (hidden while there are none).
export async function setupRequests(actions, list) {
  if (!(await available())) return;
  let { requests, sets } = await getJSON("api/requests");
  const { dialog, open } = requestDialog(sets, (items) => { requests = items; draw(); });
  document.body.append(dialog);
  actions.append(el("button", { class: "btn", text: "Request a prompt", attrs: { type: "button", id: "request-open" }, on: { click: open } }));
  actions.hidden = false;

  const draw = () => {
    list.hidden = !requests.length;
    list.replaceChildren(
      el("div", { class: "section-head" }, [
        el("h2", { text: "Requested prompts" }),
        el("span", { class: "count", text: `${requests.length} waiting` }),
        el("span", { class: "spacer" }),
        el("span", { class: "muted requests-where", text: "saved in requests.json on this machine, never published" }),
      ]),
      el("div", { class: "request-grid" }, [...requests].reverse().map((r) => requestCard(r, async () => {
        if (!confirm("Remove this request?")) return;
        requests = await send({ remove: r.id });
        draw();
      }))),
    );
  };
  draw();
}

function requestCard(r, onRemove) {
  const cmd = runCommand(r);
  const copy = el("button", { class: "btn btn-secondary btn-sm", text: "Copy command", attrs: { type: "button" } });
  copy.addEventListener("click", async () => {
    await navigator.clipboard.writeText(cmd);
    copy.textContent = "Copied";
    setTimeout(() => (copy.textContent = "Copy command"), 1500);
  });
  return el("article", { class: "request-card", attrs: { "data-id": r.id } }, [
    el("div", { class: "request-top" }, [
      el("span", { class: "kind-chip", text: kindUi(r.kind).label, attrs: { "data-kind": r.kind } }),
      r.set ? el("span", { class: "request-set", text: `set: ${r.set}` }) : null,
      el("span", { class: "request-date", text: fmtDateShort(r.created), attrs: { title: `requested ${fmtDate(r.created)}` } }),
    ]),
    r.title ? el("h3", { class: "request-title", text: r.title }) : null,
    el("p", { class: "request-prompt", text: r.prompt }),
    r.note ? el("p", { class: "request-note", text: r.note }) : null,
    el("pre", { class: "request-cmd", text: cmd }),
    el("div", { class: "request-actions" }, [
      copy,
      el("button", { class: "link-button request-remove", text: "Remove", attrs: { type: "button" }, on: { click: onRemove } }),
    ]),
  ]);
}

// The form, in a modal <dialog>: prompt, kind, optional title / note / model set, and a live preview of the command.
function requestDialog(sets, onSaved) {
  const field = (label, control, hint) => el("label", { class: "field" }, [el("span", { class: "field-label" }, [label, hint ? el("span", { class: "muted", text: ` ${hint}` }) : null]), control]);
  const prompt = el("textarea", { attrs: { name: "prompt", rows: "5", required: "", maxlength: "4000", placeholder: "e.g. An SVG that, if everyone saw it, would improve the world for the greatest number of people." } });
  const title = el("input", { attrs: { name: "title", type: "text", maxlength: "120", placeholder: "Pelican on a bicycle" } });
  const note = el("textarea", { attrs: { name: "note", rows: "2", maxlength: "1000", placeholder: "Why it's interesting, what to look for…" } });
  const set = el("select", { attrs: { name: "set" } }, [el("option", { text: "choose models later", attrs: { value: "" } }), ...sets.map((s) => el("option", { text: s, attrs: { value: s } }))]);
  const kinds = el("div", { class: "kind-options", attrs: { role: "radiogroup", "aria-label": "Kind" } }, KINDS.map(([kind, desc], i) =>
    el("label", { class: "kind-option" }, [
      el("input", { attrs: { type: "radio", name: "kind", value: kind, ...(i === 0 ? { checked: "" } : {}) } }),
      el("span", { class: "kind-option-body" }, [el("span", { class: "kind-chip", text: kindUi(kind).label, attrs: { "data-kind": kind } }), el("span", { class: "kind-desc", text: desc })]),
    ])));
  const preview = el("pre", { class: "request-cmd" });
  const error = el("p", { class: "form-error", attrs: { role: "alert" } });
  const form = el("form", { class: "request-form", attrs: { method: "dialog" } });
  const values = () => ({ prompt: prompt.value.trim(), kind: form.elements.kind.value, title: title.value.trim(), note: note.value.trim(), set: set.value });
  const update = () => { preview.textContent = runCommand(values()); };
  const close = () => dialog.close();
  form.append(
    el("div", { class: "dialog-head" }, [
      el("h2", { text: "Request a prompt" }),
      el("button", { class: "aside-close", text: "×", attrs: { type: "button", "aria-label": "Close" }, on: { click: close } }),
    ]),
    el("p", { class: "dialog-lede", text: "Something for the models to make that would improve the world for the greatest number of people. It's saved on this machine with the command to run it; nothing is published until you run it." }),
    field("Prompt", prompt),
    el("fieldset", { class: "field" }, [el("legend", { class: "field-label", text: "Kind" }), kinds]),
    el("div", { class: "field-row" }, [field("Title", title, "optional"), field("Models", set, "a set from art-crit.toml")]),
    field("Note", note, "optional"),
    el("div", { class: "field" }, [el("span", { class: "field-label", text: "Command" }), preview]),
    error,
    el("div", { class: "dialog-actions" }, [
      el("button", { class: "btn btn-ghost", text: "Cancel", attrs: { type: "button" }, on: { click: close } }),
      el("button", { class: "btn", text: "Save request", attrs: { type: "submit" } }),
    ]),
  );
  form.addEventListener("input", update);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    error.textContent = "";
    try {
      onSaved(await send({ add: values() }));
      form.reset();
      update();
      close();
    } catch (err) {
      error.textContent = err.message;
    }
  });
  update();
  const dialog = el("dialog", { class: "request-dialog", attrs: { "aria-label": "Request a prompt" } }, [form]);
  dialog.addEventListener("click", (e) => { if (e.target === dialog) close(); }); // a click on the backdrop
  return { dialog, open: () => { dialog.showModal(); prompt.focus(); } };
}
