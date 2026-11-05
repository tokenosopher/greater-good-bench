import { el, qs, qsList, setQuery, loadPage, getJSON, SITE_NAME } from "../dom.js";
import { fmtNum, fmtDuration, fmtCost } from "../fmt.js";
import { renderOutput, kindUi, summaryBlurb } from "../output.js";
import {
  runDir, runUrl, effortPill, prettyModelLabel, prettyModelName, modelParts, vendorOf, vendorName, vendorMark,
  groupByVendor, vendorOptions, byRankThenModel, filterRuns, rankBy, bestSets, stateBadge, EFFORTS, effortIndex,
} from "../runs.js";
import { createSelection, selectBox } from "../selection.js";
import { loadVotes, voteBar } from "../votes.js";
import { createLane } from "./lane.js";
import { headerAuth, promptDialog, plural, offlineVotes } from "./common.js";

const main = document.getElementById("main");
const slug = qs("p");
document.getElementById("current-link").href = `classic/page.html?p=${encodeURIComponent(slug ?? "")}`;
const page = await loadPage(slug, main);
if (page) start(page);

async function start(page) {
  document.title = `${page.title} – ${SITE_NAME}`;
  const runs = page.runs || [];
  const votes = await loadVotes(slug);
  headerAuth(votes);
  const dialog = promptDialog(page, slug);
  const selection = createSelection(slug, runs.map((r) => r.id));
  const best = bestSets(runs);
  const fmtMetric = { duration_ms: fmtDuration, tokens_total: fmtNum, cost_usd: (v, r) => fmtCost(v, r.metrics.cost_estimated, r.metrics.cost_estimate_proxy) };

  let filter = { vendors: qsList("vendor"), efforts: qsList("effort") };
  let effortDesc = qs("sort") === "effort-desc"; // order of the cards in each row: low → high effort (default) or high → low

  // ---- strip ----
  let thumb = null;
  try {
    const pages = await getJSON("data/pages.json");
    thumb = pages.find((p) => p.slug === slug)?.thumb ?? null;
  } catch {}
  const tiles = [["cost_usd", "Cheapest"], ["duration_ms", "Fastest"], ["tokens_total", "Fewest tokens"]].map(([key, label]) => {
    const ranks = rankBy(runs, key);
    const w = runs.find((r) => ranks.get(r.id) === 1);
    if (!w) return null;
    return el("a", { class: "v2-hl", attrs: { href: runUrl(slug, w.id) } }, [
      el("span", { class: "l", text: label }),
      el("span", { class: "v", text: fmtMetric[key](w.metrics[key], w) }),
      el("span", { class: "s" }, [effortPill(w.effort), el("span", { text: prettyModelName(modelParts(w.model).name) })]),
    ]);
  }).filter(Boolean);
  const models = new Set(runs.map((r) => r.model));
  const strip = el("section", { class: "v2-strip" }, [
    thumb ? el("img", { class: "v2-strip-thumb", attrs: { src: thumb, alt: "" } }) : null,
    el("div", { class: "v2-strip-main" }, [
      el("h1", { text: page.title }),
      el("div", { class: "v2-meta" }, [
        el("span", { class: "kind-chip", text: kindUi(page.kind).label, attrs: { "data-kind": page.kind } }),
        el("span", { text: plural(runs.length, "run") }),
        el("span", { text: plural(models.size, "model") }),
      ]),
      page.prompt ? el("p", { class: "v2-prompt-line", text: page.prompt }) : null,
      el("button", { class: "v2-link-btn", text: "View final prompt", attrs: { type: "button" }, on: { click: () => dialog.open() } }),
    ]),
    tiles.length ? el("div", { class: "v2-tiles" }, tiles) : null,
  ]);

  // ---- filters ----
  const filters = el("div", { class: "v2-filters", attrs: { role: "group", "aria-label": "Filter runs" } });
  const lanes = el("div", { class: "v2-lanes" });
  const tray = el("div", { class: "v2-tray", attrs: { role: "region", "aria-label": "Selected runs" } });
  tray.hidden = true;
  main.replaceChildren(strip, filters, lanes);
  document.body.append(tray);

  const toggle = (key, value) => {
    const list = filter[key];
    filter[key] = list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
    setQuery({ vendor: filter.vendors.join(","), effort: filter.efforts.join(",") });
    drawFilters();
    drawLanes();
  };
  const pill = (label, on, click) => el("button", { class: "v2-pill", text: label, attrs: { type: "button", "aria-pressed": String(on) }, on: { click } });
  function drawFilters() {
    const vendors = [...new Set(runs.map((r) => vendorOf(r.model)))];
    const efforts = [...new Set(runs.map((r) => r.effort))].sort((a, b) => effortIndex(a) - effortIndex(b));
    filters.replaceChildren(...[
      el("div", { class: "grp" }, [el("span", { class: "lbl", text: "Vendor" }), ...vendors.map((v) => pill(vendorName(v), filter.vendors.includes(v), () => toggle("vendors", v)))]),
      efforts.length > 1 ? el("div", { class: "grp" }, [el("span", { class: "lbl", text: "Effort" }), ...efforts.map((e) => pill(e ?? "–", filter.efforts.includes(e), () => toggle("efforts", e)))]) : null,
      el("span", { class: "spacer" }),
      el("div", { class: "grp" }, [
        el("span", { class: "lbl", text: "Sort" }),
        el("button", {
          class: "v2-pill v2-sort", text: effortDesc ? "Effort: high → low" : "Effort: low → high",
          attrs: { type: "button", title: "Reverse the order of the cards in each row", "aria-label": `Sorted by effort, ${effortDesc ? "high to low" : "low to high"}. Click to reverse.` },
          on: { click: () => { effortDesc = !effortDesc; setQuery({ sort: effortDesc ? "effort-desc" : null }); drawFilters(); drawLanes(); } },
        }),
      ]),
    ].filter(Boolean)); // one effort level: no Effort group (replaceChildren would print the null)
  }

  // ---- cards ----
  const cardBoxes = new Map(); // run id → [checkbox, card]
  function card(run) {
    const m = run.metrics || {};
    const metricNode = (key, text) => el("span", { class: best[key]?.has(run.id) ? "best" : "", text, attrs: best[key]?.has(run.id) ? { title: "best of this page" } : {} });
    const box = selectBox(run, selection);
    const vo = vendorOptions(run.model);
    const node = el("article", { class: "v2-card", attrs: vo.attrs, style: vo.style }, [
      openable(el("div", { class: "v2-media" }, [...renderOutput(run, runDir(slug, run.id), { compact: true, href: runUrl(slug, run.id) }), el("label", { class: "v2-select-hit" }, [box])]), runUrl(slug, run.id)),
      el("div", { class: "v2-card-head" }, [
        el("a", { class: "title", attrs: { href: runUrl(slug, run.id) } }, [prettyModelLabel(run.model)]),
        effortPill(run.effort),
        stateBadge(run),
        el("a", { class: "open", text: "↗", attrs: { href: runUrl(slug, run.id), title: "Open the run" } }),
      ]),
      summaryBlurb(run, runUrl(slug, run.id)),
      el("div", { class: "v2-metrics" }, [
        metricNode("duration_ms", fmtDuration(m.duration_ms)),
        metricNode("tokens_total", `${fmtNum(m.tokens_total)} tok`),
        metricNode("cost_usd", fmtMetric.cost_usd(m.cost_usd, run)),
      ]),
      votes ? voteBar(votes, run.id) : offlineVotes(),
    ]);
    for (const l of node.querySelectorAll(".votes-label")) l.textContent = "Your vote:";
    cardBoxes.set(run.id, [box, node]);
    return node;
  }

  function drawLanes() {
    cardBoxes.clear();
    const shown = filterRuns(runs, { vendors: filter.vendors, efforts: filter.efforts }).sort(byRankThenModel);
    if (!shown.length) {
      lanes.replaceChildren(el("p", { class: "msg", text: "No runs match these filters." }));
      return;
    }
    lanes.replaceChildren(...byModel(shown, effortDesc).map((g) => {
      const lane = createLane(g.runs.map(card));
      const range = el("span", { class: "range" });
      lane.onRange = (a, b, more) => { range.textContent = more ? `showing ${a}–${b}` : `all ${g.runs.length} shown`; };
      const vo = vendorOptions(g.runs[0].model);
      return el("section", { class: "v2-lane", attrs: vo.attrs, style: vo.style }, [
        el("div", { class: "v2-lane-head" }, [el("span", { class: "dot" }), el("h2", {}, [el("span", { class: "vend", text: g.vendor }), el("span", { class: "sep", text: " – " }), document.createTextNode(g.name)]), el("span", { class: "count", text: `${plural(g.runs.length, "run")} ·` }), range]),
        lane.node,
      ]);
    }));
    syncSelection();
  }

  // ---- selection tray ----
  function syncSelection() {
    for (const [id, [box, node]] of cardBoxes) {
      box.checked = selection.has(id);
      node.classList.toggle("is-selected", box.checked);
    }
    const picked = selection.ids.map((id) => runs.find((r) => r.id === id)).filter(Boolean);
    tray.hidden = picked.length === 0;
    document.body.classList.toggle("has-tray", picked.length > 0);
    if (!picked.length) return;
    const few = picked.length < 2;
    const link = el("a", { class: "v2-tray-go", text: "Compare in detail →", attrs: { href: `compare.html?p=${encodeURIComponent(slug)}&r=${picked.map((r) => encodeURIComponent(r.id)).join(",")}`, "aria-disabled": String(few) } });
    tray.replaceChildren(el("div", { class: "v2-tray-inner" }, [
      el("div", { class: "v2-tray-head" }, [
        el("h3", { text: "Compare" }),
        el("span", { class: "v2-tray-label", text: few ? "1 run selected — pick at least one more to compare" : `${picked.length} runs selected` }),
        el("span", { class: "spacer" }),
        el("button", { class: "v2-tray-clear", text: "Clear all", attrs: { type: "button" }, on: { click: () => selection.clear() } }),
        link,
      ]),
      el("div", { class: "v2-tray-items" }, picked.map((r) => {
        const src = r.thumb ? runDir(slug, r.id) + r.thumb : null;
        const vo = vendorOptions(r.model);
        return el("div", { class: "v2-tray-item", attrs: vo.attrs, style: vo.style }, [
          el("div", { class: "pic" }, [
            src ? el("img", { attrs: { src, alt: "" } }) : null,
            el("button", { class: "x", attrs: { type: "button", "aria-label": "Remove from comparison" }, on: { click: () => selection.set(r.id, false) } }, [el("span", { text: "×" })]),
          ]),
          el("div", { class: "cap" }, [el("b", { text: prettyModelName(modelParts(r.model).name) }), el("span", { text: `${vendorName(vendorOf(r.model))} · ${r.effort ?? "–"}` })]),
        ]);
      })),
    ]));
  }
  selection.onChange = syncSelection;

  drawFilters();
  drawLanes();
}

