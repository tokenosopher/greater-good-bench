// A run's output on screen. The sandbox-critical code lives here and only here: games and pages are embedded only by
// sandboxedGame() (never allow-same-origin), model-made images and SVGs only through mediaElement() (<img>, ADR-0004).
// A .glb is data that model.js parses with three.js (nothing in it runs), so it needs no frame.

import { el, badge, getText } from "./dom.js";
import { fmtBytes, fmtNum } from "./fmt.js";
import { mountModel } from "./model.js";

// What differs per kind in the UI: its name, the run page's output tab, what a run without output says,
// the badge for a kind step that failed, the words on a card's "open the run" cue for a game or page (`open`), and
// whether its output is a gallery of files (output.items) or a text to read (output.text) rather than a game or page.
// Anything else (kinds the viewer doesn't know) reads as a game.
const KIND_UI = {
  godot: { label: "Game", tab: "Game", none: "No playable build recorded for this run.", failed: "export failed", open: "Play" },
  media: { label: "Vector", tab: "Output", none: "No output files recorded for this run.", failed: "output failed", gallery: true },
  web: { label: "Web", tab: "Page", none: "No packaged page recorded for this run.", failed: "packaging failed", open: "View the page" },
  blender: { label: "3D", tab: "Output", none: "No model or renders recorded for this run.", failed: "output failed", gallery: true },
  text: { label: "Text", tab: "Read", none: "No text recorded for this run.", failed: "text failed", text: true },
};

export function kindUi(kind) {
  return KIND_UI[kind] ?? KIND_UI.godot;
}

export function outputOk(run) {
  return run.output?.ok === true;
}

// true / false once the output was checked (booted, loaded offline, files readable), null when it wasn't.
export function outputVerified(run) {
  return run.output?.verified ?? null;
}

// A badge for a run whose agent finished but whose output step failed ("export failed"), else null.
export function outputBadge(run) {
  return run.output && !run.output.ok ? badge(kindUi(run.kind).failed, "bad") : null;
}

// The one place games are embedded: sandboxed without allow-same-origin, so game
// code gets an opaque origin and can't touch this site's storage or cookies.
export function sandboxedGame(entryUrl) {
  return el("iframe", {
    attrs: { src: entryUrl, sandbox: "allow-scripts allow-pointer-lock", allow: "fullscreen; autoplay; gamepad" },
  });
}

// Builds a click-to-play `.game-frame`: an overlay (thumb + play button, carrying `data-play`) and a "Play full screen"
// button (always in the markup, shown only at phone width by style.css's 720px block), both replaced in place by a
// sandboxed iframe on click. Games never boot on their own. Full screen is asked for
// in that same click (the Fullscreen API needs a user gesture) on the wrapper, not the iframe, so the frame keeps exactly
// sandboxedGame()'s attributes and can carry an exit button; Esc leaves full screen and the game keeps running in place.
// Where full screen isn't available or is refused (iPhone Safari), the game simply plays in place. Returns the frame.
export function buildGameFrame(entryUrl, thumbUrl) {
  const frame = el("div", { class: "game-frame" });
  const overlay = el(
    "button",
    {
      class: "play-overlay",
      attrs: { type: "button", "data-play": "1", "aria-label": "Play" },
    },
    [el("span", { class: "play-icon", text: "▶" }), el("span", { class: "play-label", text: "Click to play" })]
  );
  if (thumbUrl) overlay.style.backgroundImage = `url("${thumbUrl}")`;
  const full = el("button", { class: "play-full", attrs: { type: "button", title: "Play full screen (Esc to leave)" } },
    [el("span", { class: "play-full-icon", text: "⛶", attrs: { "aria-hidden": "true" } }), el("span", { text: "Play full screen" })]);
  const play = (fullscreen) => {
    const game = sandboxedGame(entryUrl);
    const exit = el("button", { class: "fs-exit", text: "Exit full screen (Esc)", attrs: { type: "button" }, on: { click: () => leaveFullscreen() } });
    frame.replaceChildren(game, exit);
    if (fullscreen) enterFullscreen(frame);
    game.focus(); // keys go to the game without another click
  };
  overlay.addEventListener("click", () => play(false));
  full.addEventListener("click", () => play(true));
  frame.append(overlay, full);
  return frame;
}

