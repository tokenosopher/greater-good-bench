"""`art-crit video`: social-media videos that compare some runs of a page, made on this machine with ffmpeg and headless
Chrome (never published: they go to <root>/videos/, outside docs/). SPEC.md "Social videos", ADR-0032, ADR-0033.

Every run becomes one silent 1080x1080 source clip (`make_source`): its video, a turntable of its 3D model, a recording of
its game or page, or its pictures with a slow zoom. The clips are cut into frames, and each layout is drawn frame by frame
by the scene in scene/ (an animated page in Chrome: the opening, each run's card and caption, the closing question), with
a sound track from `video_sound`, straight into ffmpeg."""

import base64
import contextlib
import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from . import video_sound
from .site import run_failed
from .util import CritError

SITE_URL = "https://fenderog.com/art-crit/"
SITE_NAME = "fenderog.com/art-crit"  # what the cards say; the compare link is for the post (`compare_url`)
SIDE = 1080  # every source clip is SIDE x SIDE
FPS = 30
BG = "0x0e0e13"
LAYOUTS = {"reveal": (1080, 1920), "grid": (1080, 1920), "wide": (1920, 1080)}
LAYOUT_NAMES = {"reveal": "Vertical, one at a time", "grid": "Vertical, all at once", "wide": "Landscape, one at a time"}
MAX_RUNS = 12
SECONDS = 4  # per run, by default: short-form video moves fast
ENCODE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS)]
SILENT = [*ENCODE, "-an"]  # the source clips
SCENE = Path(__file__).with_name("scene")
MAX_IMAGES = 3


def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        raise CritError(f"ffmpeg failed: {r.stderr.strip()[-500:]}")


def join(parts, out):
    """Concatenate clips that were encoded alike without re-encoding them."""
    listing = Path(parts[0]).with_name(f"{Path(out).stem}-parts.txt")
    listing.write_text("".join(f"file '{Path(p).resolve()}'\n" for p in parts))
    ffmpeg("-f", "concat", "-safe", "0", "-i", listing, "-c:v", "copy", out)


def fit(side=SIDE):
    """The filter that fits a picture into a side x side square on the background colour."""
    return f"scale={side}:{side}:force_original_aspect_ratio=decrease,pad={side}:{side}:(ow-iw)/2:(oh-ih)/2:color={BG},setsar=1"


# ---- headless Chrome ------------------------------------------------------------------------------------------------

class Studio:
    """The site served from docs/ and a Chrome that records games and draws SVGs (`browser`, with the verify step's
    software WebGL), plus the scene served from the work folder and a Chrome that renders it (`renderer`, on the GPU:
    about 5x faster per frame)."""

    def __init__(self, origin, browser, scene, renderer):
        self.origin, self.browser, self.scene, self.renderer = origin, browser, scene, renderer

    def screenshot(self, html, size, out):
        """A picture page (HTML with no scripts), as a PNG of exactly `size`."""
        context = self.browser.new_context(viewport={"width": size[0], "height": size[1]}, java_script_enabled=False)
        try:
            page = context.new_page()
            page.set_content(html)
            page.screenshot(path=str(out))
        finally:
            context.close()


@contextlib.contextmanager
def studio(docs, work):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise CritError("videos need Playwright and Chrome: uv tool install --editable '.[verify]' (see the README)")
    from .serve import serve_in_thread

    for f in SCENE.iterdir():
        shutil.copy(f, Path(work) / f.name)
    (Path(work) / "assets").symlink_to(Path(docs).resolve() / "assets")  # the scene imports the site's runs.js
    servers = [serve_in_thread(docs), serve_in_thread(work)]
    origins = [f"http://127.0.0.1:{s.server_address[1]}" for s in servers]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"])
            renderer = p.chromium.launch(channel="chrome")
            try:
                yield Studio(origins[0], browser, origins[1], renderer)
            finally:
                renderer.close()
                browser.close()
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()


def record(studio, url, prepare, act, work, size=(1080, 1200)):
    """Open `url` in a page that is being recorded; `prepare(page)` waits until the picture is up and returns its
    bounding box, `act(page, box)` runs for the clip's length. Returns (the .webm, box); the clip is its last seconds."""
    context = studio.browser.new_context(viewport={"width": size[0], "height": size[1]}, record_video_dir=str(work),
                                         record_video_size={"width": size[0], "height": size[1]})
    try:
        page = context.new_page()
        page.goto(url)
        box = prepare(page)
        act(page, box)
    finally:
        context.close()
    return Path(page.video.path()), box


