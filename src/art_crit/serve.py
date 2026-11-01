"""Serve docs/ like GitHub Pages: permissive CORS, correct .wasm/.pck types, no COOP/COEP.

Plus a local-only API (the published site never has it, so the viewer only shows ranking and
prompt-request controls when served by `art-crit serve`):
  GET api/local                 -> {"rank": true, "cover": true, "requests": true, "runs": true, "video": true}
  PUT api/rank?p=<slug>         body {"ranks": {"<run id>": 1, ...}}  (null/missing = unranked)
    -> writes docs/data/<slug>/ranking.json and rebuilds, so page.json carries each run's rank.
  PUT api/cover?p=<slug>        body {"thumb": {"run", "path"|null}} and/or {"page": {"run", "image"?}|null}
    -> your pick of a run's main thumbnail and/or the page's home-page picture, in data/<slug>/covers.json (overrides
    only: with none set the viewer's default picks apply), then rebuilds.
  GET api/studio                -> the video studio's choices (studio.catalog(): templates, looks, cards...)
  POST api/studio/plan          body = a studio spec (may have empty slots) -> its timeline, for the page's preview
  POST api/video                body {"studio": spec} -> {"job": id}: renders the video studio's video in the background
    (studio.py, SPEC.md "Video studio"); one job at a time.
  GET api/video?job=<id>        -> {"state", "step", "files", "error", "title", ...} (loopback only, no CORS headers)
  GET api/video/jobs            -> {"jobs": [running or failed renders], "renders": [the videos in videos/studio/]} (same rules)
  GET api/video/file?name=<file>  -> one of those videos (a name "renders" lists, nothing else)
  POST api/video/delete         body {"name": file} deletes that video (and its .json); {"job": id} dismisses a failed render
  GET api/requests              -> {"requests": [...], "sets": [names from art-crit.toml [sets]]}
  PUT api/requests              body {"add": {"prompt", "kind", "title"?, "note"?, "set"?}} or {"remove": "<id>"}
    -> requests.json next to docs/ (outside it, so prompt requests are never published).
  GET api/runs                  -> the runs of every batch in [run].dir (see Run monitor, ADR-0027)
  GET api/run?b=<batch>&r=<id>  -> one run: state, metrics, prompt/brief, files, transcript
  POST api/stop                 body {"batch", "run"} -> writes that run's harness/stop, which the
    `art-crit run` process that owns the agent sees within a second and kills the agent's group.
Writes need Content-Type: application/json (so another site can't send one without a CORS
preflight, which this server doesn't answer), a loopback Host (a site that rebinds its own name to
127.0.0.1 would otherwise pass the Origin check, since both headers carry its name) and, when
present, a same-host Origin. The monitor's reads (api/runs, api/run) need a loopback Host too and
are answered without Access-Control-Allow-Origin, so another website can't read them at all."""

import functools
import http.server
import json
import os
import re
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import site, studio, video
from .config import Config, site_name
from .harness import HARNESSES
from .runner import STOP_FILE
from .util import CritError
from .kinds import KINDS

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")  # a batch dir name or a run id, never a path
LOOPBACK = {"127.0.0.1", "localhost", "::1"}
MONITOR_BATCHES = 30  # newest batches listed by the run monitor
MONITOR_FILES = 200  # files per directory in a run's detail view
MONITOR_ENTRIES = 400  # transcript entries kept (a monitor reads the tail of a running run)
MONITOR_CLIP = 4000  # characters kept per string: a live pi session can carry megabytes of base64 images


def save_ranking(docs_root, slug, ranks):
    """Validate and write data/<slug>/ranking.json, then rebuild. Returns an error string or None."""
    if not SLUG_RE.match(slug or ""):
        return "bad page slug"
    runs_dir = docs_root / "data" / slug / "runs"
    if not runs_dir.is_dir():
        return f"no such page: {slug}"
    if not isinstance(ranks, dict):
        return "ranks must be an object"
    run_ids = {p.name for p in runs_dir.iterdir() if (p / "run.json").is_file()}
    clean = {}
    for run_id, rank in ranks.items():
        if run_id not in run_ids:
            return f"no such run: {run_id}"
        if rank is None:
            continue
        if not isinstance(rank, int) or isinstance(rank, bool) or not 1 <= rank <= len(run_ids):
            return f"rank for {run_id} must be a whole number from 1 to {len(run_ids)}"
        clean[run_id] = rank
    ranking = {"ranks": dict(sorted(clean.items(), key=lambda kv: kv[1])),
               "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    (docs_root / "data" / slug / "ranking.json").write_text(json.dumps(ranking, indent=2) + "\n")
    site.rebuild(docs_root.parent)
    return None


COVER_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}


