"""art-crit import: publish run directories (the runner's `<batch>/<run id>/`, see SPEC.md "Run directory")
to the site: clean + secret-scan, copy, then rebuild."""

import base64
import binascii
import json
import shutil
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

from . import clean, site
from .kinds import KINDS, StageContext
from .kinds.media import thumbnail
from .summary import summary_of
from .util import CritError, mask

# Files under work/ that are never part of the copied source (editor cache, npm packages: bundled into a
# packaged page, never published as source). export_presets.cfg is one of a Godot project's own files and stays.
SOURCE_SKIP = {".DS_Store", ".godot", "node_modules", ".pi", ".grok"}  # .pi, .grok: a run's MCP config
# A transcript image (the agent reading a render or screenshot) bigger than this is published as a JPEG at most
# IMAGE_WIDTH wide: pi keeps the full file as base64, and a run that looks at its renders ten times made a 15 MB
# conversation.json (Pages takes at most 25 MiB per file). The run directory keeps the originals.
IMAGE_MAX_BYTES = 48 * 1024
IMAGE_WIDTH = 800
# A --ref file bigger than this is published as a JPEG at most REF_WIDTH wide (the viewer shows them as
# thumbnails beside the page's prompt; Pages takes at most 25 MiB per file). Still too big -> the import aborts.
REF_MAX_BYTES = 8 * 1024 * 1024
REF_WIDTH = 2048


def shrink_images(obj):
    """Every image block ({"type": "image", "data": base64}) over IMAGE_MAX_BYTES -> a JPEG thumbnail, recording the
    original's type and size like Claude Code's converted images (whose `sourceMimeType` marks them done). Without
    ffmpeg the block keeps only that record, no data. Returns the number of images shrunk."""
    if isinstance(obj, list):
        return sum(shrink_images(v) for v in obj)
    if not isinstance(obj, dict):
        return 0
    n = sum(shrink_images(v) for v in obj.values())
    data = obj.get("data")
    if obj.get("type") != "image" or not isinstance(data, str) or "sourceMimeType" in obj or len(data) * 3 // 4 <= IMAGE_MAX_BYTES:
        return n
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        return n  # not plain base64: left as is (the viewer shows only a caption for it)
    thumb = thumbnail(raw, IMAGE_WIDTH)
    obj.update(mimeType="image/jpeg", sourceMimeType=obj.get("mimeType"), bytes=len(raw))
    if thumb:
        obj["data"] = base64.b64encode(thumb).decode()
    else:
        del obj["data"]
    return n + 1


def write_cleaned(src, dest, fmt, rewrites, redact, batch, raw=None):
    """Clean src's text (or `raw`, text already read from it) per `fmt` (json / jsonl / text) and write it to dest,
    tracking rewrites/hits on `batch`."""
    try:
        raw = raw if raw is not None else src.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)
        return
    images = []  # image data, set aside from rewriting and the secret scan, restored before writing
    if fmt == "json":
        text, n = clean.clean_json(raw, rewrites, images)
    elif fmt == "jsonl":
        text, n = clean.clean_jsonl(raw, rewrites, images)
    else:
        text, n = clean.clean_plain(raw, rewrites)
    batch.rewritten += n
    if redact:
        text, k = clean.redact_secrets(text)
        batch.redacted += k
    else:
        rel = dest.relative_to(batch.run_dir)
        for line, secret in clean.scan_secrets(text):
            batch.hits.append((batch.run_id, rel.as_posix(), line, secret))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(clean.restore_images(text, images), encoding="utf-8")


def final_prompt(run_dir):
    """The brief the agent was sent: the cleaned transcript's first user message."""
    convo = run_dir / "session" / "conversation.json"
    if not convo.is_file():
        return None
    for entry in json.loads(convo.read_text()):
        msg = entry.get("message") or {}
        if msg.get("role") == "user":
            content = msg.get("content") or ""
            return content if isinstance(content, str) else "".join(b.get("text", "") for b in content if b.get("type") == "text")
    return None


def stage_session(harness_dir, run_dir, rewrites, redact, batch):
    """The transcript (and the harness's stderr, when it wrote any) -> runs/<id>/session/."""
    session = {}
    for key, fname, fmt in (("conversation", "conversation.json", "json"), ("stderr", "stderr.txt", "text")):
        src = harness_dir / fname
        if src.is_file() and src.stat().st_size:
            raw = None
            if key == "conversation":
                entries = json.loads(src.read_text(encoding="utf-8"))
                if shrink_images(entries):
                    raw = json.dumps(entries, indent=2) + "\n"
            write_cleaned(src, run_dir / "session" / fname, fmt, rewrites, redact, batch, raw)
            session[key] = f"session/{fname}"
    return session or None


