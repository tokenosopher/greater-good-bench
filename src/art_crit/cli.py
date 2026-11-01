"""art-crit: argparse wiring for import/list/rm/rename/retry/video/rebuild/serve/publish/run/models."""

import argparse
import subprocess
import sys
from pathlib import Path

from .config import Config, RunRequest
from .harness import HARNESSES
from .importer import cmd_import
from .kinds import KINDS
from .retry import cmd_retry
from .runner import cmd_models, cmd_run, resolve_ref
from .serve import serve_forever
from .video import LAYOUTS, SECONDS, compare_url, make_videos
from .site import cmd_list, cmd_rename, cmd_rm, rebuild
from .util import CritError


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-C", "--root", default=".", type=Path, help="repo root (site is <root>/docs)")

    parser = argparse.ArgumentParser(prog="art-crit")
    sub = parser.add_subparsers(dest="command", required=True)

    imp = sub.add_parser("import", parents=[common], help="publish a run directory, or every run of a batch directory")
    imp.add_argument("run_dir", help="<batch>/<run id> or <batch> (as `art-crit run` writes them)")
    imp.add_argument("-p", "--page", "--slug", help="override the page slug")
    imp.add_argument("-t", "--title", help="override the page title")
    imp.add_argument("-r", "--redact", action="store_true", help="redact secret hits instead of aborting")
    imp.add_argument("-a", "--allow-threads", action="store_true", help="allow a threaded Godot export")
    imp.add_argument("-n", "--dry-run", action="store_true", help="do the work but write nothing to docs/")

    sub.add_parser("list", parents=[common], help="list pages and their runs")

    rm = sub.add_parser("rm", parents=[common], help="remove a run, or a whole page")
    rm.add_argument("slug")
    rm.add_argument("run_id", nargs="?")
    rm.add_argument("-f", "--failed", action="store_true", help="remove every failed run on the page (asks first)")
    rm.add_argument("-y", "--yes", action="store_true", help="don't ask for confirmation")

    rn = sub.add_parser("rename", parents=[common], help="give a page a new slug (and optionally a title)")
    rn.add_argument("slug")
    rn.add_argument("new_slug")
    rn.add_argument("-t", "--title", help="also set the page title (default: follows the slug if it was derived from it)")

    rt = sub.add_parser("retry", parents=[common], help="run a page's failed runs again, replacing each one that now works")
    rt.add_argument("slug")
    rt.add_argument("run_ids", nargs="*", metavar="run_id", help="only these failed runs (default: every failed run on the page)")
    rt.add_argument("-j", type=int, dest="parallel", help="max agents at once")
    rt.add_argument("-T", "--timeout", help='per agent, e.g. "30m" (default [run].timeout or 30m)')
    rt.add_argument("-y", "--yes", action="store_true", help="don't ask for confirmation")
    rt.add_argument("-n", "--dry-run", action="store_true", help="print the plan and exit")
    rt.add_argument("--no-publish", dest="publish", action="store_false", help="import at the end only; push later with `art-crit publish`")

    vid = sub.add_parser("video", parents=[common], help="make social-media videos comparing runs of a page (needs ffmpeg and Playwright)")
    vid.add_argument("slug")
    vid.add_argument("run_ids", nargs="+", metavar="run_id", help="2 to 12 runs, shown in this order")
    vid.add_argument("-l", "--layout", dest="layouts", action="append", choices=list(LAYOUTS), help="reveal (vertical, one at a time), grid (vertical, all at once) or wide (landscape, one at a time); repeatable (default: all three)")
    vid.add_argument("-d", "--seconds", type=int, default=SECONDS, help=f"seconds per run (default {SECONDS})")
    vid.add_argument("--no-sound", dest="sound", action="store_false", help="a silent audio track instead of the beat and sound effects")
    vid.add_argument("-o", "--out", type=Path, help="output folder (default <root>/videos/<page>)")

    sub.add_parser("rebuild", parents=[common], help="regenerate page.json + pages.json")

    srv = sub.add_parser("serve", parents=[common], help="serve docs/ like GitHub Pages")
    srv.add_argument("-p", "--port", type=int, default=8000)

    pub = sub.add_parser("publish", parents=[common], help="git add docs && commit && push")
    pub.add_argument("-m", "--message")

    run = sub.add_parser("run", parents=[common], help="run agents locally, then import")
    run.add_argument("prompt", nargs="?", help="the task prompt")
    run.add_argument("-f", "--prompt-file", type=Path)
    run.add_argument("-m", "--model", dest="models", action="append", default=[], help="[HARNESS:]MODEL[:LEVELS], repeatable (no prefix = pi); see `art-crit models -H HARNESS`; omit -m/--set to pick interactively")
    run.add_argument("-s", "--set", dest="sets", action="append", default=[], help="a model set: a NAME from art-crit.toml [sets], or a FILE with one MODEL[:LEVELS] per line; repeatable, combines with -m")
    run.add_argument("-i", "--pick", action="store_true", help="interactively pick harnesses, models and levels (implied when no -m/--set is given)")
    run.add_argument("-e", "--effort", help="default LEVELS for every model without a suffix")
    run.add_argument("-k", "--kind", choices=list(KINDS), help="what the agents produce (default: the page's kind, else godot)")
    run.add_argument("-p", "--page", "--slug", help="page slug (default: from --title, else the prompt); an existing page with no PROMPT reuses its prompt")
    run.add_argument("-c", "--change-prompt", action="store_true", help="allow a different prompt for an existing page (replaces it for the whole page)")
    run.add_argument("-t", "--title", help="page title; also the default source of the slug (default: from slug)")
    run.add_argument("-b", "--brief", type=Path, help="brief template file ({prompt} is substituted)")
    run.add_argument("-j", type=int, dest="parallel", help="max agents at once")
    run.add_argument("-T", "--timeout", help='per agent, e.g. "30m" (default [run].timeout or 30m)')
    run.add_argument("-R", "--ref", dest="refs", action="append", default=[], metavar="FILE", help="a reference file under <root>/references/ (copied into each agent's working dir, which the brief points to); repeatable")
    run.add_argument("-y", "--yes", action="store_true", help="don't ask for confirmation")
    run.add_argument("-n", "--dry-run", action="store_true", help="print the plan and exit")
    run.add_argument("-P", "--publish", dest="publish", action="store_true", default=True, help="import and `art-crit publish` each run as it finishes (the default)")
    run.add_argument("--no-publish", dest="publish", action="store_false", help="import at the end only; push later with `art-crit publish`")
    run.add_argument("-r", "--resume", type=Path, help="finish an interrupted batch dir")

    models_p = sub.add_parser("models", parents=[common], help="models the harness can run")
    models_p.add_argument("search", nargs="?", help="also show effort levels for matching models")
    models_p.add_argument("-H", "--harness", default="pi", choices=sorted(HARNESSES), help="which agent program's models (default: pi)")

    return parser


