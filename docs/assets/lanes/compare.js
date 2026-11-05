import { el, qs, qsList, loadPage, SITE_NAME } from "../dom.js";
import { fmtNum, fmtDuration, fmtCost } from "../fmt.js";
import { renderOutput, kindUi, summaryBlurb } from "../output.js";
import { localFeature, runDir, runUrl, effortPill, prettyModelName, modelParts, vendorOf, vendorName, vendorMark, vendorOptions, rankBy } from "../runs.js";
import { loadVotes, voteBar } from "../votes.js";
import { headerAuth, promptDialog, plural, offlineVotes } from "./common.js";

const main = document.getElementById("main");
const slug = qs("p");
document.getElementById("current-link").href = `classic/compare.html?p=${encodeURIComponent(slug ?? "")}&r=${qsList("r").map(encodeURIComponent).join(",")}`;
const page = await loadPage(slug, main);
if (page) {
  document.title = `Compare – ${page.title} – ${SITE_NAME}`;
  const runs = qsList("r").map((id) => page.runs.find((r) => r.id === id)).filter(Boolean);
  const votes = await loadVotes(slug);
  headerAuth(votes);
  const dialog = promptDialog(page, slug);
  const back = el("a", { class: "v2-back-btn", text: "← Back to runs", attrs: { href: `page.html?p=${encodeURIComponent(slug)}` } });
  const shortName = (r) => prettyModelName(modelParts(r.model).name);

  if (runs.length < 2) {
    main.replaceChildren(el("div", { class: "v2-cmp-top" }, [back, el("h1", { text: "Pick at least two runs to compare" })]));
  } else {
    // A cost of 0 means none was reported, so it never competes (as in rankBy).
    const has = (key, v) => typeof v === "number" && (key !== "cost_usd" || v > 0);
    const fmt = {
      duration_ms: (v) => fmtDuration(v),
      tokens_total: (v) => fmtNum(v),
      cost_usd: (v, r) => fmtCost(v, r.metrics.cost_estimated, r.metrics.cost_estimate_proxy),
    };
    const ranks = Object.fromEntries(Object.keys(fmt).map((k) => [k, rankBy(runs, k)]));
    const winners = [["cost_usd", "Cheapest"], ["duration_ms", "Fastest"], ["tokens_total", "Fewest tokens"]].map(([key, label]) => {
      const w = runs.find((r) => ranks[key].get(r.id) === 1);
      return w ? el("div", { class: "v2-win" }, [
        el("span", { class: "l", text: label }),
        el("span", { class: "v", text: fmt[key](w.metrics[key], w) }),
        el("span", { class: "w", text: `${shortName(w)} · ${w.effort}` }),
      ]) : null;
    }).filter(Boolean);

    const metric = (run, key, label) => {
      const vals = runs.map((r) => r.metrics?.[key]).filter((v) => has(key, v));
      const v = run.metrics?.[key];
      const ok = has(key, v);
      const best = ok && ranks[key].get(run.id) === 1;
      const max = Math.max(0, ...vals);
      return el("div", { class: best ? "v2-metric best" : "v2-metric" }, [
        el("span", { class: "k", text: label }),
        el("span", { class: "v", text: ok ? fmt[key](v, run) : key === "cost_usd" ? "n/a" : "–", attrs: !ok && key === "cost_usd" ? { title: "This run reported no cost" } : {} }),
        el("span", { class: "track" }, [el("span", { class: "fill", style: { width: ok && max ? `${Math.max(3, (v / max) * 100)}%` : "0%" } })]),
      ]);
    };

    const col = (run) => {
      const vo = vendorOptions(run.model);
      const bar = votes ? voteBar(votes, run.id) : offlineVotes();
      return el("article", { class: "v2-col", attrs: vo.attrs, style: vo.style }, [
        // a text is read in full in each column (a scrollable box), everything else is shown as on the cards
        el("div", { class: "v2-media" }, renderOutput(run, runDir(slug, run.id), { compact: !run.output?.text, href: runUrl(slug, run.id) })),
        el("div", { class: "v2-col-head" }, [
          el("a", { class: "who", attrs: { href: runUrl(slug, run.id), title: run.model } }, [
            vendorMark(run.model),
            el("span", { class: "name", text: shortName(run) }),
          ]),
          effortPill(run.effort),
          el("span", { class: "spacer" }),
          bar,
        ]),
        summaryBlurb(run, runUrl(slug, run.id)),
        el("div", { class: "v2-metrics-col" }, [
          metric(run, "duration_ms", "Time"),
          metric(run, "tokens_total", "Tokens"),
          metric(run, "cost_usd", "Cost"),
        ]),
      ]);
    };

    const models = new Set(page.runs.map((r) => r.model));
    main.replaceChildren(...[ // replaceChildren prints null as "null": the optional parts are filtered out below
      el("header", { class: "v2-cmp-top" }, [
        back,
        el("h1", { text: `Comparing ${runs.length} runs` }),
        el("div", { class: "v2-cmp-sub" }, [
          el("span", { class: "kind-chip", text: kindUi(page.kind).label, attrs: { "data-kind": page.kind } }),
          el("a", { class: "t", text: page.title, attrs: { href: `page.html?p=${encodeURIComponent(slug)}` } }),
          el("span", { class: "n", text: `${plural(page.runs.length, "run")} · ${plural(models.size, "model")}` }),
        ]),
        page.prompt ? el("p", { class: "v2-cmp-prompt", text: page.prompt }) : null,
        el("button", { class: "v2-link-btn", text: "View final prompt", attrs: { type: "button" }, on: { click: () => dialog.open() } }),
      ]),
      winners.length ? el("div", { class: "v2-wins" }, winners) : null,
      // local only: the video studio, opened with these runs in its slots (studio.html, ADR-0034)
      (await localFeature("video")) ? el("p", { class: "v2-studio" }, [el("a", { class: "v2-pill", text: "Make a video of these runs in the video studio", attrs: { href: `studio.html?p=${encodeURIComponent(slug)}&r=${runs.map((r) => encodeURIComponent(r.id)).join(",")}` } })]) : null,
      el("div", { class: "v2-cols" }, runs.map(col)),
      el("p", { class: "v2-cmp-note", text: "Green marks the best value in each row among the selected runs. Bars are scaled to the largest value." }),
    ].filter(Boolean));
    for (const n of main.querySelectorAll(".votes-label")) n.remove();
  }
}