def crop_filter(box, size):
    """Crop to the recorded element's box (even sizes, inside the viewport), then fit the square."""
    x, y = max(0, int(box["x"])), max(0, int(box["y"]))
    w, h = min(int(box["width"]), size[0] - x) // 2 * 2, min(int(box["height"]), size[1] - y) // 2 * 2
    return f"crop={w}:{h}:{x}:{y},fps={FPS},{fit()}"


def record_game(studio, slug, run, seconds, work):
    """A game or page, in the same sandbox as the site (play.html), played a little: a click, then a few key presses."""
    size = (1080, 1200)

    def prepare(page):
        frame = page.locator(".play-frame iframe")
        frame.wait_for(timeout=30000)
        page.wait_for_timeout(4000)  # booting
        box = frame.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        return box

    def act(page, box):
        keys = ["ArrowRight", "Space", "ArrowLeft", "ArrowUp", "Space", "ArrowDown"]
        for i in range(int(seconds * 2)):
            page.keyboard.press(keys[i % len(keys)])
            page.wait_for_timeout(500)

    url = f"{studio.origin}/play.html?p={quote(slug)}&r={quote(run['id'])}"
    return _recorded_clip(studio, url, prepare, act, work, size, seconds)


def record_model(studio, slug, run, seconds, work):
    """A 3D model: the run page's viewer, orbited back and forth with the mouse."""
    size = (1080, 1300)

    def prepare(page):
        page.locator(".model-view .play-overlay").first.click(timeout=30000)
        stage = page.locator(".model-stage[data-loaded=true]")
        stage.wait_for(timeout=45000)
        page.evaluate("() => document.querySelectorAll('.model-hint').forEach((n) => n.remove())")  # "drag to orbit"
        box = stage.locator("canvas").bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.wheel(0, -250)  # a little closer: models are framed with room to spare
        page.wait_for_timeout(500)
        return box

    def act(page, box):
        cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(cx - 150, cy)
        page.mouse.down()
        steps = int(seconds * 20)
        for i in range(steps):
            page.mouse.move(cx - 150 + 300 * i / steps, cy)
            page.wait_for_timeout(50)
        page.mouse.up()

    url = f"{studio.origin}/run.html?p={quote(slug)}&r={quote(run['id'])}"
    return _recorded_clip(studio, url, prepare, act, work, size, seconds)


def _recorded_clip(studio, url, prepare, act, work, size, seconds):
    video, box = record(studio, url, prepare, act, work, size)
    out = Path(work) / f"{video.stem}.mp4"
    # the recording starts at page creation: the clip is the end of it, after the booting and the first click
    ffmpeg("-sseof", f"-{seconds}", "-i", video, "-t", seconds, "-vf", f"{crop_filter(box, size)},tpad=stop_mode=clone:stop_duration={seconds}", *SILENT, out)
    return out


# ---- one source clip per run ----------------------------------------------------------------------------------------

def still_clip(image, frames, out):
    """A picture held for `frames` frames with a slow zoom in (drawn on a 2x canvas so the zoom doesn't jitter)."""
    big = SIDE * 2
    zoom = f"zoompan=z='min(1+0.0005*on,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={SIDE}x{SIDE}:fps={FPS}"
    ffmpeg("-i", image, "-vf", f"{fit(big)},{zoom},format=yuv420p", "-frames:v", frames, *SILENT, out)


def video_clip(path, seconds, out):
    ffmpeg("-i", path, "-vf", f"fps={FPS},{fit()},tpad=stop_mode=clone:stop_duration={seconds}", "-t", seconds, *SILENT, out)


def items_of(run):
    return (run.get("output") or {}).get("items") or []


def pictures(run, run_dir):
    """The run's image items as paths, the owner's thumbnail pick (if it is one of them) first."""
    images = [i for i in items_of(run) if i["type"] == "image"]
    images.sort(key=lambda i: run.get("thumb") not in (i["path"], i.get("thumb")))
    return [run_dir / i["path"] for i in images[:MAX_IMAGES]]