def _cover_image(runs_dir, run_id, path):
    """Whether `path` is an image file inside the run's own directory (never ../, never a symlink out of it)."""
    if not isinstance(path, str) or Path(path).suffix.lower() not in COVER_EXTENSIONS:
        return False
    run_dir = (runs_dir / run_id).resolve()
    target = (run_dir / path).resolve()
    return target.is_file() and target.is_relative_to(run_dir)


def save_covers(docs_root, slug, body):
    """Set or clear the owner's cover overrides in data/<slug>/covers.json, keeping its other entries, then rebuild.
    `thumb` = {"run", "path"} (path null clears) is a run's main thumbnail; `page` = {"run", "image"?} (null clears)
    is the page's home-page picture. Returns an error string or None."""
    if not SLUG_RE.match(slug or ""):
        return "bad page slug"
    page_dir = docs_root / "data" / slug
    runs_dir = page_dir / "runs"
    if not runs_dir.is_dir():
        return f"no such page: {slug}"
    if not isinstance(body, dict) or not ({"thumb", "page"} & body.keys()):
        return "expected thumb and/or page"
    try:
        covers = site.load_covers(page_dir)
    except CritError as e:
        return f"{e}; fix or delete it first"
    run_ids = {d.name for d in runs_dir.iterdir() if (d / "run.json").is_file()}

    def check(value, field):
        """(run id, image path or None) from a {"run", field} object, or an error string."""
        run_id = value.get("run") if isinstance(value, dict) else None
        if not isinstance(run_id, str) or run_id not in run_ids:
            return "no such run"
        image = value.get(field)
        if image is not None and not _cover_image(runs_dir, run_id, image):
            return f"not an image of that run: {image}"
        return run_id, image

    if "thumb" in body:
        got = check(body["thumb"], "path")
        if isinstance(got, str):
            return f"thumb: {got}"
        run_id, image = got
        thumbs = dict(site.cover_section(covers, "thumbs"))
        if image is None:
            thumbs.pop(run_id, None)
        else:
            thumbs[run_id] = image
        covers["thumbs"] = thumbs
    if "page" in body:
        if body["page"] is None:
            covers.pop("page", None)
        else:
            got = check(body["page"], "image")
            if isinstance(got, str):
                return f"page: {got}"
            covers["page"] = {"run": got[0], **({"image": got[1]} if got[1] else {})}
    covers = {k: v for k, v in covers.items() if v}
    path = page_dir / "covers.json"
    if covers:
        path.write_text(json.dumps(covers, indent=2) + "\n")
    else:
        path.unlink(missing_ok=True)
    site.rebuild(docs_root.parent)
    return None


REQUEST_LIMITS = {"prompt": 4000, "title": 120, "note": 1000}


def _requests_file(docs_root):
    return Path(docs_root).parent / "requests.json"


def load_requests(docs_root):
    path = _requests_file(docs_root)
    return json.loads(path.read_text()) if path.is_file() else []


def model_sets(docs_root):
    try:
        return sorted(Config.load(Path(docs_root).parent).sets)
    except CritError:
        return []  # a broken art-crit.toml shouldn't break the page; `art-crit run` reports it