// Full screen on `node` where the browser allows it (prefixed on older Safari); a refusal or no API at all leaves the
// game playing in place.
function enterFullscreen(node) {
  const request = node.requestFullscreen ?? node.webkitRequestFullscreen;
  if (!request) return;
  try {
    request.call(node)?.catch?.(() => {});
  } catch {}
}

function leaveFullscreen() {
  const exit = document.exitFullscreen ?? document.webkitExitFullscreen;
  if ((document.fullscreenElement ?? document.webkitFullscreenElement) && exit) exit.call(document)?.catch?.(() => {});
}

// One media output (run.media item). Model-made SVGs may contain scripts, so every image,
// SVG included, is shown through <img> (which never runs them) and never inlined or framed.
// Videos never autoplay: like games, they start on an explicit click. The recorded size goes on as width/height, so
// a full-size gallery reserves the space and an SVG without its own size isn't drawn at the default 300×150.
// `compact` (a card) shows the item's thumbnail where it has one (`item.thumb`, an 800 px JPEG made at import,
// ADR-0029) instead of the file itself; the run page's gallery always shows the file.
export function mediaElement(item, base, poster = null, { compact = false } = {}) {
  if (item.type === "model") return modelElement(item, base, poster, { compact });
  const size = { width: item.width ?? null, height: item.height ?? null };
  if (item.type === "video") {
    const still = (compact && item.thumb) || item.poster;
    return el("video", {
      attrs: { src: base + item.path, poster: still ? base + still : null, controls: "", preload: "none", playsinline: "", loop: "", ...size },
    });
  }
  return el("img", { attrs: { src: base + shown(item, compact), alt: "", loading: "lazy", ...size } });
}

// The file a card (`compact`) or the run page shows for an image item: its thumbnail, or the image itself.
const shown = (item, compact) => (compact && item.thumb) || item.path;

// A .glb (blender kind) as a click-to-view box: the run's first render (if any) behind a "View in 3D" button, replaced in
// place by the interactive viewer (model.js) on click. Like games, nothing loads (three.js or the model) until then.
export function modelElement(item, base, poster = null, { compact = false } = {}) {
  const box = el("div", { class: "model-view" });
  const overlay = el("button", { class: "play-overlay", attrs: { type: "button", "aria-label": "View the 3D model" } },
    [el("span", { class: "play-icon", text: "\u25B6" }), el("span", { class: "play-label", text: "View in 3D" })]);
  if (poster) overlay.style.backgroundImage = `url("${base + shown(poster, compact)}")`;
  overlay.addEventListener("click", () => {
    const stage = el("div", { class: "model-stage" });
    box.replaceChildren(stage, el("p", { class: "model-hint", text: "drag to orbit · scroll to zoom · right-drag to pan" }));
    mountModel(stage, base + item.path).catch((err) => box.replaceChildren(el("p", { class: "msg", text: `Could not show the model: ${err.message}` })));
  });
  box.append(overlay);
  return box;
}

// The first render of a run, shown behind its model's "View in 3D" button.
const posterOf = (items) => items.find((i) => i.type === "image") ?? null;

// The items a gallery shows, and the hero a card picks from: the 3D model(s) when there is one (its first render stays
// as the "View in 3D" poster), else the video(s), else every image. Renders and stills beside a model or a video are
// working files; the gallery lists them under "Other files" instead (by item type, never by kind name).
export function shownItems(items) {
  const models = items.filter((i) => i.type === "model");
  if (models.length) return models;
  const videos = items.filter((i) => i.type === "video");
  return videos.length ? videos : items;
}

