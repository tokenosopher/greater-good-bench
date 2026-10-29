import { el, getJSON, showMessage } from "../dom.js";
import { modelParts, vendorOf, vendorName, vendorMark, runDir, isFailed, coverOf, EFFORTS, byRankThenModel, prettyModelName, effortPill, localFeature } from "../runs.js";
import { kindUi, textCard } from "../output.js";
import { plural } from "./common.js";
import { setupRequestButton } from "./request.js";

const main = document.getElementById("main");
let pages = [];
try {
  pages = await getJSON("data/pages.json");
  await pickThumbs(pages);
} catch (err) {
  showMessage(main, `Could not load pages: ${err.message}`, "error");
}

const dateOf = (p) => {
  const d = p.updated ? new Date(p.updated) : null;
  return d && !Number.isNaN(d.getTime()) ? d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "";
};
const vendorCount = (p) => new Set((p.models || []).map(vendorOf)).size;
const pageHref = (p) => `page.html?p=${encodeURIComponent(p.slug)}`;
// A page without a picture whose runs wrote texts shows one of them as a text tile (title + excerpt) instead.
const thumbOf = (p) => (p.thumb = p.pickedThumb ?? p.thumb)
  ? el("img", { attrs: { src: p.thumb, alt: "", loading: "lazy" } })
  : p.pickedText ? textCard(p.pickedText.output)
  : el("div", { class: "thumb-ph", text: "no preview" });
const kindChip = (p) => el("span", { class: "kind-chip", text: kindUi(p.kind).label, attrs: { "data-kind": p.kind } });

function vendorIcons(models) {
  const byVendor = new Map();
  for (const m of models || []) {
    const v = vendorOf(m);
    if (!byVendor.has(v)) byVendor.set(v, { model: m, names: [] });
    byVendor.get(v).names.push(modelParts(m).short);
  }
  return el("div", { class: "vendor-icons" }, [...byVendor].map(([v, { model, names }]) => vendorMark(model, `${vendorName(v)}: ${names.join(", ")}`)));
}

function feature(p) {
  return el("a", { class: "v2-feature", attrs: { href: pageHref(p) } }, [
    slideshow(p),
    el("div", { class: "v2-feature-body" }, [
      el("span", { class: "eyebrow", text: "Latest prompt" }),
      el("h2", { text: p.title }),
      p.data?.prompt ? el("p", { class: "v2-feature-prompt", text: `“${p.data.prompt}”` }) : null,
      el("div", { class: "v2-meta" }, [
        el("span", { text: plural(p.n_runs, "run") }),
        el("span", { text: plural(vendorCount(p), "vendor") }),
        el("span", { text: dateOf(p) }),
      ]),
      el("span", { class: "v2-cta", text: "See and compare →" }),
    ]),
  ]);
}

function tile(p) {
  return el("a", { class: "v2-tile", attrs: { href: pageHref(p) } }, [
    el("div", { class: "v2-tile-media" }, [thumbOf(p), kindChip(p)]),
    el("div", { class: "v2-tile-body" }, [
      el("span", { class: "v2-tile-title", text: p.title }),
      vendorIcons(p.models),
      el("div", { class: "v2-meta" }, [el("span", { text: plural(p.n_runs, "run") }), el("span", { text: dateOf(p) })]),
    ]),
  ]);
}

// "Request a prompt" at the right end of the top bar: it becomes a GitHub issue (request.js, ADR-0030).
setupRequestButton(document.querySelector(".site-header"));
// local only (`art-crit serve`): the run monitor and the video studio (ADR-0027, ADR-0034)
localFeature("video").then((on) => {
  if (on) document.querySelector(".site-header").append(
    el("a", { class: "monitor-crumb", attrs: { href: "monitor.html" }, text: "Runs (local)" }),
    el("a", { class: "monitor-crumb", attrs: { href: "studio.html" }, text: "Video studio (local)" }));
});