def change_requests(docs_root, body):
    """Add or remove one prompt request in requests.json. Returns (error or None, the request list)."""
    items = load_requests(docs_root)
    if not isinstance(body, dict):
        return "expected an object", items
    if "add" in body:
        add = body["add"]
        if not isinstance(add, dict):
            return "add must be an object", items
        req = {}
        for key, limit in REQUEST_LIMITS.items():
            value = add.get(key) or ""
            if not isinstance(value, str) or len(value.strip()) > limit:
                return f"{key} must be text of at most {limit} characters", items
            if value.strip():
                req[key] = value.strip()
        if "prompt" not in req:
            return "a prompt is required", items
        if add.get("kind") not in KINDS:
            return f"kind must be one of {', '.join(KINDS)}", items
        if add.get("set") and add["set"] not in model_sets(docs_root):
            return f"no such model set: {add['set']}", items
        if add.get("set"):
            req["set"] = add["set"]
        req = {"id": secrets.token_hex(4), "kind": add["kind"], **req,
               "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        items.append(req)
    elif "remove" in body:
        if not any(r["id"] == body["remove"] for r in items):
            return f"no such request: {body['remove']}", items
        items = [r for r in items if r["id"] != body["remove"]]
    else:
        return "expected add or remove", items
    _requests_file(docs_root).write_text(json.dumps(items, indent=2) + "\n")
    return None, items


# --- run monitor (ADR-0027): read [run].dir, ask running agents to stop ---------------------------------

_HARNESSES = {}


def _harness(name):
    """A shared harness instance for live metrics (their constructors only store settings)."""
    if name not in _HARNESSES and name in HARNESSES:
        _HARNESSES[name] = HARNESSES[name]()
    return _HARNESSES.get(name)


def runs_root(docs_root):
    """The `[run].dir` of the repo this docs/ belongs to, or None when art-crit.toml is missing/broken."""
    try:
        return Config.load(Path(docs_root).parent).run.dir
    except CritError:
        return None


def _read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def _run_dir(root, batch, run_id):
    """(batch dir, run dir) for a batch name and run id that both come from batch.json, or (None, None).
    Both are validated as plain names, so neither can walk out of the runs root."""
    if not root or not (NAME_RE.match(batch or "") and NAME_RE.match(run_id or "")):
        return None, None
    batch_dir = Path(root) / batch
    if not (batch_dir / "batch.json").is_file():
        return None, None
    return batch_dir, batch_dir / run_id


def _mtime_ms(path):
    return int(path.stat().st_mtime * 1000)


def _created_ms(path):
    """Approximate creation time: birth time on macOS, ctime elsewhere (both close enough for "elapsed")."""
    st = path.stat()
    return int((getattr(st, "st_birthtime", None) or st.st_ctime) * 1000)


def _activity_ms(harness_dir):
    """How long since anything was written to a run's harness dir (None when there's nothing yet)."""
    if not harness_dir.is_dir():
        return None
    times = [_mtime_ms(p) for p in harness_dir.iterdir() if p.is_file()]
    return int(time.time() * 1000) - max(times) if times else None


def _elapsed_ms(run_dir):
    """A running run's elapsed time (approximate: the run dir is created when its agent starts)."""
    return int(time.time() * 1000) - _created_ms(run_dir) if run_dir.is_dir() else None


def live_metrics(name, harness_dir, level):
    """A running run's live metrics in run.json's `metrics` shape, or {} when there's no session yet.
    Reuses each harness's own parser (the one the CLI's progress table polls)."""
    harness = _harness(name)
    if not harness:
        return {}
    try:
        metrics = harness.metrics(harness_dir, level)
    except Exception:  # a live session file can be mid-write, or a shape we don't know yet
        return {}
    if not metrics:
        return {}
    tokens = metrics.get("tokens") or {}
    return {"cost_usd": metrics.get("cost_usd") or 0.0, "tool_calls": metrics.get("tool_calls") or 0,
            "turns": metrics.get("turns") or 0, "tokens_total": tokens.get("total") or 0,
            "tokens_input": tokens.get("input") or 0, "tokens_output": tokens.get("output") or 0,
            "tokens_reasoning": tokens.get("reasoning") or 0, "tokens_cache_read": tokens.get("cacheRead") or 0}


def _batch_runs(batch):
    """A batch's runs that have an id. Batch dirs from before run ids existed carry `model_dir` instead
    and have no run directories, so the monitor leaves them out."""
    return [r for r in batch.get("runs") or [] if r.get("id")]


def _run_row(batch_dir, run, page_dir):
    """One batch.json run as the monitor shows it: its record when it finished, live metrics while running."""
    run_dir = batch_dir / run["id"]
    record = _read_json(run_dir / "run.json") or {}
    state = record.get("state") or run.get("state") or "queued"
    metrics = record.get("metrics") or {}
    if state == "running":  # no run.json yet: live metrics from the growing session, elapsed from the run dir
        metrics = {**live_metrics(run.get("harness"), run_dir / "harness", run.get("level")), "duration_ms": _elapsed_ms(run_dir)}
    return {"id": run["id"], "harness": run.get("harness"), "model": run.get("model"), "level": run.get("level"),
            "state": state, "metrics": metrics, "output": record.get("output"), "error": record.get("error"),
            "started_at": record.get("started_at"), "activity_ms": _activity_ms(run_dir / "harness"),
            "published": (page_dir / "runs" / run["id"] / "run.json").is_file()}


def list_batches(docs_root):
    """Every batch under [run].dir, newest first (up to MONITOR_BATCHES), with each run's state and
    live metrics. Read-only: the monitor never writes inside a batch (only `stop_run` does)."""
    root = runs_root(docs_root)
    if not root or not Path(root).is_dir():
        return []
    batches = sorted((p for p in Path(root).iterdir() if (p / "batch.json").is_file()), key=lambda p: p.name, reverse=True)
    out = []
    for batch_dir in batches[:MONITOR_BATCHES]:
        batch = _read_json(batch_dir / "batch.json") or {}
        runs = _batch_runs(batch)
        if not runs:  # an old batch dir: no run ids, nothing to monitor
            continue
        page_dir = Path(docs_root) / "data" / str(batch.get("page") or "")
        out.append({"batch": batch_dir.name, "page": batch.get("page"), "kind": batch.get("kind"),
                    "title": batch.get("title"), "prompt": batch.get("prompt"), "created": batch.get("created"),
                    "runs": [_run_row(batch_dir, run, page_dir) for run in runs]})
    return out


def _files(root, limit=MONITOR_FILES):
    """A run's work/ or output/ as {name, bytes} entries (relative names, capped)."""
    out = []
    root = Path(root)
    if not root.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            path = Path(dirpath) / name
            out.append({"name": str(path.relative_to(root)), "bytes": path.stat().st_size})
            if len(out) >= limit:
                return out
    return out


def _clip(value):
    """Recursively shrink one transcript entry: image blocks go (a live pi session holds base64 copies of
    everything the agent looked at) and long strings are cut. The run's own page shows the full thing."""
    if isinstance(value, str):
        return value if len(value) <= MONITOR_CLIP else value[:MONITOR_CLIP] + f"\n… [{len(value) - MONITOR_CLIP} more characters]"
    if isinstance(value, list):
        return [_clip(v) for v in value]
    if isinstance(value, dict):
        if str(value.get("type") or "").endswith("image"):
            return {"type": "text", "text": "[image omitted here]"}
        return {k: _clip(v) for k, v in value.items()}
    return value


def transcript(batch, run, harness_dir):
    """(entries, live, truncated): the finished conversation.json, or a running run's session converted on
    the fly. Empty for a run whose harness hasn't written a session yet (muse writes its export at exit)."""
    if (harness_dir / "conversation.json").is_file():
        entries, live = _read_json(harness_dir / "conversation.json") or [], False
    else:
        harness = _harness(run.get("harness"))
        try:
            entries = (harness.session_entries(harness_dir, batch.get("brief"), run.get("level")) or []) if harness else []
        except Exception:  # a live stream mid-line, or a shape we don't know yet
            entries = []
        live = bool(entries)
    return [_clip(e) for e in entries[-MONITOR_ENTRIES:]], live, len(entries) > MONITOR_ENTRIES


def run_detail(docs_root, batch, run_id):
    """One run for the monitor: the list row plus prompt, brief, file lists and a light transcript.
    Returns (data, error)."""
    root = runs_root(docs_root)
    batch_dir, run_dir = _run_dir(root, batch, run_id)
    if not batch_dir:
        return None, "no such batch"
    batch_data = _read_json(batch_dir / "batch.json") or {}
    run = next((r for r in _batch_runs(batch_data) if r["id"] == run_id), None)
    if run is None:
        return None, f"no such run: {run_id}"
    page_dir = Path(docs_root) / "data" / str(batch_data.get("page") or "")
    entries, live, truncated = transcript(batch_data, run, run_dir / "harness")
    return {"batch": batch_dir.name, "page": batch_data.get("page"), "kind": batch_data.get("kind"),
            "prompt": batch_data.get("prompt"), "brief": batch_data.get("brief"),
            "run": _run_row(batch_dir, run, page_dir), "transcript": entries, "live": live, "truncated": truncated,
            "files": {"work": _files(run_dir / "work"), "output": _files(run_dir / "output")}}, None


def stop_run(docs_root, batch, run_id):
    """Ask a running agent to stop: write <run>/harness/stop, which the `art-crit run` process that owns
    the agent notices within a second and turns into a kill of the agent's process group (runner.wait_agent).
    This process must not kill anything itself: it doesn't own the child. Returns an error string or None."""
    root = runs_root(docs_root)
    batch_dir, run_dir = _run_dir(root, batch, run_id)
    if not batch_dir:
        return "no such batch"
    batch_data = _read_json(batch_dir / "batch.json") or {}
    run = next((r for r in _batch_runs(batch_data) if r["id"] == run_id), None)
    if run is None:
        return f"no such run: {run_id}"
    if run.get("state") != "running":
        return f"{run_id} isn't running ({run.get('state')})"
    harness_dir = run_dir / "harness"
    if not harness_dir.is_dir():
        return "that run hasn't started its agent yet"
    (harness_dir / STOP_FILE).write_text(json.dumps(
        {"by": "local monitor", "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, indent=2) + "\n")
    return None


VIDEO_JOBS = {}  # job id -> {"state", "step", "files", "dir", "error", "title", ...}; the studio page polls it
VIDEO_LOCK = threading.Lock()


def start_video(root, body):
    """Check a studio spec, then render it in a background thread. Returns (job id, None) or (None, error)."""
    if not isinstance(body, dict) or not isinstance(body.get("studio"), dict):
        return None, "expected {studio: spec}"
    try:
        spec, runs = studio.check_spec(root, body["studio"])
        video.check_tools()
    except CritError as e:
        return None, str(e)
    with VIDEO_LOCK:
        if any(j["state"] == "running" for j in VIDEO_JOBS.values()):
            return None, "a video is already being made; wait for it to finish"
        job_id = secrets.token_hex(8)
        job = VIDEO_JOBS[job_id] = {"job": job_id, "state": "running", "step": "starting", "files": [], "dir": None,
                                    "error": None, "started": time.time(), **studio.describe(spec),
                                    "length": studio.timeline(spec, runs)[1]}

    def work():
        try:
            out = studio.make_studio_video(root, spec, say=lambda step: job.update(step=step))
            job.update(state="done", step="done", files=[out.name], dir=str(out.parent))
        except Exception as e:  # CritError, or whatever Chrome/ffmpeg raised: show it, never kill the server
            job.update(state="failed", error=str(e) or type(e).__name__)

    threading.Thread(target=work, daemon=True).start()
    return job_id, None


def video_status(job_id):
    job = VIDEO_JOBS.get(job_id)
    return {k: v for k, v in job.items() if k != "dir"} if job else None


def video_jobs(root):
    """The renders under way or failed (this server's memory), and the finished videos on disk (studio.renders)."""
    jobs = [video_status(j) for j in sorted(VIDEO_JOBS, key=lambda j: -VIDEO_JOBS[j]["started"]) if VIDEO_JOBS[j]["state"] != "done"]
    return {"jobs": jobs, "renders": studio.renders(root)}


def delete_video(root, body):
    """Delete a finished video ({name}) or dismiss a failed render ({job}). Returns an error or None."""
    if not isinstance(body, dict):
        return "expected {name} or {job}"
    if "job" in body:
        job = VIDEO_JOBS.get(body["job"])
        if not job or job["state"] == "running":
            return "no such finished render"
        VIDEO_JOBS.pop(body["job"])
        return None
    try:
        studio.delete_render(root, body.get("name"))
    except CritError as e:
        return str(e)
    for job_id in [j for j, job in VIDEO_JOBS.items() if body["name"] in job["files"]]:
        VIDEO_JOBS.pop(job_id)
    return None


def studio_plan(root, spec):
    """The preview's timeline (studio.preview), or an error."""
    try:
        return studio.preview(root, spec), None
    except CritError as e:
        return None, str(e)


class _Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # The monitor's reads carry run dirs and prompts, so they are answered without CORS headers
        # (the viewer is same-origin, and a page on another site must not be able to read them).
        if not getattr(self, "_local_only", False):
            self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def guess_type(self, path):
        p = str(path)
        if p.endswith(".wasm"):
            return "application/wasm"
        if p.endswith(".pck"):
            return "application/octet-stream"
        return super().guess_type(path)

    def _json(self, status, obj):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _loopback(self):
        return urlsplit("//" + self.headers.get("Host", "")).hostname in LOOPBACK

    def _local_json(self, status, obj):
        """Answer one of the monitor's reads: loopback only, no CORS headers (see end_headers)."""
        self._local_only = True
        if not self._loopback():
            return self._json(403, {"error": "the local API is only served on a loopback address"})
        return self._json(status, obj)

    def _write_body(self):
        """The JSON body of a local write, or None after answering the request itself."""
        if not self._loopback():
            self._json(403, {"error": "writes are only accepted on a loopback address"})
            return None
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            self._json(403, {"error": "cross-origin write refused"})
            return None
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            self._json(415, {"error": "expected application/json"})
            return None
        try:
            return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        except (ValueError, UnicodeDecodeError):
            self._json(400, {"error": "bad JSON"})
            return None

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.endswith("/api/local"):
            return self._json(200, {"rank": True, "cover": True, "requests": True, "runs": True, "video": True})
        if path.endswith("/api/video/file"):
            return self._video_file(parse_qs(urlsplit(self.path).query))
        if path.endswith("/api/video/jobs"):
            return self._local_json(200, video_jobs(Path(self.directory).parent))
        if path.endswith("/api/studio"):
            return self._local_json(200, studio.catalog(site_name(Config.load(Path(self.directory).parent).site_url)))
        if path.endswith("/api/video"):
            status = video_status(parse_qs(urlsplit(self.path).query).get("job", [None])[0])
            return self._local_json(404, {"error": "no such job"}) if status is None else self._local_json(200, status)
        if path.endswith("/api/requests"):
            return self._json(200, {"requests": load_requests(self.directory), "sets": model_sets(self.directory)})
        if path.endswith("/api/runs"):
            root = runs_root(self.directory)
            return self._local_json(200, {"dir": str(root) if root else None, "batches": list_batches(self.directory)})
        if path.endswith("/api/run"):
            query = parse_qs(urlsplit(self.path).query)
            data, error = run_detail(self.directory, query.get("b", [None])[0], query.get("r", [None])[0])
            return self._local_json(400, {"error": error}) if error else self._local_json(200, data)
        return super().do_GET()

    def _video_file(self, query):
        """One of the studio's videos, by a name studio.renders lists (loopback only, no CORS headers)."""
        self._local_only = True
        name = query.get("name", [None])[0]
        if not self._loopback():
            return self._json(403, {"error": "the local API is only served on a loopback address"})
        root = Path(self.directory).parent
        if name not in {r["name"] for r in studio.renders(root)}:
            return self._json(404, {"error": "no such video"})
        data = (studio.renders_dir(root) / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_PUT(self):
        url = urlsplit(self.path)
        if not (url.path.endswith(("/api/rank", "/api/cover", "/api/requests"))):
            return self._json(404, {"error": "not found"})
        body = self._write_body()
        if body is None:
            return
        if url.path.endswith("/api/requests"):
            error, items = change_requests(self.directory, body)
            return self._json(400, {"error": error}) if error else self._json(200, {"requests": items})
        slug = parse_qs(url.query).get("p", [None])[0]
        if url.path.endswith("/api/cover"):
            error = save_covers(Path(self.directory), slug, body)
        else:
            error = save_ranking(Path(self.directory), slug, body.get("ranks") if isinstance(body, dict) else None)
        if error:
            return self._json(400, {"error": error})
        return self._json(200, {"ok": True})

    def do_POST(self):
        url = urlsplit(self.path)
        if not url.path.endswith(("/api/stop", "/api/video", "/api/video/delete", "/api/studio/plan")):
            return self._json(404, {"error": "not found"})
        body = self._write_body()
        if body is None:
            return
        root = Path(self.directory).parent
        if url.path.endswith("/api/studio/plan"):
            self._local_only = True  # a read of local data in a POST's clothing: no CORS headers either
            plan, error = studio_plan(root, body)
            return self._json(400, {"error": error}) if error else self._json(200, plan)
        if url.path.endswith("/api/video/delete"):
            error = delete_video(root, body)
            return self._json(400, {"error": error}) if error else self._json(200, {"ok": True})
        if url.path.endswith("/api/video"):
            job, error = start_video(root, body)
            return self._json(400, {"error": error}) if error else self._json(200, {"job": job})
        if not isinstance(body, dict):
            return self._json(400, {"error": "expected an object"})
        error = stop_run(self.directory, body.get("batch"), body.get("run"))
        return self._json(400, {"error": error}) if error else self._json(200, {"ok": True})

    def log_message(self, fmt, *args):
        pass  # keep test/CLI output quiet


class _Server(http.server.ThreadingHTTPServer):
    # A page loads many ES modules concurrently. The stdlib default backlog of 5 can reset
    # some connections before handler threads accept them, leaving the viewer stuck at Loading….
    request_queue_size = 64


def build_server(docs_root, port=0):
    handler = functools.partial(_Handler, directory=str(docs_root))
    return _Server(("127.0.0.1", port), handler)


def serve_in_thread(docs_root, port=0):
    """Start serving in a daemon thread; return the server (caller shuts it down)."""
    server = build_server(docs_root, port)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def serve_forever(docs_root, port):
    server = build_server(docs_root, port)
    print(f"serving {docs_root} at http://127.0.0.1:{server.server_address[1]}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
