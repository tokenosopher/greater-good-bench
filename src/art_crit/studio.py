"""The video studio (docs/studio.html, local only; SPEC.md "Video studio", ADR-0034): pick a template, fill its slots with
runs from any page, put text cards between them, and render one video.

A spec is the studio's whole state as JSON (`check_spec` says what it may hold). `timeline` turns it into segments the
same way for the page's preview (`preview`, through `POST api/studio/plan`) and for the render (`make_studio_video`),
which records each run with video.py, draws the frames with scene/studio.js and adds a sound track from video_sound."""

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import video, video_sound
from .config import DEFAULT_SITE_URL, site_name
from .site import run_failed
from .util import CritError

FORMATS = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080)}
# together = every slot on screen at once (one shared segment); otherwise one segment per slot, in order
TEMPLATES = {
    # the three layouts of `art-crit video`
    "reveal": {"name": "Reveal", "desc": "Two to twelve models one at a time, numbered, their time and cost counting up.",
               "format": "9:16", "counts": list(range(2, 13)), "default": 4, "together": False, "badges": True, "stickers": True},
    "grid": {"name": "Grid", "desc": "Two to twelve models at once in numbered tiles, then a spotlight steps through them.",
             "format": "9:16", "counts": list(range(2, 13)), "default": 4, "together": True, "badges": True, "spotlight": True},
    "wide": {"name": "Wide", "desc": "Like Reveal in landscape: each run with its caption beside it.",
             "format": "16:9", "counts": list(range(2, 13)), "default": 4, "together": False, "badges": True, "stickers": True},
    "duel": {"name": "Head to head", "desc": "Two models side by side on the same prompt, then a vote card.",
             "format": "16:9", "labels": ["Left", "Right"], "together": True},
    "lineup": {"name": "Line-up", "desc": "Three or four models in a row, all playing at once.",
               "format": "16:9", "counts": [3, 4], "together": True, "badges": True},
    "wipe": {"name": "Wipe", "desc": "Two models on the same prompt, layered, with a divider sliding between them.",
             "format": "16:9", "labels": ["Model A", "Model B"], "together": True, "wipe": True},
    "ladder": {"name": "Effort ladder", "desc": "One model climbing from low to max effort.",
               "format": "9:16", "labels": ["low", "medium", "high", "max"], "together": False, "stickers": True},
    "countdown": {"name": "Countdown", "desc": "Five models revealed from your #5 to your #1.",
                  "format": "9:16", "labels": ["#5", "#4", "#3", "#2", "#1"], "together": False, "badges": True, "stickers": True},
    "montage": {"name": "Grid montage", "desc": "Six models in a grid behind a title.",
                "format": "1:1", "labels": ["1", "2", "3", "4", "5", "6"], "together": True, "badges": True, "title": True},
}
# where the tiles of a together template go (x, y, w, h), per format; the wipe stacks both runs in one square
TILE_BOX = {"grid": (36, 380, 1008, 1180), "duel": (60, 90, 1800, 900), "lineup": (60, 140, 1800, 800),
            "wipe": (460, 40, 1000, 1000), "montage": (40, 40, 1000, 1000)}
