"""Regenerate page.json / pages.json from runs/*/run.json, and GC unreferenced
engines. Also `rm` and `list`, which both end by calling rebuild()."""

import json
import re
import shutil
import sys
from datetime import datetime, timedelta, timezone

from .kinds.media import add_thumbs, write_thumb
from .summary import summary_of
from .util import CritError, effort_sort_key, title_from_slug


def _ended_at(run):
    started = datetime.strptime(run["started_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ms = (run.get("metrics") or {}).get("duration_ms") or 0
    return (started + timedelta(milliseconds=ms)).strftime("%Y-%m-%dT%H:%M:%SZ")


def cover_of(run):
    """The picture that stands for a run on the home page: its `cover` (a path chosen in covers.json), else its
    `thumb`; None for a run kept off the home page (`cover: false`)."""
    return run.get("thumb") if run.get("cover") is None else run["cover"] or None


def _pick_thumb(runs):
    """The most recent run (by started_at, then effort order) that has a cover picture."""
    for run in sorted(runs, key=effort_sort_key, reverse=True):
        if cover_of(run):
            return run
    return None


def backfill_thumbs(run_dir, run):
    """Thumbnails for a run published before they existed (ADR-0029), made from its published files: a godot/web run's
    full-size `thumb.png` becomes `thumb.jpg`, media items get `media/<stem>.thumb.jpg`. Nothing to do on a current
    run. Returns whether run.json changed."""
    before = json.dumps(run, sort_keys=True)
    items = (run.get("output") or {}).get("items")
    if items:
        run["thumb"] = add_thumbs(run_dir, items)
    elif run.get("thumb") == "thumb.png" and write_thumb(run_dir / "thumb.png", run_dir / "thumb.jpg"):
        (run_dir / "thumb.png").unlink()
        run["thumb"] = "thumb.jpg"
    return json.dumps(run, sort_keys=True) != before


def backfill_summary(run_dir, run):
    """`summary` for a run published before it existed, from its published (cleaned) transcript; null when there is
    none. Never redone once the key is there. Returns whether run.json changed."""
    if "summary" in run:
        return False
    run["summary"] = summary_of(run_dir) if (run.get("session") or {}).get("conversation") else None
    return True


def apply_ranking(page_dir, runs):
    """Set each run's `rank` from data/<slug>/ranking.json (null when unranked), dropping entries
    for runs that no longer exist (e.g. after `art-crit rm`)."""
    path = page_dir / "ranking.json"
    ranking = json.loads(path.read_text()) if path.is_file() else {"ranks": {}}
    ids = {r["id"] for r in runs}
    kept = {k: v for k, v in ranking.get("ranks", {}).items() if k in ids}
    if path.is_file() and kept != ranking.get("ranks"):
        path.write_text(json.dumps({**ranking, "ranks": kept}, indent=2) + "\n")
    for run in runs:
        run["rank"] = kept.get(run["id"])


def load_covers(page_dir):
    """data/<slug>/covers.json (hand-curated, or written by the local `api/cover`):
    {"thumbs": {run: path}, "page": {"run": id, "image": path?}, "covers": {run: path | false}}.
    Raises CritError when the file isn't a JSON object."""
    path = page_dir / "covers.json"
    if not path.is_file():
        return {}
    try:
        covers = json.loads(path.read_text())
    except ValueError as e:
        raise CritError(f"{path}: not valid JSON ({e})")
    if not isinstance(covers, dict):
        raise CritError(f"{path}: expected a JSON object")
    return covers


def cover_section(covers, key):
    """covers.json's `thumbs` or `covers` as a dict ({} when it's missing or isn't an object)."""
    section = covers.get(key)
    return section if isinstance(section, dict) else {}


def _covers_or_none(page_dir):
    """What `rebuild` reads: a broken covers.json is reported and ignored, so it can't stop every page's rebuild."""
    try:
        return load_covers(page_dir)
    except CritError as e:
        print(f"warning: {e}; ignoring it", file=sys.stderr)
        return {}


def _is_file(page_dir, run_id, rel):
    return isinstance(rel, str) and (page_dir / "runs" / run_id / rel).is_file()


def apply_covers(page_dir, runs, covers):
    """Apply covers.json's overrides to the runs (in page.json only; run.json stays the record):
    `thumbs` replaces a run's `thumb` (its main picture on cards and tables) and marks it `thumb_override: true`,
    `covers` sets `cover`, the picture the home page may use for the run instead (a path), or false to keep the run
    off the home page. Entries for runs or files that don't exist are ignored."""
    thumbs, home = cover_section(covers, "thumbs"), cover_section(covers, "covers")
    for run in runs:
        thumb = thumbs.get(run["id"])
        if _is_file(page_dir, run["id"], thumb):
            run["thumb"] = thumb
            run["thumb_override"] = True
        cover = home.get(run["id"])
        if cover is False or _is_file(page_dir, run["id"], cover):
            run["cover"] = cover


def page_cover(page_dir, runs, covers):
    """The page's own pick for its home-page picture: {"run": id, "image": path} from covers.json's `page`, or None
    (use the default pick). `image` falls back to the run's cover picture. Ignored when the run is failed or gone,
    or the image is."""
    pick = covers.get("page")
    run = next((r for r in runs if isinstance(pick, dict) and r["id"] == pick.get("run") and not run_failed(r)), None)
    if not run:
        return None
    image = pick.get("image") or cover_of(run)
    return {"run": run["id"], "image": image} if _is_file(page_dir, run["id"], image) else None


def rebuild(root):
    docs = root / "docs"
    data_dir = docs / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    referenced_engines = set()
    pages = []

    for page_dir in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        runs = []
        runs_dir = page_dir / "runs"
        if runs_dir.is_dir():
            for run_dir in sorted(runs_dir.iterdir()):
                rj = run_dir / "run.json"
                if rj.is_file():
                    run = json.loads(rj.read_text())
                    if backfill_thumbs(run_dir, run) | backfill_summary(run_dir, run):
                        rj.write_text(json.dumps(run, indent=2) + "\n")
                    runs.append(run)
        if not runs:
            shutil.rmtree(page_dir)
            continue

        runs.sort(key=effort_sort_key)
        apply_ranking(page_dir, runs)
        covers = _covers_or_none(page_dir)
        apply_covers(page_dir, runs, covers)
        (page_dir / "results.json").unlink(missing_ok=True)
        for run in runs:
            output = run.get("output")
            if output and output.get("engine"):
                referenced_engines.add(output["engine"])

        slug = page_dir.name
        page_json_path = page_dir / "page.json"
        existing = json.loads(page_json_path.read_text()) if page_json_path.is_file() else {}
        page = {
            "slug": slug,
            "title": existing.get("title") or title_from_slug(slug),
            "kind": existing.get("kind", "godot"),
            "prompt": existing.get("prompt", ""),
            "final_prompt": existing.get("final_prompt"),
            "created": existing.get("created") or min(r["started_at"] for r in runs),
            "updated": max(_ended_at(r) for r in runs),
            "runs": runs,
        }
        refs_dir = page_dir / "references"  # --ref files published by import; the viewer lists them by name
        if refs_dir.is_dir():
            page["references"] = sorted(p.name for p in refs_dir.iterdir() if p.is_file())
        picked = page_cover(page_dir, runs, covers)  # the owner's pick for the home page, else the viewer chooses (see Covers)
        if picked:
            page["cover"] = picked
        page_json_path.write_text(json.dumps(page, indent=2) + "\n")

        thumb_run = _pick_thumb(runs)
        pages.append(
            {
                "slug": slug,
                "title": page["title"],
                "kind": page["kind"],
                "n_runs": len(runs),
                "models": sorted({r["model"] for r in runs}),
                "updated": page["updated"],
                "thumb": f"data/{slug}/runs/{picked['run']}/{picked['image']}" if picked
                else f"data/{slug}/runs/{thumb_run['id']}/{cover_of(thumb_run)}" if thumb_run else None,
            }
        )

    pages.sort(key=lambda p: p["updated"], reverse=True)
    (data_dir / "pages.json").write_text(json.dumps(pages, indent=2) + "\n")

    engines_dir = docs / "engines"
    if engines_dir.is_dir():
        for d in engines_dir.iterdir():
            if d.is_dir() and d.name not in referenced_engines:
                shutil.rmtree(d)


def run_failed(run):
    """Whether a run is broken in any of the three senses (ADR-0018): the agent didn't finish it
    (`state` isn't complete), the kind step recorded nothing or failed (`output` / `output.ok`),
    or the check failed (`output.verified`). An unchecked run (`verified` null) isn't failed."""
    if run.get("state") != "complete":
        return True
    output = run.get("output")
    if not output:
        return True
    return output.get("ok") is False or output.get("verified") is False


def _failure_reason(run):
    if run.get("state") != "complete":
        return f"agent {run.get('state')}"
    if not run.get("output"):
        return "no output"
    if run["output"].get("ok") is False:
        return "kind step failed"
    return "not verified"


def cmd_rm(root, slug, run_id=None, failed=False, yes=False):
    page_dir = root / "docs" / "data" / slug
    if not page_dir.is_dir():
        raise CritError(f"no such page: {slug}")
    if failed:
        if run_id is not None:
            raise CritError("--failed takes no run id: it removes every failed run on the page")
        runs_dir = page_dir / "runs"
        doomed = []
        if runs_dir.is_dir():
            for run_dir in sorted(runs_dir.iterdir()):
                rj = run_dir / "run.json"
                if rj.is_file() and run_failed(json.loads(rj.read_text())):
                    doomed.append(run_dir.name)
        if not doomed:
            print(f"no failed runs on {slug}")
            return 0
        runs = {d: json.loads((runs_dir / d / "run.json").read_text()) for d in doomed}
        print(f"failed runs on {slug}:")
        for d in doomed:
            print(f"  {d}\t{runs[d]['model']}\t{runs[d]['effort']}\t{_failure_reason(runs[d])}")
        if not yes:
            answer = input(f"Remove {len(doomed)} run{'s' if len(doomed) != 1 else ''}? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("aborted")
                return 1
        for d in doomed:
            shutil.rmtree(runs_dir / d)
            print(f"removed run {slug}/{d}")
        rebuild(root)
        return 0
    if run_id is None:
        shutil.rmtree(page_dir)
        print(f"removed page {slug}")
    else:
        run_dir = page_dir / "runs" / run_id
        if not run_dir.is_dir():
            raise CritError(f"no such run: {slug}/{run_id}")
        shutil.rmtree(run_dir)
        print(f"removed run {slug}/{run_id}")
    rebuild(root)
    return 0


def cmd_rename(root, old, new, title=None):
    """Move a page to a new slug. The slug is also each run.json's `page`; a title that was
    only derived from the old slug follows it, any other title stays unless `title` is given."""
    data_dir = root / "docs" / "data"
    old_dir, new_dir = data_dir / old, data_dir / new
    if not old_dir.is_dir():
        raise CritError(f"no such page: {old}")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", new):
        raise CritError(f"bad slug {new!r}: use lowercase letters, digits and single hyphens")
    if new_dir.exists():
        raise CritError(f"page already exists: {new}")
    old_dir.rename(new_dir)
    for rj in new_dir.glob("runs/*/run.json"):
        run = json.loads(rj.read_text())
        run["page"] = new
        rj.write_text(json.dumps(run, indent=2) + "\n")
    page_path = new_dir / "page.json"
    page = json.loads(page_path.read_text()) if page_path.is_file() else {}
    if title or page.get("title") in (None, title_from_slug(old)):
        page["title"] = title or title_from_slug(new)
    page_path.write_text(json.dumps({**page, "slug": new}, indent=2) + "\n")
    rebuild(root)
    print(f"renamed page {old} -> {new}")
    return 0


def cmd_list(root):
    pages_json = root / "docs" / "data" / "pages.json"
    if not pages_json.is_file():
        print("no pages")
        return 0
    for p in json.loads(pages_json.read_text()):
        print(f"{p['slug']}\t{p['n_runs']} runs\tupdated {p['updated']}\t{', '.join(p['models'])}")
        results = json.loads((root / "docs" / "data" / p["slug"] / "page.json").read_text())["runs"]
        for r in results:
            verified = {True: "yes", False: "no", None: "?"}[(r.get("output") or {}).get("verified")]
            print(f"  {r['id']}\t{r['effort']}\t{r['model']}\tverified={verified}")
    return 0