// A run's media items as captioned figures (file name, size, duration) with download links: the shownItems() ones,
// then any others as a small "Other files" list of download links, so nothing is lost.
// Downloads use the `download` attribute so an SVG is saved, never opened as a page here. `full` (the run page) shows
// them one below the other at their own size (never wider than the page) instead of in fixed 4:3 boxes. `tools(item)`
// returns extra nodes for an item's caption (the owner's local cover buttons).
export function mediaGallery(items, base, { full = false, tools = null } = {}) {
  const grid = el("div", { class: full ? "media-grid is-full" : "media-grid" });
  const shownSet = shownItems(items || []);
  for (const item of shownSet) {
    const name = item.path.split("/").pop();
    const dims = item.width && item.height ? `${item.width}×${item.height}` : null;
    const dur = item.duration_s != null ? `${Number(item.duration_s).toFixed(1)}s` : null;
    const tris = item.triangles != null ? `${fmtNum(item.triangles)} triangles` : null;
    const caption = el("figcaption", {}, [
      el("span", { text: [name, dims, dur, tris, fmtBytes(item.bytes)].filter(Boolean).join(" · ") }),
      el("a", { text: "download", attrs: { href: base + item.path, download: name } }),
      ...(tools?.(item) ?? []),
    ]);
    const boxClass = item.type === "model" && full ? "media-full is-model" : full ? "media-full" : "media-box";
    grid.append(el("figure", { class: item.type === "model" ? "media-item is-model" : "media-item" }, [el("div", { class: boxClass }, [mediaElement(item, base, posterOf(items))]), caption]));
  }
  const others = (items || []).filter((i) => !shownSet.includes(i));
  if (others.length) {
    grid.append(el("div", { class: "media-other" }, [
      el("h3", { class: "media-other-title", text: "Other files" }),
      el("ul", {}, others.map((item) => {
        const name = item.path.split("/").pop();
        return el("li", {}, [
          el("a", { text: name, attrs: { href: base + item.path, download: name } }),
          el("span", { class: "muted", text: [item.width && item.height ? `${item.width}×${item.height}` : null, fmtBytes(item.bytes)].filter(Boolean).join(" · ") }),
          ...(tools?.(item) ?? []), // the owner's cover buttons stay reachable for a hidden still
        ]);
      })),
    ]));
  }
  return grid;
}

// "3 files · 1 video": how many outputs a media run has, for the corner badge on its card and table thumbnail.
export function mediaCount(items) {
  const count = (type, noun) => {
    const n = items.filter((i) => i.type === type).length;
    return n ? ` · ${n} ${noun}${n === 1 ? "" : "s"}` : "";
  };
  return `${items.length} files${count("video", "video")}${count("model", "3D model")}`;
}

// A media run on a card, at a fixed height: one output as the hero (a video or 3D model if there is one; both still start
// on a click), a corner badge counting the outputs, and a strip of small thumbnails that swap the hero in place.
// Everything is shown through mediaElement(), so model-made SVGs stay <img> (ADR-0004). With `href` (the run page), an
// image hero is a link there; a video hero isn't, so a click still plays it.
export function mediaCard(items, base, href = null) {
  const box = el("div", { class: "media-box" });
  const poster = posterOf(items);
  const thumbs = items.length > 1 ? items.map((item, i) => {
    const src = item.type === "video" ? item.thumb || item.poster : item.type === "model" ? poster && shown(poster, true) : shown(item, true);
    const label = item.path.split("/").pop();
    return el("button", {
      class: item.type === "image" ? "media-thumb" : `media-thumb is-${item.type}`,
      attrs: { type: "button", title: label, "aria-label": `Show ${label}` },
      on: { click: () => show(i) },
    }, [src ? el("img", { attrs: { src: base + src, alt: "", loading: "lazy" } }) : null]);
  }) : [];
  const show = (i) => {
    const media = mediaElement(items[i], base, poster, { compact: true });
    const hero = href && items[i].type === "image" ? el("a", { class: "media-link", attrs: { href, title: "Open the run" } }, [media]) : media;
    box.replaceChildren(...[hero, items.length > 1 ? el("span", { class: "media-count", text: mediaCount(items) }) : null].filter(Boolean));
    thumbs.forEach((t, j) => t.setAttribute("aria-current", String(j === i)));
  };
  if (items.length) show(items.indexOf(shownItems(items)[0]));
  return el("div", { class: "media-card" }, [box, thumbs.length ? el("div", { class: "media-strip" }, thumbs) : null]);
}