def make_source(studio, docs, slug, run, seconds, work, say):
    """One silent SIDE x SIDE clip of `seconds` that shows the run, or None when there is nothing to show."""
    run_dir = docs / "data" / slug / "runs" / run["id"]
    out = Path(work) / f"{run['id']}.mp4"
    items = items_of(run)
    if not items and not (run.get("output") or {}).get("entry"):
        return None  # a text run: nothing to record or picture
    try:
        if not items:  # a game or page
            return record_game(studio, slug, run, seconds, work)
        video = next((i for i in items if i["type"] == "video"), None)
        if video:
            video_clip(run_dir / video["path"], seconds, out)
            return out
        if any(i["type"] == "model" for i in items):
            return record_model(studio, slug, run, seconds, work)
    except Exception as e:  # a game that won't boot, a model that won't load: fall back to its pictures
        say(f"{run['id']}: recording failed ({str(e).splitlines()[0][:120]}); using its pictures")
        if not items:
            thumb = run.get("thumb")
            return _thumb_clip(run_dir, thumb, seconds, out)
    images = pictures(run, run_dir)
    if not images:
        return None
    frames = max(1, round(seconds * FPS / len(images)))
    parts = []
    for n, image in enumerate(images):
        if image.suffix.lower() == ".svg":  # only ever through <img>, in Chrome (ADR-0004); ffmpeg can't read SVG
            png = Path(work) / f"{run['id']}-{n}.png"
            rel = quote(str(image.relative_to(docs)))
            studio.screenshot(f'<body style="margin:0;background:#fff"><img src="{studio.origin}/{rel}" '
                              'style="width:100vw;height:100vh;object-fit:contain">', (SIDE, SIDE), png)
            image = png
        part = Path(work) / f"{run['id']}-{n}.mp4"
        still_clip(image, frames, part)
        parts.append(part)
    if len(parts) > 1:
        join(parts, out)
    else:
        shutil.move(parts[0], out)
    return out


def _thumb_clip(run_dir, thumb, seconds, out):
    if not thumb or not (run_dir / thumb).is_file():
        return None
    still_clip(run_dir / thumb, round(seconds * FPS), out)
    return out


# ---- the scene: timeline, plan, rendering ---------------------------------------------------------------------------

TIMING = {  # seconds; the scene (scene/scene.js) and the sound cues (`cues`) both read these
    "hook": 3.0, "finale": 4.5,  # the opening and the closing question
    "bubble": 0.55, "type_from": 0.8,  # the prompt's bubble pops in, then the prompt types (type_s, by its length)
    "enter": 0.5, "exit": 0.28,  # a run's card springs in, then whips out at the end of its turn
    "name": 0.32, "stats": 0.78, "count": 0.9, "sticker": 1.35,  # its caption: the name, then the counting numbers
    "tiles": 0.0, "stagger": 0.07,  # every run's tile, one after another
    "question": 0.35, "cta": 1.4, "pick": 2.5,  # "Place your vote", "on art-crit", the owner's pick
}
TILE_BOX = {"reveal": (36, 380, 1008, 1180), "grid": (36, 380, 1008, 1180), "wide": (60, 240, 1800, 790)}
MAX_PROMPT = 600  # characters the opening types out


def prompt_text(page):
    """A page's prompt as the opening types it: whitespace collapsed, at most MAX_PROMPT characters."""
    prompt = " ".join((page.get("prompt") or page["title"]).split())
    return prompt if len(prompt) <= MAX_PROMPT else prompt[:MAX_PROMPT - 1].rstrip() + "…"


def run_info(run):
    """What the scene says about a run (the model id is named by the site's own runs.js)."""
    m = run.get("metrics") or {}
    return {"model": run["model"], "effort": run["effort"], "duration_s": round(m["duration_ms"] / 1000, 1) if m.get("duration_ms") else None,
            "tokens": m.get("tokens_total") or None, "cost": m.get("cost_usd") or None}  # 0 = unreported, not free


def stickers(infos):
    """A label for the runs that stand out (3 runs or more): one sticker each, the first that applies wins."""
    labels = [None] * len(infos)
    if len(infos) < 3:
        return labels
    for key, best, label in [("duration_s", min, "FASTEST"), ("cost", min, "CHEAPEST"), ("cost", max, "PRICIEST"), ("duration_s", max, "SLOWEST")]:
        values = [(i[key], n) for n, i in enumerate(infos) if i[key]]
        if len(values) >= 3 and len({v for v, _ in values}) > 1:
            n = best(values)[1]
            labels[n] = labels[n] or label
    return labels