FINALE_BOX = {"9:16": (36, 380, 1008, 1180), "16:9": (60, 240, 1800, 790), "1:1": (40, 200, 1000, 790)}  # the Finale card's tiles
LOOKS = {
    "glow": {"label": "Glow", "bg": "#0c0b14", "fg": "#ffffff", "chip_bg": "#ffffff", "chip_fg": "#0b0b10"},
    "dark": {"label": "Dark", "bg": "#1c1b22", "fg": "#ffffff", "chip_bg": "#f9d9c4", "chip_fg": "#7a3410"},
    "accent": {"label": "Purple", "bg": "#4a2fc4", "fg": "#ffffff", "chip_bg": "#ffffff", "chip_fg": "#4a2fc4"},
    "peach": {"label": "Peach", "bg": "#f9d9c4", "fg": "#3d1a06", "chip_bg": "#1c1b22", "chip_fg": "#ffffff"},
    "light": {"label": "Light", "bg": "#ffffff", "fg": "#1c1b22", "chip_bg": "#4a2fc4", "chip_fg": "#ffffff"},
}
# `at` = how many result blocks play before the card (0 = the very start; past the last = the end). A `scene` card is
# drawn like `art-crit video`'s opening (hook) or closing (finale), always on the glow; its texts are optional overrides.
CARDS = {
    "hook": {"label": "Hook", "heading": "", "sub": "", "look": "glow", "secs": 3, "at": 0, "scene": True,
             "heading_label": "Headline", "sub_label": "Second line",
             "hint": "Every run on a moving wall, a headline and the prompt typing out. Empty: \"N AI models. Same prompt.\""},
    "finale": {"label": "Finale", "heading": "Place your vote", "sub": "", "link": "", "look": "glow",
               "secs": 5, "at": 99, "scene": True, "heading_label": "Question", "sub_label": "Line under it",
               "hint": "Every run as a numbered tile, the question and a call to vote; a crown on your #1. Empty line: \"on art-crit ↓\""},
    "title": {"label": "Title", "heading": "Which model built it best?", "sub": "Same prompt, different models", "look": "dark",
              "at": 0, "heading_label": "Title", "sub_label": "Subtitle"},
    "question": {"label": "Question", "heading": "Can a model draw this?", "sub": "", "look": "accent", "at": 0,
                 "heading_label": "Question", "sub_label": "Detail"},
    "section": {"label": "Section", "heading": "Round 2", "sub": "Max effort", "look": "light", "at": "middle",
                "heading_label": "Section name", "sub_label": "Subtitle"},
    "vote": {"label": "Vote", "heading": "Place your vote", "sub": "", "link": "", "look": "peach",
             "at": 99, "heading_label": "Question", "sub_label": "Subtitle"},
    "credits": {"label": "Credits", "heading": "Made with art-crit", "sub": "Every run, with its cost and full transcript, is on the site.",
                "look": "dark", "at": 99, "heading_label": "Heading", "sub_label": "Text"},
}
SECONDS = (2, 3, 5)  # the choices for a card's length and a still picture's
SYNC = {"together": "Start together, each stops at its end", "stretch": "Stretch all to the longest",
        "loop": "Loop the shorter ones"}
MUSIC = {"none": "None", **video_sound.STYLES}
RECORD_SECONDS = (4, 6, 8)  # the choices for how long a game, page or 3D model is recorded (4 = `art-crit video`'s pace)
TYPES = {  # what a run's output becomes in a video
    "image": {"label": "Image", "how": "still, slow zoom"},
    "video": {"label": "Video", "how": "plays its clip"},
    "model": {"label": "3D model", "how": "3D turntable"},
    "game": {"label": "Game", "how": "gameplay recording"},
    "web": {"label": "Web page", "how": "page recording"},
}
LIMITS = {"heading": 90, "sub": 280, "link": 60, "cards": 12}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def catalog(site=site_name(DEFAULT_SITE_URL)):
    """What the page offers (GET api/studio): its choices come from here, so the page and the render agree. `site` is
    the default link of the cards that have one (`[site] url` without the scheme)."""
    cards = {k: {**c, "link": site} if "link" in c else c for k, c in CARDS.items()}
    return {"templates": {k: {**t, "size": FORMATS[t["format"]]} for k, t in TEMPLATES.items()}, "looks": LOOKS,
            "cards": cards, "seconds": SECONDS, "record_seconds": RECORD_SECONDS, "sync": SYNC, "music": MUSIC, "types": TYPES, "limits": LIMITS}


def slot_labels(template, count=None):
    t = TEMPLATES[template]
    if "counts" in t:
        return [str(i + 1) for i in range(count if count in t["counts"] else t.get("default", t["counts"][0]))]
    return t["labels"]


def slot_type(run):
    """image | video | model | game | web: how the run's output plays in a video (video.make_source does the same)."""
    kind = run.get("kind") or (run.get("output") or {}).get("kind")
    items = video.items_of(run)
    if not items:
        return "game" if kind == "godot" else "web"
    if any(i["type"] == "video" for i in items):
        return "video"
    return "model" if any(i["type"] == "model" for i in items) else "image"


def clip_seconds(run, still, record=RECORD_SECONDS[0]):
    """How long a run plays: a still picture `still` seconds, a video its own length (2 to 10 s), a recording `record`."""
    kind = slot_type(run)
    if kind == "image":
        return still
    if kind == "video":
        clip = next(i for i in video.items_of(run) if i["type"] == "video")
        return round(min(10, max(2, clip.get("duration_s") or 6)), 1)
    return record