def stage_source(work_dir, run_dir, kind, rewrites, redact, batch):
    """What the agent wrote -> runs/<id>/source/ (the kind may leave files out, e.g. rendered frames)."""
    if not work_dir.is_dir():
        return None
    files = []
    for src in sorted(work_dir.rglob("*")):
        rel = src.relative_to(work_dir)
        if src.is_dir() or rel.parts[0] in SOURCE_SKIP | {"references"} or src.name in SOURCE_SKIP or not kind.keep_source(rel, src):
            continue
        write_cleaned(src, run_dir / "source" / rel, "text", rewrites, redact, batch)
        files.append(rel.as_posix())
    return {"root": "source/", "files": sorted(files)} if files else None


def stage_run(src, slug, tmp_root, docs_root, rewrites, redact, allow_threads, known_engines):
    """One run directory -> a staged copy of runs/<id>/ under tmp_root (nothing is written to the site yet)."""
    record = json.loads((src / "run.json").read_text())
    # Re-importing older Muse batches upgrades their zero (unreported) cost from the
    # original export without changing the archived run or re-running the agent.
    if record.get("harness", {}).get("name") == "muse-code" and not record["metrics"].get("cost_estimated"):
        from .harness import MuseCode, _read_muse_export, muse_metrics

        export = src / "harness" / "export.json"
        if export.is_file():
            estimate = MuseCode().finish(src / "harness", record["model"], muse_metrics(_read_muse_export(export)))
            for key in ("cost_usd", "cost_estimated", "cost_estimate_proxy"):
                if key in estimate and estimate.get("cost_estimated"):
                    record["metrics"][key] = estimate[key]
    kind = KINDS[record["kind"]]()
    run_id = record["id"]
    run_dir = tmp_root / run_id
    run_dir.mkdir(parents=True)
    batch = SimpleNamespace(rewritten=0, redacted=0, hits=[], run_dir=run_dir, run_id=run_id)

    ctx = StageContext(docs_root, slug, run_id, allow_threads, known_engines,
                       write_text=lambda s, d: write_cleaned(s, d, "text", rewrites, redact, batch))
    result = record["output"]
    staged = kind.stage(src / "output", run_dir, ctx) if result and result["ok"] else None
    output = None
    if result:
        output = {"kind": result["kind"], **(staged.fields if staged else {}),
                  "ok": result["ok"], "verified": result["verified"], "error": result["error"]}
    engine_sha, engine_files = staged.engine if staged and staged.engine else (None, None)

    session = stage_session(src / "harness", run_dir, rewrites, redact, batch)
    source = stage_source(src / "work", run_dir, kind, rewrites, redact, batch)

    run_json = {
        **{k: v for k, v in record.items() if k != "output"},
        "page": slug,
        "thumb": staged.thumb if staged else None,
        "output": output,
        # read back from the cleaned, scanned transcript just written (run.json itself isn't scanned)
        "summary": summary_of(run_dir) if session else None,
        "session": session,
        "source": source,
    }
    (run_dir / "run.json").write_text(json.dumps(run_json, indent=2) + "\n")
    n_bytes = sum(p.stat().st_size for p in run_dir.rglob("*") if p.is_file())
    return SimpleNamespace(
        run_id=run_id,
        kind=record["kind"],
        run_dir=run_dir,
        engine_sha=engine_sha,
        engine_files=engine_files,
        bytes=n_bytes,
        rewritten=batch.rewritten,
        redacted=batch.redacted,
        hits=batch.hits,
    )


def run_dirs_of(path):
    """A run directory, or a batch directory (the run directories inside it, in name order)."""
    if (path / "run.json").is_file():
        return [path]
    found = sorted(d for d in path.iterdir() if d.is_dir() and (d / "run.json").is_file())
    if not found:
        raise CritError(f"no run.json in {path} or its subdirectories: expected a run directory or a batch directory")
    return found