// The question and why it is asked: shown above the prompts, and on its own while there are none yet.
const hero = () => el("section", { class: "v2-hero" }, [
  el("h1", {}, [document.createTextNode("Can AI make something that would "), el("span", { class: "hl-pill", text: "improve the world" }), document.createTextNode(" for the most people?")]),
  el("p", { class: "lede", text: "What gets measured in AI gets optimized, so this starts measuring it: frontier models are asked to make an SVG, a website, a 3D model, a game, an animation and an essay that, if everyone saw, used, played, watched or read it, would improve the world for the greatest number of people. Each prompt's outputs are shown side by side with the full agent transcript, time, tokens and cost. Nothing is judged automatically: the ranking is the owner's own, plus community votes." }),
]);

if (pages.length) {
  main.replaceChildren(hero(), feature(pages[0]));
  const kinds = [...new Set(pages.map((p) => p.kind))];
  const pills = el("div", { class: "v2-pills" });
  const grid = el("div", { class: "v2-grid" });
  let current = "all";
  const draw = () => {
    pills.replaceChildren(...[["all", "All", pages.length], ...kinds.map((k) => [k, kindUi(k).label, pages.filter((p) => p.kind === k).length])].map(([k, label, n]) =>
      el("button", { class: "v2-pill", attrs: { type: "button", "aria-pressed": String(current === k) }, on: { click: () => { current = k; draw(); } } },
        [document.createTextNode(label), el("span", { class: "n", text: String(n) })])));
    grid.replaceChildren(...pages.filter((p) => current === "all" || p.kind === current).map(tile));
  };
  draw();
  main.append(el("section", {}, [el("div", { class: "v2-section-head" }, [el("h2", { text: "All prompts" }), pills]), grid]));
} else if (!main.firstChild) {
  main.replaceChildren(hero(), el("p", { class: "msg msg-info", text: "No prompts have been run yet." }));
}

// Each page's picture comes from one of its highest-effort runs that made its output (and has a cover picture: its thumbnail, or the one covers.json names), so the cover
// shows a model at its best. Going down the list, a model (then a vendor) that already covers another page is avoided,
// so the covers don't all come from the same model. Ties go to the page owner's rank, then model order. A page whose
// data can't be read keeps the thumbnail from pages.json. A page's `cover` (the owner's pick) wins over all of this.
async function pickThumbs(pages) {
  const usedModel = new Map(), usedVendor = new Map();
  const level = (r) => EFFORTS.indexOf(r.effort); // -1 for an unknown effort: never above a known one
  const datas = await Promise.all(pages.map((p) => getJSON(`data/${encodeURIComponent(p.slug)}/page.json`).catch(() => null)));
  pages.forEach((p, i) => {
    p.data = datas[i];
    const runs = (datas[i]?.runs || []).filter((r) => !isFailed(r) && coverOf(r));
    // The owner's own pick for this page (covers.json, set through `art-crit serve`) replaces the default choice below.
    // It may be a run kept off the home page by default: the owner asked for it.
    const chosen = datas[i]?.cover && (datas[i].runs || []).find((r) => r.id === datas[i].cover.run && !isFailed(r));
    if (chosen) {
      p.pickedThumb = runDir(p.slug, chosen.id) + datas[i].cover.image;
      p.pickedFrom = chosen;
      usedModel.set(chosen.model, (usedModel.get(chosen.model) ?? 0) + 1);
      usedVendor.set(vendorOf(chosen.model), (usedVendor.get(vendorOf(chosen.model)) ?? 0) + 1);
      return;
    }
    if (!runs.length) {
      // No pictures (a text page): its highest-effort run with an excerpt stands for it.
      const texts = (datas[i]?.runs || []).filter((r) => !isFailed(r) && r.output?.excerpt != null);
      p.pickedText = texts.sort((a, b) => level(b) - level(a) || byRankThenModel(a, b))[0] ?? null;
      return;
    }
    const top = Math.max(...runs.map(level));
    const score = (r) => (usedModel.get(r.model) ?? 0) * 100 + (usedVendor.get(vendorOf(r.model)) ?? 0);
    const pick = runs.filter((r) => level(r) === top).sort((a, b) => score(a) - score(b) || byRankThenModel(a, b))[0];
    p.pickedThumb = runDir(p.slug, pick.id) + coverOf(pick);
    p.pickedFrom = pick;
    usedModel.set(pick.model, (usedModel.get(pick.model) ?? 0) + 1);
    usedVendor.set(vendorOf(pick.model), (usedVendor.get(vendorOf(pick.model)) ?? 0) + 1);
  });
}