def _choice(value, options, what):
    if value not in options:
        raise CritError(f"{what} must be one of: {', '.join(map(str, options))}")
    return value


def check_spec(root, spec, complete=True):
    """The spec, checked and normalized, plus the run (or None) in each slot. `complete` = every slot must hold a run."""
    if not isinstance(spec, dict):
        raise CritError("expected a studio spec (a JSON object)")
    template = _choice(spec.get("template"), TEMPLATES, "template")
    labels = slot_labels(template, spec.get("count"))
    slots = spec.get("slots") or []
    if not isinstance(slots, list) or len(slots) > len(labels):
        raise CritError(f"{TEMPLATES[template]['name']} has {len(labels)} slots")
    slots = slots + [None] * (len(labels) - len(slots))
    pages, runs = {}, []
    for label, slot in zip(labels, slots):
        if slot is None:
            if complete:
                raise CritError(f"slot {label} is empty: fill every slot to render")
            runs.append(None)
            continue
        if not isinstance(slot, dict) or not isinstance(slot.get("page"), str) or not isinstance(slot.get("run"), str):
            raise CritError("a slot is {page, run} or null")
        slug = slot["page"]
        if slug not in pages:
            path = root / "docs" / "data" / slug / "page.json"
            if not SLUG_RE.match(slug) or not path.is_file():
                raise CritError(f"no such page: {slug}")
            pages[slug] = json.loads(path.read_text())
        run = next((r for r in pages[slug]["runs"] if r["id"] == slot["run"]), None)
        if run is None:
            raise CritError(f"no such run: {slug}/{slot['run']}")
        if run_failed(run):
            raise CritError(f"{slot['run']} failed: it has nothing to show")
        runs.append({**run, "page": slug, "page_title": pages[slug]["title"], "page_prompt": video.prompt_text(pages[slug])})
    cards = spec.get("cards") or []
    if not isinstance(cards, list) or len(cards) > LIMITS["cards"]:
        raise CritError(f"at most {LIMITS['cards']} cards")
    clean_cards = []
    for c in cards:
        if not isinstance(c, dict):
            raise CritError("a card is an object")
        kind = _choice(c.get("type"), CARDS, "card type")
        text = {}
        for key in ("heading", "sub", "link"):
            value = c.get(key) or ""
            if not isinstance(value, str) or len(value) > LIMITS[key]:
                raise CritError(f"a card's {key} is text of at most {LIMITS[key]} characters")
            text[key] = value.strip()
        at = c.get("at", 0)
        if not isinstance(at, int) or isinstance(at, bool) or at < 0:
            raise CritError("a card's place (at) is a whole number")
        clean_cards.append({"id": str(c.get("id") or len(clean_cards))[:20], "type": kind, **text,
                            "link": text["link"] if "link" in CARDS[kind] else "",
                            "look": "glow" if CARDS[kind].get("scene") else _choice(c.get("look"), LOOKS, "look"),
                            "secs": _choice(c.get("secs", 3), SECONDS, "a card's length"), "at": at})
    clean = {"template": template, "count": len(labels), "slots": slots, "cards": clean_cards,
             "still": _choice(spec.get("still", 3), SECONDS, "seconds for a still"),
             "record": _choice(spec.get("record", RECORD_SECONDS[0]), RECORD_SECONDS, "seconds for a recording"),
             "sync": _choice(spec.get("sync", "together"), SYNC, "sync"),
             "music": _choice(spec.get("music", "upbeat"), MUSIC, "music")}
    for key, default in (("labels", True), ("metrics", True)):
        clean[key] = spec.get(key, default)
        if not isinstance(clean[key], bool):
            raise CritError(f"{key} must be true or false")
    wipe = spec.get("wipe", 50)
    if not isinstance(wipe, int) or isinstance(wipe, bool) or not 0 <= wipe <= 100:
        raise CritError("wipe is a whole number from 0 to 100")
    clean["wipe"] = wipe
    return clean, runs