def cmd_import(config, path, page=None, title=None, redact=False, allow_threads=False, dry_run=False):
    """Publish the runs under `path` into docs/. Returns the paths it wrote (relative to the root, for
    `cmd_publish`), so a caller that pushes can commit just this import and not the rest of the working copy."""
    path = Path(path).resolve()
    if not path.is_dir():
        raise CritError(f"not a directory: {path}")
    sources = run_dirs_of(path)
    records = [json.loads((d / "run.json").read_text()) for d in sources]
    kinds = {r["kind"] for r in records}
    if len(kinds) > 1:
        raise CritError(f"{path} holds runs of different kinds ({', '.join(sorted(kinds))}); import them separately")
    [kind] = kinds
    slug = page or records[0]["page"]
    docs_root = config.root / "docs"
    page_path = docs_root / "data" / slug / "page.json"
    page_kind = json.loads(page_path.read_text()).get("kind", "godot") if page_path.is_file() else kind
    if page_kind != kind:
        raise CritError(f"page {slug!r} holds {page_kind} runs, this import has {kind} runs; use another --page")
    (docs_root / "data").mkdir(parents=True, exist_ok=True)
    (docs_root / "engines").mkdir(parents=True, exist_ok=True)
    rewrites = config.rewrites
    # The originating prompt (not the brief given to the agents), in the batch directory; cleaned and scanned like everything else.
    prompt_path = sources[0].parent / "prompt.md"
    prompt = clean.rewrite_text(prompt_path.read_text().strip(), rewrites)[0] if prompt_path.is_file() else None
    if prompt and redact:
        prompt = clean.redact_secrets(prompt)[0]

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        results = []
        written = []  # what this import touches, relative to the root (see the docstring)
        known_engines = set()
        for src in sources:
            r = stage_run(src, slug, tmp_root, docs_root, rewrites, redact, allow_threads, known_engines)
            if r.engine_files is not None:
                known_engines.add(r.engine_sha)
            results.append(r)

        all_hits = [h for r in results for h in r.hits]
        if prompt and not redact:
            all_hits += [("page", "prompt.md", line, secret) for line, secret in clean.scan_secrets(prompt)]
        if all_hits and not redact:
            for run_id, rel, line, secret in all_hits:
                print(f"secret: {run_id}/{rel}:{line}: {mask(secret)}", file=sys.stderr)
            raise CritError(f"{len(all_hits)} possible secret(s) found before writing anything; use --redact to continue")

        for r in results:
            status = "n/a" if r.engine_sha is None else ("stored" if r.engine_files is not None else "reused")
            tag = "[dry-run] " if dry_run else ""
            engine_note = f" {r.engine_sha}" if r.engine_sha else ""
            secret_note = r.redacted if redact else len(r.hits)
            print(
                f"{tag}{r.run_id}: engine {status}{engine_note}, {r.bytes} bytes, "
                f"{r.rewritten} paths rewritten, {secret_note} secret hits"
            )

        if dry_run:
            return []

        final = next((p for r in results if (p := final_prompt(r.run_dir))), None)

        # The batch's --ref copies (runner.REF_DIR), published beside the runs so the viewer can show them
        # (references/ is the one work/ subtree the run staging skips). A fresh copy per import: re-importing
        # replaces the set. The originals stay in the batch; the viewer shows them through <img> only.
        refs_src = sources[0].parent / "references"
        if refs_src.is_dir():
            refs_dir = docs_root / "data" / slug / "references"
            if refs_dir.is_dir():
                shutil.rmtree(refs_dir)
            refs_dir.mkdir(parents=True)
            for ref in sorted(p for p in refs_src.iterdir() if p.is_file()):
                raw = ref.read_bytes()
                if len(raw) > REF_MAX_BYTES:
                    small = thumbnail(raw, REF_WIDTH)
                    if small:
                        raw = small
                if len(raw) > 20 * 1024 * 1024:
                    raise CritError(f"reference {ref.name} is {len(raw)} bytes even re-encoded; Pages takes at most 25 MiB per file")
                (refs_dir / ref.name).write_bytes(raw)

        for r in results:
            if r.engine_sha and r.engine_files is not None:
                engine_dir = docs_root / "engines" / r.engine_sha
                if not engine_dir.is_dir():
                    engine_dir.mkdir(parents=True)
                    for name, content in r.engine_files.items():
                        (engine_dir / name).write_bytes(content)
                    written.append(engine_dir)
            target = docs_root / "data" / slug / "runs" / r.run_id
            if target.is_dir():
                shutil.rmtree(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(r.run_dir), str(target))
            written.append(target)

        page_json = json.loads(page_path.read_text()) if page_path.is_file() else {"slug": slug}
        page_json["kind"] = kind
        if title:
            page_json["title"] = title
        if prompt:
            page_json["prompt"] = prompt
        if final:
            page_json["final_prompt"] = final
        page_path.write_text(json.dumps(page_json, indent=2) + "\n")

        # page.json and any references/ copies, plus rebuild's pages.json: the run directories above are the rest.
        written.append(page_path)
        if refs_src.is_dir():
            written.append(docs_root / "data" / slug / "references")
        written.append(docs_root / "data" / "pages.json")
        site.rebuild(config.root)
    return [p.relative_to(config.root) for p in written]
