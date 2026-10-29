// "Request a prompt" (ADR-0030): a visitor's prompt idea becomes an issue on the GitHub repo. On the published site
// the Worker opens it (POST api/request, signed in with GitHub); where there is no such API (art-crit serve, a plain
// static host, a Worker not yet configured) the form opens GitHub's own "new issue" page with everything filled in,
// for the visitor to submit there. Nothing is stored on this machine any more (the classic pages keep the local list).

import { el } from "../dom.js";
import { kindUi } from "../output.js";

const REPO_ISSUES = "https://github.com/tokenosopher/mtwabp-bench/issues";
const KINDS = [
  ["media", "Images or video the agent saves (SVG, PNG, MP4…)"],
  ["godot", "A Godot project, played in the browser"],
  ["web", "A web page with JS modules, packaged into one file"],
  ["blender", "A 3D model and renders made in Blender (viewable in 3D)"],
];
const DRAFT = "art-crit.request-draft"; // kept across the sign-in round trip only
const AGAIN = "#request"; // the hash sign-in returns to, which reopens the form with the draft

// The same issue the Worker would open (cloudflare/votes.mjs issueFor), for GitHub's prefilled new-issue page.
function fenced(text) {
  const longest = Math.max(0, ...(text.match(/`+/g) ?? []).map((run) => run.length));
  const fence = "`".repeat(Math.max(3, longest + 1));
  return `${fence}text\n${text}\n${fence}`;
}
function newIssueUrl({ prompt, kind, note }) {
  const first = prompt.split("\n")[0].replace(/\s+/g, " ").trim();
  const title = `Prompt request: ${first.length > 80 ? `${first.slice(0, 79)}…` : first}`;
  const body = [`**Kind:** ${kindUi(kind).label} (\`--kind ${kind}\`)`, "", "**Prompt**", "", fenced(prompt),
    ...(note ? ["", "**Note**", "", fenced(note)] : [])].join("\n");
  const url = new URL(`${REPO_ISSUES}/new`);
  url.search = new URLSearchParams({ title, body, labels: "prompt request" }).toString();
  return url.toString();
}

// The header button and its dialog. `header` is the .site-header to put the button in.
export function setupRequestButton(header) {
  const prompt = el("textarea", { attrs: { name: "prompt", rows: "5", required: "", minlength: "10", maxlength: "4000", placeholder: "e.g. Create an SVG of a pelican riding a bicycle" } });
  const note = el("textarea", { attrs: { name: "note", rows: "2", maxlength: "1000", placeholder: "Why it's interesting, what to look for…" } });
  const kinds = el("div", { class: "kind-options", attrs: { role: "radiogroup", "aria-label": "Kind" } }, KINDS.map(([kind, desc], i) =>
    el("label", { class: "kind-option" }, [
      el("input", { attrs: { type: "radio", name: "kind", value: kind, ...(i === 0 ? { checked: "" } : {}) } }),
      el("span", { class: "kind-option-body" }, [el("span", { class: "kind-chip", text: kindUi(kind).label, attrs: { "data-kind": kind } }), el("span", { class: "kind-desc", text: desc })]),
    ])));
  const status = el("p", { class: "form-error", attrs: { role: "status" } });
  const submit = el("button", { class: "btn", text: "Open the request", attrs: { type: "submit" } });
  const form = el("form", { class: "request-form", attrs: { method: "dialog" } });
  const close = () => dialog.close();
  const values = () => ({ prompt: prompt.value.trim(), kind: form.elements.kind.value, note: note.value.trim() });
  const done = (children) => {
    form.replaceChildren(
      el("div", { class: "dialog-head" }, [el("h2", { text: "Thanks!" }), el("button", { class: "aside-close", text: "×", attrs: { type: "button", "aria-label": "Close" }, on: { click: close } })]),
      el("p", { class: "dialog-lede" }, children),
      el("div", { class: "dialog-actions" }, [el("button", { class: "btn", text: "Done", attrs: { type: "button" }, on: { click: () => { close(); reset(); } } })]),
    );
  };
  const fields = [
    el("div", { class: "dialog-head" }, [
      el("h2", { text: "Request a prompt" }),
      el("button", { class: "aside-close", text: "×", attrs: { type: "button", "aria-label": "Close" }, on: { click: close } }),
    ]),
    el("p", { class: "dialog-lede", text: "Something for the models to make that, if everyone saw, used, played, watched or read it, would improve the world for the greatest number of people. It's posted as an issue on the site's GitHub repo, where you can follow it. You sign in with GitHub to send it." }),
    el("label", { class: "field" }, [el("span", { class: "field-label", text: "Prompt" }), prompt]),
    el("fieldset", { class: "field" }, [el("legend", { class: "field-label", text: "Kind" }), kinds]),
    el("label", { class: "field" }, [el("span", { class: "field-label" }, ["Note", el("span", { class: "muted", text: " optional" })]), note]),
    status,
    el("div", { class: "dialog-actions" }, [el("button", { class: "btn btn-ghost", text: "Cancel", attrs: { type: "button" }, on: { click: close } }), submit]),
  ];
  const reset = () => { form.replaceChildren(...fields); form.reset(); status.textContent = ""; };
  reset();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const v = values();
    if (v.prompt.length < 10) { status.textContent = "Write a prompt of at least 10 characters."; return; }
    status.textContent = "";
    submit.disabled = true;
    let res = null;
    try {
      res = await fetch("api/request", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(v) });
    } catch {} // offline or no API: falls through to GitHub's own form
    submit.disabled = false;
    const data = res && (res.headers.get("Content-Type") ?? "").startsWith("application/json") ? await res.json().catch(() => null) : null;
    if (res?.status === 201 && typeof data?.url === "string" && data.url.startsWith(`${REPO_ISSUES}/`)) {
      try { sessionStorage.removeItem(DRAFT); } catch {}
      done([document.createTextNode("Your request is issue "), el("a", { text: `#${data.number}`, attrs: { href: data.url, target: "_blank", rel: "noopener" } }), document.createTextNode(" on GitHub. Follow it there to see when it's run.")]);
      return;
    }
    if (res?.status === 401) { // signed out: sign in with GitHub, then come back to this form with the draft
      try { sessionStorage.setItem(DRAFT, JSON.stringify(v)); } catch {}
      location.assign(`api/login?return=${encodeURIComponent(location.pathname + location.search + AGAIN)}`);
      return;
    }
    if (!data || res.status === 404 || res.status === 503) { // no request API here: GitHub's prefilled form instead
      window.open(newIssueUrl(v), "_blank", "noopener");
      done([document.createTextNode("GitHub's new-issue form opened in a new tab with your prompt filled in. Submit it there to send the request.")]);
      return;
    }
    status.textContent = data.error || `Not sent (HTTP ${res.status}).`;
  });

  const dialog = el("dialog", { class: "request-dialog", attrs: { "aria-label": "Request a prompt" } }, [form]);
  dialog.addEventListener("click", (e) => { if (e.target === dialog) close(); }); // a click on the backdrop
  document.body.append(dialog);
  const open = () => { dialog.showModal(); prompt.focus(); };
  header.append(el("div", { class: "v2-head-request" }, [el("button", { class: "btn", text: "Request a prompt", attrs: { type: "button", id: "request-open" }, on: { click: open } })]));

  if (location.hash === AGAIN) { // back from signing in
    history.replaceState(null, "", location.pathname + location.search);
    try {
      const draft = JSON.parse(sessionStorage.getItem(DRAFT) ?? "null");
      if (draft) {
        prompt.value = draft.prompt ?? "";
        note.value = draft.note ?? "";
        const radio = [...form.elements.kind].find((r) => r.value === draft.kind);
        if (radio) radio.checked = true;
      }
    } catch {}
    open();
  }
}