def timeline(spec, runs):
    """The segments in play order: [{type: card|slots|slot, start, secs, card?, slot?}] (seconds), and the total.
    Cards go before the result block their `at` names (clamped: a large `at` = the end), in list order."""
    template = TEMPLATES[spec["template"]]
    lengths = [clip_seconds(r, spec["still"], spec["record"]) if r else spec["still"] for r in runs]
    units = 1 if template["together"] else len(runs)
    segments, at = [], 0
    for u in range(units + 1):
        for card in (c for c in spec["cards"] if min(units, c["at"]) == u):
            segments.append({"type": "card", "card": card["id"], "secs": card["secs"]})
        if u < units:
            segments.append({"type": "slots", "secs": max(lengths)} if template["together"]
                            else {"type": "slot", "slot": u, "secs": lengths[u]})
    for seg in segments:
        seg["start"] = round(at, 3)
        at += seg["secs"]
    return segments, round(at, 3)


def preview(root, spec):
    """What the page's preview needs (POST api/studio/plan): the timeline, and each slot's type and length."""
    spec, runs = check_spec(root, spec, complete=False)
    segments, total = timeline(spec, runs)
    slots = [{"type": slot_type(r), "secs": clip_seconds(r, spec["still"], spec["record"])} if r else None for r in runs]
    return {"segments": segments, "total": total, "slots": slots, "labels": slot_labels(spec["template"], spec["count"])}


def scene_plan(spec, runs, clips):
    """Everything scene/studio.js needs (JSON; every string in it is shown with textContent)."""
    template = TEMPLATES[spec["template"]]
    size = FORMATS[template["format"]]
    segments, _ = timeline(spec, runs)
    cards = {c["id"]: c for c in spec["cards"]}
    frames, at = [], 0
    for seg in segments:  # seconds -> frames, each segment a whole number of them
        n = video.frames(seg["secs"])
        spot = video.spotlight("grid", seg["secs"], len(runs)) if seg["type"] == "slots" and template.get("spotlight") else None
        frames.append({**seg, "card": cards.get(seg.get("card")), "start": at, "frames": n, "spot": spot})
        at += n
    labels = slot_labels(spec["template"], spec["count"])
    infos = [video.run_info(r) for r in runs]
    stickers = video.stickers(infos) if template.get("stickers") else [None] * len(runs)
    one_page = len({r["page"] for r in runs}) == 1
    ranks = [r.get("rank") for r in runs if r.get("rank")] if one_page else []  # ranks only compare within a page
    slots = [{**info, "label": label, "frames": count, "type": slot_type(r), "page_title": r["page_title"], "sticker": sticker,
              "pick": bool(ranks) and r.get("rank") == min(ranks)}
             for r, info, label, count, sticker in zip(runs, infos, labels, clips, stickers)]
    tiles = []
    if template["together"]:
        box = TILE_BOX[spec["template"]]
        tiles = [list(box[:2]) + [box[2]]] * len(runs) if template.get("wipe") else video.tile_boxes(len(runs), box)
    title = next((c["heading"] for c in spec["cards"] if c["type"] == "title" and c["heading"]), "")
    prompt = runs[0]["page_prompt"] if one_page else ""  # the opening types the prompt only when every run shares it
    return {"mode": "studio", "layout": "studio", "size": size, "fps": video.FPS, "frames": at, "segments": frames,
            "template": {"id": spec["template"], **template}, "labels": spec["labels"], "metrics": spec["metrics"],
            "sync": spec["sync"], "wipe": spec["wipe"], "slots": slots, "tiles": tiles, "looks": LOOKS,
            "finale_tiles": video.tile_boxes(len(runs), FINALE_BOX[template["format"]]), "prompt": prompt,
            "timing": {**video.TIMING, "type_s": video.type_seconds(prompt)}, "title": title if template.get("title") else ""}