// A card's output as one link to the run page (`href`): the lanes cards and compare columns never play anything in
// place. It shows a still (a game's or page's screenshot, the hero item's thumbnail or poster, a model's first render),
// a strip of the outputs' thumbnails when there are several (pictures only, part of the link), and a cue saying what
// the run page does: "▶ Play" / "▶ Watch" / "▶ View in 3D" in the middle, or "Open run →" in the corner for pictures.
// Images, SVGs included, stay <img> (mediaElement(), ADR-0004); nothing here loads a frame, a video or three.js.
function outputLink(run, base, href) {
  const out = run.output;
  let still = null;
  let strip = null;
  let cue = null;
  if (out.items) {
    const items = out.items;
    const hero = shownItems(items)[0];
    const poster = posterOf(items);
    const picture = (item) => (item.type === "video" ? item.thumb || item.poster : item.type === "model" ? poster && shown(poster, true) : shown(item, true));
    if (hero) {
      const src = picture(hero);
      still = hero.type === "image" ? mediaElement(hero, base, null, { compact: true }) : src ? el("img", { attrs: { src: base + src, alt: "", loading: "lazy" } }) : null;
      cue = hero.type === "model" ? "View in 3D" : hero.type === "video" ? "Watch" : null;
    }
    const shownSet = shownItems(items);
    if (shownSet.length > 1) {
      strip = el("span", { class: "media-strip" }, shownSet.map((item) => {
        const src = picture(item);
        return el("span", { class: item.type === "image" ? "media-thumb" : `media-thumb is-${item.type}`, attrs: { "aria-current": String(item === hero) } },
          [src ? el("img", { attrs: { src: base + src, alt: "", loading: "lazy" } }) : null]);
      }));
    }
  } else {
    still = run.thumb ? el("img", { attrs: { src: base + run.thumb, alt: "", loading: "lazy" } }) : null;
    cue = kindUi(run.kind).open ?? "Play";
  }
  const label = cue ?? "Open run";
  // the cue sits on the picture itself (centred on it, or in its corner), the strip at the bottom of the whole link
  const cueNode = el("span", { class: "open-cue" }, cue
    ? [el("span", { class: "open-icon", text: "▶", attrs: { "aria-hidden": "true" } }), el("span", { class: "open-label", text: cue })]
    : [el("span", { class: "open-label", text: "Open run" }), el("span", { class: "open-icon", text: "→", attrs: { "aria-hidden": "true" } })]);
  return el("a", { class: cue ? "output-link is-play" : "output-link", attrs: { href, title: `${label} on the run page` } }, [
    el("span", { class: still ? "output-still" : "output-still is-blank" }, [still, cueNode]),
    strip,
  ]);
}

// A text run (output.text, Markdown) on a card: its title and the excerpt recorded at import, as plain text (no fetch),
// in a tile as tall as any other card's output; with `href` the tile links to the run.
export function textCard(out, href = null) {
  const body = [out.title ? el("strong", { class: "text-tile-title", text: out.title }) : null, el("span", { class: "text-tile-excerpt", text: out.excerpt || "" })];
  return href ? el("a", { class: "text-tile", attrs: { href, title: "Read the run" } }, body) : el("div", { class: "text-tile" }, body);
}

// The run's own summary (`run.summary`: one to three plain sentences on what it made) as a card's blurb, in full, as
// plain text (textContent). Capped at ~`limit` characters with "…" (the whole text then in the tooltip) in case a long
// one slips through. Null when the run has none.
export function summaryBlurb(run, limit = 240) {
  const flat = plainSummary(run.summary);
  if (!flat) return null;
  const cut = flat.length > limit;
  const text = cut ? `${flat.slice(0, limit).replace(/\s+\S*$/, "").replace(/[\s,;:.-]+$/, "")}…` : flat;
  return el("p", { class: "run-blurb", text, attrs: cut ? { title: flat } : {} });
}