// The featured prompt's picture is a slideshow of 3–4 of its best runs, each from a different model: the highest effort
// level first, then the next level down if that level has too few models. It starts with the run on its grid tile,
// changes every 4.5s, pauses while hovered or focused (and in a background tab), and never moves on its own with
// reduced motion. The dots (bottom center) switch slides; each dot names its model for screen readers and on hover.
function pickSlides(p, max = 4) {
  const level = (r) => EFFORTS.indexOf(r.effort);
  const runs = (p.data?.runs || []).filter((r) => !isFailed(r) && coverOf(r))
    .sort((a, b) => level(b) - level(a) || byRankThenModel(a, b));
  const out = [], models = new Set(), vendors = new Set();
  const take = (r) => { out.push(r); models.add(r.model); vendors.add(vendorOf(r.model)); };
  if (p.pickedFrom) take(p.pickedFrom);
  for (const pass of ["new vendor", "new model"]) {
    for (const r of runs) {
      if (out.length >= max) break;
      if (models.has(r.model) || (pass === "new vendor" && vendors.has(vendorOf(r.model)))) continue;
      // Stay at the top effort level while it still has unused models; only then go one level down.
      take(r);
    }
  }
  return out;
}

function slideshow(p) {
  const slides = pickSlides(p);
  const box = el("div", { class: "v2-feature-media" });
  if (slides.length < 2) {
    box.append(thumbOf(p), kindChip(p));
    return box;
  }
  const imgs = slides.map((r, i) => el("img", { class: i ? "slide" : "slide is-on", attrs: { src: i === 0 && r === p.pickedFrom ? p.pickedThumb : runDir(p.slug, r.id) + coverOf(r), alt: "", loading: i ? "lazy" : null } }));
  const dots = slides.map((r, i) => el("button", {
    class: "v2-dot", attrs: { type: "button", "aria-label": `Show ${prettyModelName(modelParts(r.model).name)} ${r.effort}`, title: `${prettyModelName(modelParts(r.model).name)} · ${r.effort}` },
    on: { click: (e) => { e.preventDefault(); e.stopPropagation(); show(i); restart(); } },
  }));
  let cur = 0;
  const show = (i) => {
    cur = (i + slides.length) % slides.length;
    imgs.forEach((img, j) => img.classList.toggle("is-on", j === cur));
    dots.forEach((d, j) => d.setAttribute("aria-current", String(j === cur)));
    imgs.forEach((img, j) => img.setAttribute("alt", j === cur ? `${prettyModelName(modelParts(slides[j].model).name)} ${slides[j].effort}` : ""));
  };
  show(0);
  let timer = 0, paused = false;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const restart = () => {
    clearInterval(timer);
    if (!reduced) timer = setInterval(() => { if (!paused && !document.hidden) show(cur + 1); }, 4500);
  };
  box.addEventListener("mouseenter", () => { paused = true; });
  box.addEventListener("mouseleave", () => { paused = false; });
  box.addEventListener("focusin", () => { paused = true; });
  box.addEventListener("focusout", () => { paused = false; });
  restart();
  box.append(...imgs, kindChip(p), el("div", { class: "v2-dots" }, dots));
  return box;
}