def cues(plan):
    """When each sound effect plays (seconds, kind), from the same segments as the pictures."""
    t, out, n = plan["timing"], [], len(plan["slots"])
    for seg in plan["segments"]:
        at = seg["start"] / video.FPS
        out.append((at, "cut") if at else (0, "hit"))
        card = seg["card"]
        if seg["type"] == "card" and card["type"] == "hook":
            if plan["prompt"]:
                out.append((at + t["bubble"], "pop"))
                out += [(at + t["type_from"] + k * 0.075, "tick") for k in range(int(t["type_s"] / 0.075))]
        elif seg["type"] == "card" and card["type"] == "finale":
            out += [(at + t["tiles"] + i * t["stagger"] + 0.2, "pop") for i in range(n)] + [(at + t["cta"], "pop")]
            if any(s["pick"] for s in plan["slots"]):
                out.append((at + t["pick"], "ding"))
        elif seg["type"] == "card":
            out.append((at + 0.2, "pop"))
            if card["link"]:
                out.append((at + 0.8, "pop"))
        elif seg["type"] == "slots":
            out += [(at + t["tiles"] + i * t["stagger"] + 0.2, "pop") for i in range(n)]
            if seg["spot"]:
                out += [(at + seg["spot"]["from"] + i * seg["spot"]["each"], "tick") for i in range(n)]
        else:
            out.append((at + t["name"], "pop"))
            if plan["slots"][seg["slot"]]["sticker"]:
                out.append((at + t["sticker"], "pop"))
            if plan["metrics"]:
                out += [(at + t["stats"] + k * 0.09, "tick") for k in range(int(t["count"] / 0.09))]
    return out


def describe(spec):
    """One line about a render, for the page's list of renders."""
    template = TEMPLATES[spec["template"]]
    title = next((c["heading"] for t in ("title", "hook") for c in spec["cards"] if c["type"] == t and c["heading"]), template["name"])
    return {"title": title, "template": template["name"], "format": template["format"], "slots": spec["count"]}


def renders_dir(root):
    return root / "videos" / "studio"


def renders(root):
    """The studio's videos on disk, newest first, with what each one's .json beside it says (older ones have none)."""
    folder = renders_dir(root)
    out = []
    for path in sorted(folder.glob("*.mp4"), reverse=True) if folder.is_dir() else []:
        try:
            info = json.loads(path.with_suffix(".json").read_text())
        except (OSError, ValueError):
            template = TEMPLATES.get(path.stem.rsplit("-", 1)[-1], {})
            info = {"template": template.get("name", ""), "format": template.get("format", "")}
        out.append({"name": path.name, "title": info.get("title") or path.stem, "template": info.get("template", ""),
                    "format": info.get("format", ""), "slots": info.get("slots"), "length": info.get("length"),
                    "bytes": path.stat().st_size})
    return out


def delete_render(root, name):
    """Remove one of the studio's videos (and its .json); only a name `renders` lists."""
    if not isinstance(name, str) or name not in {r["name"] for r in renders(root)}:
        raise CritError("no such video")
    path = renders_dir(root) / name
    path.unlink()
    path.with_suffix(".json").unlink(missing_ok=True)


def make_studio_video(root, spec, out_dir=None, say=print):
    """Render a complete spec into one MP4 (in <root>/videos/studio/ by default); returns its path."""
    spec, runs = check_spec(root, spec)
    video.check_tools()
    docs = root / "docs"
    out_dir = Path(out_dir) if out_dir else renders_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out = out_dir / f"{stamp}-{spec['template']}.mp4"
    with tempfile.TemporaryDirectory(prefix="art-crit-studio-") as work, video.studio(docs, work) as chrome:
        clips, done = [], {}
        for n, run in enumerate(runs):
            key = (run["page"], run["id"])
            frames_dir = Path(work) / "clips" / str(n)
            if key in done:  # the same run in two slots: record it once
                (frames_dir.parent).mkdir(exist_ok=True)
                frames_dir.symlink_to(done[key][0], target_is_directory=True)
                clips.append(done[key][1])
                continue
            say(f"recording {n + 1}/{len(runs)}: {run['model']} {run['effort']}")
            source = video.make_source(chrome, docs, run["page"], run, clip_seconds(run, spec["still"], spec["record"]), work, say)
            if source is None:
                raise CritError(f"{run['id']} has no picture, video or model to show")
            clips.append(video.extract_frames(source, frames_dir))
            done[key] = (frames_dir, clips[-1])
        plan = scene_plan(spec, runs, clips)
        wav = None
        if spec["music"] != "none":
            wav = Path(work) / "studio.wav"
            video_sound.soundtrack(cues(plan), plan["frames"] / video.FPS, wav, spec["music"])
        say("rendering")
        video.render_layout(chrome, plan, work, out, wav, say, scene="studio.html")
    # what the list of renders shows about it, next to it
    out.with_suffix(".json").write_text(json.dumps({**describe(spec), "length": timeline(spec, runs)[1]}, indent=2) + "\n")
    return out