def tile_boxes(n, box, gap=24):
    """n equal squares (x, y, side), as big as fit in `box` (x, y, w, h), in rows centred in it."""
    bx, by, bw, bh = box
    side, _, cols = max(  # the biggest tiles; on a tie, the fewest empty places
        (min((bw - gap * (c - 1)) // c, (bh - gap * (-(-n // c) - 1)) // -(-n // c)) // 2 * 2, n - c * -(-n // c), c)
        for c in range(1, n + 1))
    rows = -(-n // cols)
    y0 = by + (bh - rows * side - (rows - 1) * gap) // 2
    tiles = []
    for i in range(n):
        row, col = divmod(i, cols)
        in_row = min(cols, n - row * cols)
        x0 = bx + (bw - in_row * side - (in_row - 1) * gap) // 2
        tiles.append((x0 + col * (side + gap), y0 + row * (side + gap), side))
    return tiles


def frames(seconds):
    return round(seconds * FPS)


def timeline(layout, n, seconds):
    """The segments (type, first frame, frames, run) and the total number of frames."""
    segments, at = [], 0
    parts = [("hook", TIMING["hook"], None)]
    if layout == "grid":
        parts.append(("grid", seconds + TIMING["tiles"] + TIMING["stagger"] * n, None))
    else:
        parts += [("run", seconds, i) for i in range(n)]
    parts.append(("finale", TIMING["finale"], None))
    for kind, secs, run in parts:
        segments.append({"type": kind, "start": at, "frames": frames(secs), "run": run, "spot": spotlight(kind, secs, n)})
        at += frames(secs)
    return segments, at


def spotlight(kind, seconds, n):
    """When the grid's spotlight starts stepping through the tiles, and how long it stays on each (if there's time)."""
    if kind != "grid":
        return None
    start = TIMING["tiles"] + (n - 1) * TIMING["stagger"] + 0.6  # every tile has landed
    each = (seconds - start) / n
    return {"from": start, "each": each} if each >= 0.25 else None


def type_seconds(prompt):
    return min(1.6, max(0.6, len(prompt) / 45))


def cues(plan):
    """When each sound plays (seconds, kind), from the same timeline and timings as the pictures."""
    t, n = plan["timing"], len(plan["runs"])
    out = []
    for seg in plan["segments"]:
        at = seg["start"] / FPS
        if at:
            out.append((at, "cut"))
        if seg["type"] == "hook":
            out += [(0, "hit"), (t["bubble"], "pop")]
            out += [(t["type_from"] + k * 0.075, "tick") for k in range(int(t["type_s"] / 0.075))]
        elif seg["type"] == "run":
            out += [(at + t["name"], "pop")] + [(at + t["stats"] + k * 0.09, "tick") for k in range(int(t["count"] / 0.09))]
            if plan["runs"][seg["run"]]["sticker"]:
                out.append((at + t["sticker"], "pop"))
        else:
            if seg["type"] == "grid" or not any(s["type"] == "grid" for s in plan["segments"]):
                out += [(at + t["tiles"] + i * t["stagger"] + 0.2, "pop") for i in range(n)]
            if seg["spot"]:
                out += [(at + seg["spot"]["from"] + i * seg["spot"]["each"], "tick") for i in range(n)]
            if seg["type"] == "finale":
                out += [(at, "hit"), (at + t["cta"], "pop")]
                if any(r["pick"] for r in plan["runs"]):
                    out.append((at + t["pick"], "ding"))
    return out


def scene_plan(layout, page, runs, clips, seconds):
    """Everything scene.js needs for one layout (JSON; every string in it is shown with textContent)."""
    prompt = prompt_text(page)
    infos = [run_info(r) for r in runs]
    ranks = [r.get("rank") for r in runs if r.get("rank")]
    best = min(ranks) if ranks else None
    for info, run, label, count in zip(infos, runs, stickers(infos), clips):
        info.update(sticker=label, pick=best is not None and run.get("rank") == best, frames=count)
    segments, total = timeline(layout, len(runs), seconds)
    return {"layout": layout, "size": LAYOUTS[layout], "fps": FPS, "frames": total, "segments": segments,
            "timing": {**TIMING, "type_s": type_seconds(prompt)}, "tiles": tile_boxes(len(runs), TILE_BOX[layout]),
            "prompt": prompt, "title": page["title"], "site": SITE_NAME, "runs": infos}


def extract_frames(source, out_dir):
    """The clip as numbered JPEGs, full size (f/) and half size for tiles (s/); returns how many frames."""
    for sub, scale, q in (("f", SIDE, 3), ("s", SIDE // 2, 4)):
        (out_dir / sub).mkdir(parents=True)
        ffmpeg("-i", source, "-vf", f"scale={scale}:{scale}", "-q:v", q, out_dir / sub / "%04d.jpg")
    return len(list((out_dir / "f").glob("*.jpg")))


def render_layout(studio, plan, work, out, wav, say, scene="scene.html"):
    """Draw every frame of the plan with a scene page (scene.html, or studio.html) in Chrome and pipe the screenshots,
    with the sound track `wav` (None = a silent one), into ffmpeg."""
    layout, total = plan["layout"], plan["frames"]
    (Path(work) / f"plan-{layout}.json").write_text(json.dumps(plan))
    if wav:
        audio = ["-i", wav]
    else:  # platforms expect an audio track: a silent one
        audio = ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    w, h = plan["size"]
    page = studio.renderer.new_page(viewport={"width": w, "height": h}, color_scheme="dark")  # the logo's dark colours
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    encoder = None
    try:
        page.goto(f"{studio.scene}/{scene}?plan=plan-{layout}.json")
        try:
            page.wait_for_function("() => window.sceneReady === true", timeout=30000)
        except Exception:
            raise CritError(f"the video scene didn't load: {'; '.join(errors) or 'timed out'}")
        cdp = page.context.new_cdp_session(page)
        encoder = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-", *map(str, audio),
                                    "-map", "0:v", "-map", "1:a", *ENCODE, "-c:a", "aac", "-b:a", "160k", "-shortest",
                                    "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        for f in range(total):
            if f % (FPS * 5) == 0:
                say(f"rendering {layout}: {f * 100 // total}%")
            page.evaluate("(f) => window.renderFrame(f)", f)
            if errors:
                raise CritError(f"the video scene failed: {errors[0]}")
            shot = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": 92, "optimizeForSpeed": True})
            encoder.stdin.write(base64.b64decode(shot["data"]))
        encoder.stdin.close()
        if encoder.wait():
            raise CritError(f"ffmpeg failed: {encoder.stderr.read().decode(errors='replace').strip()[-500:]}")
    except BrokenPipeError:
        raise CritError(f"ffmpeg failed: {encoder.stderr.read().decode(errors='replace').strip()[-500:]}")
    finally:
        if encoder and encoder.poll() is None:
            encoder.kill()
        page.close()


def compare_url(slug, run_ids):
    """The site's compare page for these runs: the link to put in the post."""
    return f"{SITE_URL}compare.html?p={quote(slug)}&r={quote(','.join(run_ids))}"


# ---- entry point ----------------------------------------------------------------------------------------------------

def check_request(root, slug, run_ids, layouts, seconds):
    """(page.json, the chosen runs in order, the layouts) or a CritError; nothing is started."""
    path = root / "docs" / "data" / slug / "page.json"
    if not path.is_file():
        raise CritError(f"no such page: {slug}")
    page = json.loads(path.read_text())
    by_id = {r["id"]: r for r in page["runs"]}
    for run_id in run_ids:
        if run_id not in by_id:
            raise CritError(f"no such run: {slug}/{run_id}")
    run_ids = list(dict.fromkeys(run_ids))
    if not 2 <= len(run_ids) <= MAX_RUNS:
        raise CritError(f"a video compares 2 to {MAX_RUNS} runs, got {len(run_ids)}")
    runs = [by_id[i] for i in run_ids]
    failed = [r["id"] for r in runs if run_failed(r)]
    if failed:
        raise CritError(f"failed runs have nothing to show: {', '.join(failed)}")
    layouts = list(dict.fromkeys(layouts or LAYOUTS))
    for layout in layouts:
        if layout not in LAYOUTS:
            raise CritError(f"unknown layout {layout!r} (expected one of: {', '.join(LAYOUTS)})")
    if not 2 <= seconds <= 20:
        raise CritError("seconds per run must be between 2 and 20")
    check_tools()
    return page, runs, layouts


def check_tools():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise CritError(f"videos need {tool} on PATH")


def make_videos(root, slug, run_ids, layouts=None, seconds=SECONDS, out_dir=None, say=print, sound=True):
    """Make one video per layout of the given runs of a page; returns the files (in <root>/videos/<slug>/ by default)."""
    page, runs, layouts = check_request(root, slug, run_ids, layouts, seconds)
    docs = root / "docs"
    out_dir = Path(out_dir) if out_dir else root / "videos" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    files = []
    with tempfile.TemporaryDirectory(prefix="art-crit-video-") as work, studio(docs, work) as chrome:
        clips = []
        for n, run in enumerate(runs):
            say(f"recording {n + 1}/{len(runs)}: {run['model']} {run['effort']}")
            source = make_source(chrome, docs, slug, run, seconds, work, say)
            if source is None:
                raise CritError(f"{run['id']} has no picture, video or model to show")
            clips.append(extract_frames(source, Path(work) / "clips" / str(n)))
        for layout in layouts:
            say(f"rendering {layout} ({LAYOUT_NAMES[layout]})")
            out = out_dir / f"{stamp}-{slug}-{layout}.mp4"
            plan = scene_plan(layout, page, runs, clips, seconds)
            wav = None
            if sound:
                wav = Path(work) / f"{layout}.wav"
                video_sound.soundtrack(cues(plan), plan["frames"] / FPS, wav)
            render_layout(chrome, plan, work, out, wav, say)
            files.append(out)
    return files