// One lane per model ("Anthropic – Haiku 5.5"): vendors in their usual order, a vendor's models by their best rank then
// name, and each model's runs from low to high effort (or high to low with `desc`).
function byModel(runs, desc = false) {
  const lanes = [];
  for (const v of groupByVendor(runs)) {
    const models = new Map();
    for (const r of v.runs) {
      if (!models.has(r.model)) {
        const { name, via } = modelParts(r.model);
        models.set(r.model, { vendor: v.name, name: prettyModelName(name) + (via ? ` via ${via}` : ""), runs: [] });
      }
      models.get(r.model).runs.push(r);
    }
    const best = (g) => Math.min(...g.runs.map((r) => r.rank ?? Infinity));
    const groups = [...models.values()].sort((a, b) => best(a) - best(b) || a.name.localeCompare(b.name));
    for (const g of groups) g.runs.sort((a, b) => (effortIndex(a.effort) - effortIndex(b.effort)) * (desc ? -1 : 1));
    lanes.push(...groups);
  }
  return lanes;
}

// A card's media opens the run page on a click anywhere in it — a video's picture or the empty space under a short image
// included — except on the controls that do their own thing (checkbox, thumbnails, play / View in 3D, links). Videos on
// cards show their poster without native controls, so a click there opens the run instead of playing in the small box.
// (A click that ends a drag never gets here: the lane swallows it.)
function openable(media, href) {
  const quiet = () => { for (const v of media.querySelectorAll("video[controls]")) v.removeAttribute("controls"); };
  quiet();
  new MutationObserver(quiet).observe(media, { childList: true, subtree: true }); // a thumbnail swaps in a fresh <video>
  media.classList.add("is-openable");
  media.addEventListener("click", (e) => {
    if (e.defaultPrevented || e.target.closest("a, button, input, label, iframe, .model-stage")) return;
    if (e.metaKey || e.ctrlKey || e.button === 1) window.open(href, "_blank");
    else location.assign(href);
  });
  return media;
}