def cmd_publish(root, message, paths=None):
    """Commit and push `paths` and nothing else (default: all of `docs/`). A commit with a pathspec takes those
    paths as they are in the working tree and leaves the rest of the index alone, so publishing a run never
    sweeps up other files: neither unrelated edits under `docs/` nor anything the working copy had staged."""

    def git(*args):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)

    # A path that is gone (a removed run) is covered by its parent directory, which the caller passes instead.
    paths = [str(Path(p).relative_to(root)) if Path(p).is_absolute() and Path(p).is_relative_to(root) else str(p)
             for p in (paths or [])]
    paths = [p for p in paths if (root / p).exists()] or ["docs"]
    add = git("add", "-A", "--", *paths)
    if add.returncode != 0:
        raise CritError(f"git add failed: {add.stderr.strip()}")
    commit = git("commit", "-m", message or "art-crit publish", "--", *paths)
    # With a pathspec, git says "no changes added to commit" (not "nothing to commit") when those paths are clean.
    quiet = ("nothing to commit", "no changes added to commit", "nothing added to commit")
    if commit.returncode != 0 and not any(q in commit.stdout + commit.stderr for q in quiet):
        raise CritError(f"git commit failed: {commit.stderr.strip()}")
    push = git("push")
    if push.returncode != 0:
        raise CritError(f"git push failed: {push.stderr.strip()}")
    print((commit.stdout + commit.stderr).strip() or "nothing to commit")
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    try:
        config = Config.load(root)
        if args.command == "import":
            cmd_import(
                config,
                args.run_dir,
                page=args.page,
                title=args.title,
                redact=args.redact,
                allow_threads=args.allow_threads,
                dry_run=args.dry_run,
            )
            return 0
        if args.command == "list":
            return cmd_list(root)
        if args.command == "rm":
            return cmd_rm(root, args.slug, args.run_id, failed=args.failed, yes=args.yes)
        if args.command == "rename":
            return cmd_rename(root, args.slug, args.new_slug, args.title)
        if args.command == "retry":
            return cmd_retry(config, args.slug, args.run_ids, yes=args.yes, dry_run=args.dry_run,
                             parallel=args.parallel, timeout=args.timeout, publish=args.publish)
        if args.command == "video":
            for path in make_videos(root, args.slug, args.run_ids, args.layouts, args.seconds, args.out, sound=args.sound):
                print(path)
            print(f"link for the post: {compare_url(config.site_url, args.slug, args.run_ids)}")
            return 0
        if args.command == "rebuild":
            rebuild(root)
            return 0
        if args.command == "serve":
            serve_forever(root / "docs", args.port)
            return 0
        if args.command == "publish":
            return cmd_publish(root, args.message)
        if args.command == "run":
            request = RunRequest(
                prompt=args.prompt_file.read_text().strip() if args.prompt_file else (args.prompt or ""),
                kind=args.kind,
                page=args.page,
                title=args.title,
                model_specs=args.models,
                model_sets=args.sets,
                effort=args.effort,
                brief=args.brief.read_text() if args.brief else None,
                parallel=args.parallel,
                timeout=args.timeout,
                publish=args.publish,
                change_prompt=args.change_prompt,
                refs=[resolve_ref(root, ref) for ref in args.refs],
            )
            return cmd_run(
                config,
                request,
                yes=args.yes,
                dry_run=args.dry_run,
                resume=args.resume,
                pick=args.pick,
            )
        if args.command == "models":
            return cmd_models(HARNESSES[args.harness](), args.search)
    except CritError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 1