// A summary as one line of plain text. Older summaries were Markdown, so block markers, emphasis, code ticks and link or
// image syntax are dropped (like text.py's plain()); a plain sentence passes through unchanged.
export function plainSummary(md) {
  if (!md) return "";
  return md.split("\n").filter((line) => !/^\s*(```|~~~|[-*_=|:]{3,}\s*$)/.test(line))
    .map((line) => line.replace(/^\s{0,3}(#{1,6}\s+|>\s?|[-*+]\s+(\[[ xX]\]\s+)?|\d+[.)]\s+)/, "")
      .replace(/!?\[([^\]]*)\]\([^)]*\)/g, "$1").replace(/\*{1,3}|_{2,3}|~~|`+/g, ""))
    .join(" ").replace(/\s+/g, " ").trim();
}

// A text run's Markdown as an article. The file is fetched and rendered by markdown.js (loaded on first use: it carries
// the Markdown parser, which only text runs and transcripts need), which builds DOM nodes and keeps raw HTML as text.
// `full` (the run page) shows it at reading width with a download link; otherwise it sits in a scrollable box (compare).
export function textArticle(out, base, { full = false } = {}) {
  const article = el("article", { class: "prose" }, [el("p", { class: "msg", text: "Loading…" })]);
  Promise.all([getText(base + out.text), import("./markdown.js")])
    .then(([source, { renderMarkdown }]) => renderMarkdown(article, source))
    .catch((err) => article.replaceChildren(el("p", { class: "msg", text: `Could not load the text: ${err.message}` })));
  if (!full) return el("div", { class: "prose-box" }, [article]);
  const name = out.text.split("/").pop();
  const facts = [out.words != null ? `${fmtNum(out.words)} words` : null, fmtBytes(out.bytes)].filter(Boolean).join(" · ");
  return el("div", { class: "prose-page" }, [
    article,
    el("p", { class: "prose-foot" }, [el("span", { text: facts }), el("a", { text: `download ${name}`, attrs: { href: base + out.text, download: name } })]),
  ]);
}

// A run's output wherever it is shown, as an array of nodes: the kind step's own error (if any), then
// the media gallery, the text, the game or page in the sandbox, or the "no output" message.
// Games and pages start on a click (a thumbnail with a play button) unless `autoplay` (the click was
// opening the row or the window); `frameClass` is the wrapper of an autoplaying frame. `compact` (the classic cards)
// shows media as one hero with a thumbnail strip instead of the full captioned gallery, its image linking to `href`;
// `full` (the run page) shows the gallery at full size. `link` (the lanes cards and compare columns: the run page's
// URL) shows the output as one link there (outputLink(); a text as its title/excerpt tile), never playing in place.
export function renderOutput(run, base, { autoplay = false, frameClass = "game-frame", compact = false, href = null, full = false, tools = null, link = null } = {}) {
  const out = run.output;
  // A failed kind step is an error everywhere. When the output worked, `error` holds what the step skipped (a duplicate
  // file, an unreadable extra): a quiet note on the run page (`full`), and nothing on cards.
  const nodes = !out?.error ? [] : !out.ok ? [el("p", { class: "run-error", text: out.error })]
    : full ? [el("p", { class: "run-note", text: out.error })] : [];
  if (!out?.ok) return [...nodes, el("p", { class: "msg", text: kindUi(run.kind).none })];
  if (link) return [...nodes, out.text ? textCard(out, link) : outputLink(run, base, link)];
  if (out.items) return [...nodes, compact ? mediaCard(out.items || [], base, href) : mediaGallery(out.items || [], base, { full, tools })];
  if (out.text) return [...nodes, compact ? textCard(out, href) : textArticle(out, base, { full })];
  const entry = base + out.entry;
  return [...nodes, autoplay ? el("div", { class: frameClass }, [sandboxedGame(entry)]) : buildGameFrame(entry, run.thumb ? base + run.thumb : null)];
}

// Whether a run's output is a game or page that has its own full-screen window (play.html).
export function isPlayable(run) {
  return outputOk(run) && !run.output.items && !run.output.text;
}
