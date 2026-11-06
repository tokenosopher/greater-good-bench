"""art-crit run: level parsing, plan/confirmation, parallelism, timeout, failed runs still being
imported, metrics, and --resume. Uses a fake `pi` (tests/fixtures/fake_pi/pi) on PATH so no
real model, Godot or Playwright is needed; Godot export/verify are monkeypatched to fast fakes.
"""

import base64
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from art_crit.cli import main
from art_crit.config import Config, RunRequest
from art_crit.harness import (Codex, GrokBuild, MuseCode, Ori, Pi, agy_metrics, codex_metrics, convert_agy_stream,
                              convert_claude_stream, convert_codex_stream, convert_muse_export, convert_ori_stream,
                              muse_metrics)
from art_crit.runner import assign_run_ids, expand_levels, parse_duration, plan_runs
from art_crit.util import CritError

FAKE_PI = Path(__file__).parent / "fixtures" / "fake_pi"


def batch_runs(plan):
    """The plan's runs as batch.json holds them (ids from a fixed start time)."""
    from datetime import datetime

    from art_crit.runner import Harnesses

    return assign_run_ids(plan, Harnesses(), datetime(2026, 10, 2, 12, 0, 0))


def plan_for(specs, effort=None):
    """plan_runs for a request with no art-crit.toml (no model sets)."""
    return plan_runs(Config.load(Path("/nonexistent")), RunRequest(prompt="p", model_specs=specs, effort=effort))


def fake_export_project(godot_bin, project_dir, out_dir, timeout=600):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(
        '<html><script src="index.js"></script><script>const GODOT_CONFIG = {"executable":"index",'
        '"mainPack":"index.pck","fileSizes":{"index.wasm":1}};</script></html>'
    )
    (out_dir / "index.js").write_bytes(b"js")
    (out_dir / "index.wasm").write_bytes(b"wasm")
    (out_dir / "index.pck").write_bytes(b"pck")
    (out_dir / "index.audio.worklet.js").write_bytes(b"worklet")
    (out_dir / "index.audio.position.worklet.js").write_bytes(b"pos-worklet")
    manifest = {"godot": "4.7.2.fake", "threads": False, "template": "web_nothreads_release.zip", "exportedAt": "2026-09-27T00:00:00Z"}
    (out_dir / "export-manifest.json").write_text(json.dumps(manifest) + "\n")
    return True, manifest, None


@pytest.fixture(autouse=True)
def fake_pi_on_path(monkeypatch):
    monkeypatch.setenv("PATH", f"{FAKE_PI}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.delenv("FAKE_PI_EXIT_CODE", raising=False)
    monkeypatch.delenv("FAKE_PI_HANG", raising=False)
    monkeypatch.delenv("FAKE_PI_ERROR_STOP", raising=False)
    for var in ("FAKE_CLAUDE_ERROR", "FAKE_CLAUDE_HANG", "FAKE_CLAUDE_ARGV"):
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(autouse=True)
def fake_build(monkeypatch):
    monkeypatch.setattr("art_crit.kinds.godot.export_project", fake_export_project)
    monkeypatch.setattr("art_crit.kinds.godot.Godot.verify", lambda self, out_dir: None)
    monkeypatch.setattr("art_crit.kinds.web.Web.verify", lambda self, out_dir: None)


@pytest.fixture
def run_root(bench_root, tmp_path, git_repo):
    runs_dir = tmp_path / "art-crit-runs"
    (bench_root / "art-crit.toml").write_text(f'[run]\ndir = "{runs_dir}"\nparallel = 8\ntimeout = "30m"\n')
    git_repo(bench_root)  # `art-crit run` publishes by default; these tests are a git repo already
    return bench_root


def harness():
    return Pi("pi")


# --- level parsing (pure) ----------------------------------------------------------------------


def test_expand_levels_all_excludes_off():
    supported = ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
    assert expand_levels("all", supported, "m") == ["minimal", "low", "medium", "high", "xhigh", "max"]


def test_expand_levels_range():
    supported = ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
    assert expand_levels("low..high", supported, "m") == ["low", "medium", "high"]


def test_expand_levels_explicit_list():
    supported = ["low", "medium", "high"]
    assert expand_levels("low,high", supported, "m") == ["low", "high"]


def test_expand_levels_explicit_off():
    assert expand_levels("off", ["off", "low"], "m") == ["off"]


def test_expand_levels_unsupported_raises_naming_supported():
    with pytest.raises(CritError, match="low.*not supported.*low, medium, high|not supported"):
        expand_levels("xhigh", ["low", "medium", "high"], "m")


def test_plan_runs_checks_before_anything_starts():
    plan = plan_for(["openai-codex/gpt-6-sol", "test/limited:low..high"], None)
    assert ("pi", "openai-codex/gpt-6-sol", "low") in plan
    assert ("pi", "test/limited", "high") in plan
    assert ("pi", "test/limited", "off") not in plan


def test_plan_runs_unsupported_level_errors_for_whole_batch():
    with pytest.raises(CritError):
        plan_for(["test/limited:xhigh"], None)


def test_plan_runs_dedupes_same_model_merging_levels():
    plan = plan_for(["openai-codex/gpt-6-sol:low", "openai-codex/gpt-6-sol:high"], None)
    assert sorted(l for _, m, l in plan) == ["high", "low"]
    assert len(plan) == 2


def test_plan_runs_rejects_unknown_model_with_suggestions():
    with pytest.raises(CritError, match=r"unknown model 'openai-codex/gpt-6-sool'.*gpt-6-sol"):
        plan_for(["openai-codex/gpt-6-sool:low"], None)
    with pytest.raises(CritError, match="unknown model 'nope/nothing'"):
        plan_for(["nope/nothing"], None)


def test_plan_runs_handles_colons_inside_model_ids():
    model = "openrouter/openai/gpt-6-sol:batch"
    assert plan_for([model], None) == [("pi", model, l) for l in ["low", "medium", "high", "xhigh", "max"]]
    assert plan_for([model + ":high"], None) == [("pi", model, "high")]


def test_run_ids_name_the_run_directories():
    runs = batch_runs(plan_for(["openai-codex/gpt-6-sol:low,high", "claude-code:opus:high"], None))
    assert [r["id"] for r in runs] == [
        "gpt-6-sol-low-20261002-120000", "gpt-6-sol-high-20261002-120000", "claude-opus-5-5-cc-high-20261002-120000"]
    assert runs[2] == {"id": runs[2]["id"], "harness": "claude-code", "model": "anthropic/claude-opus-5-5",
                       "model_arg": "claude-opus-5-5", "level": "high", "state": "queued"}


def test_two_runs_with_one_id_are_refused_before_anything_starts():
    # Two distinct model ids that both reduce to the id "limited-low-...".
    plan = [("pi", "test/limited", "low"), ("pi", "other/limited", "low")]
    with pytest.raises(CritError, match="both resolve to the run id 'limited-low-20261002-120000'"):
        batch_runs(plan)


def test_parse_duration():
    assert parse_duration("30m") == 1800
    assert parse_duration("90s") == 90
    assert parse_duration("1h") == 3600
    with pytest.raises(CritError):
        parse_duration("bad")


# --- plan / confirmation ------------------------------------------------------------------------


def test_dry_run_prints_plan_and_writes_nothing(run_root, capsys):
    rc = main(["run", "--dry-run", "a spinning cube", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "openai-codex/gpt-6-sol:low" in out
    assert not (run_root / "docs" / "data").exists() or not list((run_root / "docs" / "data").iterdir())


def test_slug_comes_from_title_unless_overridden():
    from art_crit.runner import page_slug
    assert page_slug(None, None, "a spinning red cube in space please now") == "a-spinning-red-cube-in-space"
    assert page_slug(None, "Voxel Horse!", "a spinning cube") == "voxel-horse"
    assert page_slug("custom", "Voxel Horse", "a spinning cube") == "custom"
    assert page_slug(None, "  ", "a spinning cube") == "a-spinning-cube"


@pytest.mark.parametrize("flag", ["--page", "--slug"])
def test_dry_run_slug_follows_title_and_slug_flag_overrides(run_root, capsys, flag):
    base = ["run", "--dry-run", "a spinning cube", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]
    assert main(base + ["--title", "Cube Demo"]) == 0
    assert "page: cube-demo (new, title: 'Cube Demo')" in capsys.readouterr().out
    assert main(base + ["--title", "Cube Demo", flag, "my-cube"]) == 0
    assert "page: my-cube (new, title: 'Cube Demo')" in capsys.readouterr().out


def test_missing_confirmation_on_nontty_is_an_error(run_root, monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    rc = main(["run", "a spinning cube", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 1


def test_yes_skips_confirmation_and_runs(run_root, capsys):
    rc = main(["run", "--yes", "a spinning cube", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    results = json.loads((run_root / "docs/data/a-spinning-cube/page.json").read_text())["runs"]
    assert len(results) == 1
    assert results[0]["effort"] == "low"
    assert results[0]["state"] == "complete"
    assert results[0]["harness"]["name"] == "pi"
    assert results[0]["output"] == {"kind": "godot", "entry": "game/index.html", "engine": results[0]["output"]["engine"],
                                    "godot": "4.7.2.fake", "threads": False, "ok": True, "verified": None, "error": None}
    assert results[0]["batch"].endswith("-a-spinning-cube")
    page = json.loads((run_root / "docs/data/a-spinning-cube/page.json").read_text())
    assert page["prompt"] == "a spinning cube"
    assert page["final_prompt"].startswith("a spinning cube\n\nBuild this as a complete, playable Godot")
    assert "Failure summary:" not in capsys.readouterr().err


def test_summary_is_the_agents_blurb_or_its_closing_message_without_one(run_root, monkeypatch):
    main(["run", "--yes", "a spinning cube", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    run = json.loads((run_root / "docs/data/a-spinning-cube/page.json").read_text())["runs"][0]
    assert run["summary"] == "Fake Thing is a stand-in that shows what an agent made."
    monkeypatch.setenv("FAKE_PI_NO_BLURB", "1")
    main(["run", "--yes", "a spinning cone", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    run = json.loads((run_root / "docs/data/a-spinning-cone/page.json").read_text())["runs"][0]
    assert run["summary"] == "Done. Summary: built a fake project."


# --- failures --------------------------------------------------------------------------------


def test_failed_run_is_still_imported(run_root, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    rc = main(["run", "--yes", "broken run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    results = json.loads((run_root / "docs/data/broken-run/page.json").read_text())["runs"]
    assert results[0]["state"] == "failed"
    assert results[0]["error"]
    err = capsys.readouterr().err
    assert "Failure summary: 1 of 1 runs had problems" in err
    assert results[0]["id"] in err and "pi / openai-codex/gpt-6-sol:low" in err
    assert "agent failed: fake pi: forced failure" in err


def test_error_stop_produces_failed_state(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_PI_ERROR_STOP", "1")
    rc = main(["run", "--yes", "error stop run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    results = json.loads((run_root / "docs/data/error-stop-run/page.json").read_text())["runs"]
    assert results[0]["state"] == "failed"
    assert "fake induced error" in results[0]["error"]


def test_timeout_kills_hung_agent(run_root, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_PI_HANG", "1")
    rc = main(["run", "--yes", "--timeout", "1s", "hung run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    results = json.loads((run_root / "docs/data/hung-run/page.json").read_text())["runs"]
    assert results[0]["state"] == "timeout"
    assert "agent timeout: timed out after 1s" in capsys.readouterr().err


def test_a_run_is_one_directory_with_work_harness_and_output(run_root, tmp_path):
    rc = main(["run", "--yes", "layout run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    [batch] = (tmp_path / "art-crit-runs").glob("*-layout-run")
    [run_dir] = [d for d in batch.iterdir() if d.is_dir()]
    assert run_dir.name.startswith("gpt-6-sol-low-")
    assert sorted(p.name for p in run_dir.iterdir()) == ["harness", "output", "run.json", "work"]
    assert (run_dir / "work/project.godot").is_file() and not list((run_dir / "work").glob("*.json"))  # nothing but the agent's files
    assert {"brief.md", "events.jsonl", "conversation.json"} <= {p.name for p in (run_dir / "harness").iterdir()}
    record = json.loads((run_dir / "run.json").read_text())
    assert record["state"] == "complete" and record["output"] == {"kind": "godot", "ok": True, "error": None, "verified": None}
    assert "exit" not in json.dumps(record) and record["batch"] == batch.name
    assert record["tools"]["allowed"] == {"builtin": None, "mcp": {}} and isinstance(record["tools"]["used"], dict)
    batch_json = json.loads((batch / "batch.json").read_text())
    assert [(r["id"], r["state"]) for r in batch_json["runs"]] == [(run_dir.name, "complete")]


def test_a_crashed_harness_is_a_failed_run_with_its_stderr_published(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    rc = main(["run", "--yes", "exit code run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    [run] = json.loads((run_root / "docs/data/exit-code-run/page.json").read_text())["runs"]
    assert (run["state"], run["error"], run["output"]) == ("failed", "fake pi: forced failure", None)
    assert run["session"] == {"stderr": "session/stderr.txt"}  # no transcript: the agent never wrote a session


def test_brief_is_not_written_into_the_agents_working_dir(run_root):
    rc = main(["run", "--yes", "brief location run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    results = json.loads((run_root / "docs/data/brief-location-run/page.json").read_text())["runs"]
    files = results[0]["source"]["files"]
    assert "brief.md" not in files


def test_ref_is_looked_up_under_references_and_named_in_the_brief_only(tmp_path):
    from art_crit.runner import render_brief, resolve_ref

    (tmp_path / "references").mkdir()
    (tmp_path / "references/toy.jpg").write_bytes(b"jpg")
    (tmp_path / "outside.jpg").write_bytes(b"jpg")
    ref = resolve_ref(tmp_path, "toy.jpg")
    assert ref == str((tmp_path / "references/toy.jpg").resolve())
    brief = render_brief(None, "model the toy", "media", (), [ref])
    assert "model the toy\n\nReference files" in brief and "- ./references/toy.jpg" in brief
    assert "references" not in render_brief(None, "model the toy", "media", ())
    for bad in ("missing.jpg", "../outside.jpg"):
        with pytest.raises(CritError, match="no such file"):
            resolve_ref(tmp_path, bad)


def test_ref_is_copied_into_each_runs_work_dir_and_not_published_as_source(run_root, tmp_path):
    (run_root / "references").mkdir()
    (run_root / "references/toy.txt").write_text("a reference")
    rc = main(["run", "--yes", "ref run", "-m", "openai-codex/gpt-6-sol:low", "--ref", "toy.txt", "--root", str(run_root)])
    assert rc == 0
    [batch] = (tmp_path / "art-crit-runs").glob("*-ref-run")
    [run_dir] = [d for d in batch.iterdir() if d.is_dir() and (d / "work").is_dir()]
    assert (run_dir / "work/references/toy.txt").read_text() == "a reference"
    assert "- ./references/toy.txt" in (run_dir / "harness/brief.md").read_text()
    [run] = json.loads((run_root / "docs/data/ref-run/page.json").read_text())["runs"]
    assert not any(f.startswith("references/") for f in run["source"]["files"])


def test_tool_durations_are_stored_and_the_event_stream_is_not_published(run_root):
    rc = main(["run", "--yes", "events run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    run = json.loads((run_root / "docs/data/events-run/page.json").read_text())["runs"][0]
    run_dir = run_root / f"docs/data/events-run/runs/{run['id']}"
    assert "events" not in run["session"] and not (run_dir / "session/events.jsonl").exists()
    convo = json.loads((run_dir / "session/conversation.json").read_text())
    [result] = [e["message"] for e in convo if e.get("message", {}).get("role") == "toolResult"]
    assert result["durationMs"] == 2500  # from the assistant entry that called it to the result entry


def test_export_failure_is_the_outputs_error_not_the_agents(run_root, monkeypatch, capsys):
    def failing_export(godot_bin, project_dir, out_dir, timeout=600):
        return False, None, "Godot export failed: boom"

    monkeypatch.setattr("art_crit.kinds.godot.export_project", failing_export)
    rc = main(["run", "--yes", "export fails run", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    results = json.loads((run_root / "docs/data/export-fails-run/page.json").read_text())["runs"]
    assert results[0]["state"] == "complete" and results[0]["error"] is None  # the agent did finish
    assert results[0]["output"] == {"kind": "godot", "ok": False, "verified": None, "error": "Godot export failed: boom"}
    assert results[0]["thumb"] is None
    err = capsys.readouterr().err
    assert "output: Godot export failed: boom" in err
    assert "agent failed:" not in err


@pytest.mark.parametrize("report,reason", [
    ({"ok": False, "pageErrors": ["ReferenceError: robot is not defined"]}, "page error: ReferenceError: robot is not defined"),
    ({"ok": False, "blockedRequests": ["https://example.test/model.js"]}, "blocked request: https://example.test/model.js"),
    ({"ok": False, "booted": False}, "page did not become ready"),
    ({"ok": False, "framesDiffer": False}, "captured frames did not change"),
    ({"ok": False}, "check failed without a recorded reason"),
    ({"ok": True}, None),
    (None, None),
    (RuntimeError("Chrome unavailable"), "could not run verification: Chrome unavailable"),
])
def test_verification_summary_survives_resume(run_root, monkeypatch, tmp_path, capsys, report, reason):
    def verify(self, out_dir):
        if isinstance(report, Exception):
            raise report
        return report

    monkeypatch.setattr("art_crit.kinds.godot.Godot.verify", verify)
    assert main(["run", "--yes", "--no-publish", "verify summary", "-m", "openai-codex/gpt-6-sol:low",
                 "--root", str(run_root)]) == 0
    [batch] = (tmp_path / "art-crit-runs").glob("*-verify-summary")
    [run] = json.loads((run_root / "docs/data/verify-summary/page.json").read_text())["runs"]
    assert run["state"] == "complete" and run["output"]["ok"] is True
    assert run["output"]["error"] is None
    expected = report["ok"] if isinstance(report, dict) else None
    assert run["output"]["verified"] is expected  # verifier exceptions aren't model failures
    first = capsys.readouterr().err
    monkeypatch.setattr("art_crit.kinds.godot.Godot.verify", lambda *args: pytest.fail("resume must reuse diagnostics"))
    assert main(["run", "--resume", str(batch), "--no-publish", "--root", str(run_root)]) == 0
    resumed = capsys.readouterr().err
    for err in (first, resumed):
        if reason:
            assert err.count("Failure summary:") == 1
            assert f"verification: {reason}" in err
            assert str(batch) in err
        else:
            assert "Failure summary:" not in err


def test_failure_summary_is_in_plan_order_and_omits_successes(run_root, monkeypatch, capsys):
    def finalize(self, work, out):
        if "-high-" in work.parent.name:
            return False, "missing project.godot"
        ok, _, error = fake_export_project(None, work, out)
        return ok, error

    monkeypatch.setattr("art_crit.kinds.godot.Godot.finalize", finalize)
    assert main(["run", "--yes", "--no-publish", "mixed summary", "-m", "openai-codex/gpt-6-sol:high,low",
                 "-m", "openai-codex/gpt-6-luna:high", "--root", str(run_root)]) == 0
    summary = capsys.readouterr().err
    assert "Failure summary: 2 of 3 runs had problems" in summary
    assert "gpt-6-sol:low" not in summary
    assert summary.index("gpt-6-sol:high") < summary.index("gpt-6-luna:high")
    assert summary.count("output: missing project.godot") == 2


@pytest.mark.parametrize("recovers", [False, True])
def test_summary_reports_only_unrecovered_publish_errors(run_root, monkeypatch, capsys, recovers):
    attempts = []

    def publish(*args):
        attempts.append(1)
        if len(attempts) == 1 or not recovers:
            raise CritError("git push failed: offline")
        return 0

    monkeypatch.setattr("art_crit.cli.cmd_publish", publish)
    assert main(["run", "--yes", "push summary", "-m", "openai-codex/gpt-6-sol:low",
                 "--root", str(run_root)]) == (0 if recovers else 1)
    err = capsys.readouterr().err
    if recovers:
        assert "Failure summary:" not in err
    else:
        assert "Failure summary: 1 of 1 runs had problems" in err
        assert "publish: git push failed: offline" in err


# --- parallelism -------------------------------------------------------------------------------


def test_multiple_models_and_levels_all_run(run_root):
    rc = main([
        "run", "--yes", "-j", "4", "many runs",
        "-m", "openai-codex/gpt-6-sol:low,high",
        "-m", "openai-codex/gpt-6-luna:medium",
        "--root", str(run_root),
    ])
    assert rc == 0
    results = json.loads((run_root / "docs/data/many-runs/page.json").read_text())["runs"]
    assert len(results) == 3
    assert {r["effort"] for r in results} == {"low", "medium", "high"}
    assert {r["model"] for r in results} == {"openai-codex/gpt-6-sol", "openai-codex/gpt-6-luna"}


# --- resume --------------------------------------------------------------------------------------


def test_resume_does_not_rerun_finished_agents(run_root, monkeypatch, tmp_path):
    # Build a batch by hand: one run already "complete" (its work, run.json and output already on
    # disk), one still "queued". Resume must only (re)run the queued one.
    from art_crit.runner import write_batch_json

    batch_dir = tmp_path / "art-crit-runs" / "2026-09-27-000000-resume-me"
    low = batch_dir / "gpt-6-sol-low-20260927-000000"
    (low / "work").mkdir(parents=True)
    (low / "work" / "project.godot").write_text("config_version=5\n")
    fake_export_project(None, low / "work", low / "output")
    (low / "run.json").write_text(json.dumps({
        "id": low.name, "page": "resume-me", "model": "openai-codex/gpt-6-sol", "effort": "low", "kind": "godot",
        "started_at": "2026-09-27T00:00:00Z", "batch": batch_dir.name, "harness": {"name": "pi", "version": "0.1.0-fake"},
        "state": "complete", "error": None, "route": None,
        "metrics": {"duration_ms": 1, "cost_usd": 0.01, "tool_calls": 1, "turns": 1, "tokens_total": 2, "tokens_input": 1,
                    "tokens_output": 1, "tokens_reasoning": 0, "tokens_cache_read": 0},
        "output": {"kind": "godot", "ok": True, "error": None, "verified": None},
    }))
    (batch_dir / "prompt.md").write_text("resume me")
    runs = [
        {"id": low.name, "harness": "pi", "model": "openai-codex/gpt-6-sol", "model_arg": "openai-codex/gpt-6-sol", "level": "low", "state": "complete"},
        {"id": "gpt-6-sol-medium-20260927-000000", "harness": "pi", "model": "openai-codex/gpt-6-sol",
         "model_arg": "openai-codex/gpt-6-sol", "level": "medium", "state": "queued"},
    ]
    write_batch_json(batch_dir, {
        "prompt": "resume me", "kind": "godot", "page": "resume-me", "title": "Resume me", "title_is_explicit": False,
        "harnesses": {"pi": "0.1.0-fake"}, "brief": "do the thing", "created": "2026-09-27T00:00:00Z", "runs": runs,
    })

    exported = []

    def counting_export(godot_bin, project_dir, out_dir, timeout=600):
        exported.append(project_dir.parent.name)
        return fake_export_project(godot_bin, project_dir, out_dir, timeout)

    monkeypatch.setattr("art_crit.kinds.godot.export_project", counting_export)

    rc = main(["run", "--resume", str(batch_dir), "--root", str(run_root)])
    assert rc == 0

    # The already-complete "low" run must not have been re-run (its hand-written project file is
    # untouched: the fake pi always overwrites project.godot with its own fixed content), nor re-exported.
    assert (low / "work" / "project.godot").read_text() == "config_version=5\n"
    assert exported == ["gpt-6-sol-medium-20260927-000000"]
    medium = json.loads((batch_dir / "gpt-6-sol-medium-20260927-000000" / "run.json").read_text())
    assert medium["state"] == "complete" and medium["output"]["ok"] is True
    assert [r["state"] for r in json.loads((batch_dir / "batch.json").read_text())["runs"]] == ["complete", "complete"]

    results = json.loads((run_root / "docs/data/resume-me/page.json").read_text())["runs"]
    assert sorted(r["effort"] for r in results) == ["low", "medium"]


def test_resume_retries_a_failed_output_step_without_rerunning_the_agent(run_root, monkeypatch, tmp_path):
    attempts = []

    def flaky_export(godot_bin, project_dir, out_dir, timeout=600):
        attempts.append(1)
        if len(attempts) == 1:
            return False, None, "Godot export failed: first try"
        return fake_export_project(godot_bin, project_dir, out_dir, timeout)

    monkeypatch.setattr("art_crit.kinds.godot.export_project", flaky_export)
    assert main(["run", "--yes", "retry output", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/retry-output/page.json").read_text())["runs"]
    assert run["output"]["ok"] is False
    [batch] = (tmp_path / "art-crit-runs").glob("*-retry-output")
    work = batch / run["id"] / "work"
    (work / "marker.txt").write_text("the agent must not run again")

    assert main(["run", "--resume", str(batch), "--root", str(run_root)]) == 0
    assert (work / "marker.txt").is_file() and len(attempts) == 2
    [run] = json.loads((run_root / "docs/data/retry-output/page.json").read_text())["runs"]
    assert run["output"]["ok"] is True and run["state"] == "complete"


# --- retry ------------------------------------------------------------------------------------


def page_runs(root, slug):
    return json.loads((root / "docs/data" / slug / "page.json").read_text())["runs"]


def test_retry_replaces_a_failed_run_with_a_good_one(run_root, monkeypatch):
    spec = "openai-codex/gpt-6-sol"
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "retry me", "-m", f"{spec}:low", "-m", f"{spec}:medium", "--root", str(run_root)]) == 0
    monkeypatch.delenv("FAKE_PI_EXIT_CODE")
    assert main(["run", "--yes", "--page", "retry-me", "-m", f"{spec}:high", "--root", str(run_root)]) == 0
    before = {r["effort"]: r["id"] for r in page_runs(run_root, "retry-me")}
    assert [r["state"] for r in page_runs(run_root, "retry-me")].count("failed") == 2

    assert main(["retry", "--yes", "retry-me", "--root", str(run_root)]) == 0
    runs = page_runs(run_root, "retry-me")
    assert sorted(r["effort"] for r in runs) == ["high", "low", "medium"]
    assert all(r["state"] == "complete" and r["output"]["ok"] for r in runs)
    assert next(r["id"] for r in runs if r["effort"] == "high") == before["high"]  # the good run wasn't touched
    assert not {before["low"], before["medium"]} & {r["id"] for r in runs}
    assert not (run_root / "docs/data/retry-me/runs" / before["low"]).exists()
    log = subprocess.run(["git", "log", "-1", "--format=%s"], cwd=run_root, capture_output=True, text=True).stdout
    assert "art-crit retry: retry-me (replaced 2 failed runs)" in log


def test_retry_keeps_a_run_that_fails_again_and_exits_nonzero(run_root, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "stays broken", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    [old] = page_runs(run_root, "stays-broken")
    assert main(["retry", "--yes", "stays-broken", "--root", str(run_root)]) == 1
    runs = page_runs(run_root, "stays-broken")
    assert len(runs) == 2 and old["id"] in {r["id"] for r in runs}
    assert f"still failed: {old['id']}" in capsys.readouterr().err


def test_retry_only_takes_failed_runs_and_known_pages(run_root, monkeypatch, capsys):
    assert main(["run", "--yes", "all good", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    [run] = page_runs(run_root, "all-good")
    assert main(["retry", "all-good", "--root", str(run_root)]) == 0
    assert "no failed runs on all-good" in capsys.readouterr().out
    assert main(["retry", "all-good", run["id"], "--root", str(run_root)]) == 1
    assert "didn't fail" in capsys.readouterr().err
    assert main(["retry", "all-good", "nope", "--root", str(run_root)]) == 1
    assert "no such run" in capsys.readouterr().err
    assert main(["retry", "no-such-page", "--root", str(run_root)]) == 1
    assert "no such page" in capsys.readouterr().err
    assert len(page_runs(run_root, "all-good")) == 1


def test_retry_dry_run_only_prints_the_plan(run_root, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "just look", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    capsys.readouterr()
    assert main(["retry", "--dry-run", "just-look", "--root", str(run_root)]) == 0
    out = capsys.readouterr().out
    assert "retrying 1 failed run on just-look" in out and "openai-codex/gpt-6-sol:low" in out
    assert len(page_runs(run_root, "just-look")) == 1


def test_retry_spec_names_the_model_the_harness_lists_under_the_recorded_display_name():
    from art_crit.retry import retry_spec
    from art_crit.runner import Harnesses

    harnesses = Harnesses()
    run = {"id": "x", "harness": {"name": "claude-code"}, "model": "anthropic/claude-opus-5-5", "effort": "high"}
    assert retry_spec(harnesses, run) == "claude-code:claude-opus-5-5:high"
    with pytest.raises(CritError, match="no longer offers"):
        retry_spec(harnesses, {**run, "model": "anthropic/claude-gone-1"})


def batch_count(tmp_path):
    return len(list((tmp_path / "art-crit-runs").glob("*-*")))


def test_retry_does_not_rerun_a_failed_run_that_already_has_a_good_newer_one(run_root, monkeypatch, tmp_path):
    spec = "openai-codex/gpt-6-sol:low"
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "fixed already", "-m", spec, "--root", str(run_root)]) == 0
    monkeypatch.delenv("FAKE_PI_EXIT_CODE")
    assert main(["run", "--yes", "--page", "fixed-already", "-m", spec, "--root", str(run_root)]) == 0
    batches = batch_count(tmp_path)

    assert main(["retry", "--yes", "fixed-already", "--root", str(run_root)]) == 0
    [run] = page_runs(run_root, "fixed-already")
    assert run["state"] == "complete" and batch_count(tmp_path) == batches  # replaced, no agent started


def test_retry_after_ctrl_c_still_replaces_what_finished(run_root, monkeypatch):
    import art_crit.retry as retry

    spec = "openai-codex/gpt-6-sol:low"
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "interrupted", "-m", spec, "--root", str(run_root)]) == 0
    monkeypatch.delenv("FAKE_PI_EXIT_CODE")
    real = retry.cmd_run

    def run_then_ctrl_c(*args, **kwargs):
        real(*args, **kwargs)
        raise SystemExit(130)

    monkeypatch.setattr(retry, "cmd_run", run_then_ctrl_c)
    with pytest.raises(SystemExit):
        main(["retry", "--yes", "interrupted", "--root", str(run_root)])
    [run] = page_runs(run_root, "interrupted")
    assert run["state"] == "complete"


def test_retry_declined_changes_nothing(run_root, monkeypatch, capsys):
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "say no", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    capsys.readouterr()
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    assert main(["retry", "say-no", "--root", str(run_root)]) == 1
    captured = capsys.readouterr()
    assert "aborted" in captured.out and "still failed" not in captured.err
    assert len(page_runs(run_root, "say-no")) == 1


def test_retry_skips_a_model_the_harness_no_longer_offers(run_root, monkeypatch, capsys):
    spec = "openai-codex/gpt-6-sol"
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "retired", "-m", f"{spec}:low", "-m", f"{spec}:medium", "--root", str(run_root)]) == 0
    monkeypatch.delenv("FAKE_PI_EXIT_CODE")
    low = next(r for r in page_runs(run_root, "retired") if r["effort"] == "low")
    run_json = run_root / "docs/data/retired/runs" / low["id"] / "run.json"
    run_json.write_text(json.dumps({**json.loads(run_json.read_text()), "model": "openai-codex/retired-model"}))
    assert main(["rebuild", "--root", str(run_root)]) == 0
    capsys.readouterr()

    assert main(["retry", "--yes", "retired", low["id"], "--root", str(run_root)]) == 1  # named: an error
    assert "no longer offers openai-codex/retired-model" in capsys.readouterr().err
    assert main(["retry", "--yes", "retired", "--root", str(run_root)]) == 1  # not named: the others still run
    err = capsys.readouterr().err
    assert "skipping" in err and f"still failed: {low['id']}" in err
    assert sorted((r["effort"], r["state"]) for r in page_runs(run_root, "retired")) == [("low", "failed"), ("medium", "complete")]


def test_retry_runs_identical_failed_runs_once_and_replaces_them_all(run_root, monkeypatch, tmp_path):
    spec = "openai-codex/gpt-6-sol:low"
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "twice broken", "-m", spec, "--root", str(run_root)]) == 0
    assert main(["run", "--yes", "--page", "twice-broken", "-m", spec, "--root", str(run_root)]) == 0
    monkeypatch.delenv("FAKE_PI_EXIT_CODE")
    assert len(page_runs(run_root, "twice-broken")) == 2
    batches = batch_count(tmp_path)

    assert main(["retry", "--yes", "twice-broken", "--root", str(run_root)]) == 0
    [run] = page_runs(run_root, "twice-broken")
    assert run["state"] == "complete" and batch_count(tmp_path) == batches + 1


def test_retry_no_publish_replaces_locally_without_a_commit(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_PI_EXIT_CODE", "1")
    assert main(["run", "--yes", "keep local", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    monkeypatch.delenv("FAKE_PI_EXIT_CODE")
    head = lambda: subprocess.run(["git", "rev-parse", "HEAD"], cwd=run_root, capture_output=True, text=True).stdout
    before = head()
    assert main(["retry", "--yes", "--no-publish", "keep-local", "--root", str(run_root)]) == 0
    [run] = page_runs(run_root, "keep-local")
    assert run["state"] == "complete" and head() == before


def test_retry_spec_keeps_a_pinned_openrouter_upstream_and_reads_the_model_list_once():
    from art_crit.retry import retry_spec
    from art_crit.runner import Harnesses

    harnesses = Harnesses()
    run = {"id": "x", "harness": {"name": "pi"}, "model": "openrouter/test/model@deepinfra", "effort": "low"}
    assert retry_spec(harnesses, run) == "pi:openrouter/test/model@deepinfra:low"
    assert plan_for([retry_spec(harnesses, run)]) == [("pi", "openrouter/test/model@deepinfra", "low")]  # what `run` plans from it

    class Listing:
        calls = 0
        pinned = lambda self, model, upstreams: model
        display_model = lambda self, model: model

        def models(self):
            Listing.calls += 1
            return ["a/b"]

    listed = {}
    for _ in range(3):
        retry_spec({"pi": Listing()}, {"id": "y", "harness": {"name": "pi"}, "model": "a/b", "effort": "low"}, listed)
    assert Listing.calls == 1


# --- Ctrl-C -----------------------------------------------------------------------------------


def test_ctrl_c_kills_the_agent_and_marks_it_queued_for_resume(run_root, monkeypatch):
    """A hung fake pi + a real SIGINT delivered to this process shortly after it starts (mirroring
    a real Ctrl-C) must: kill the fake pi's process group (so it stops "billing"), leave the run
    "queued" in batch.json (so --resume reruns it), and exit 130. This exercises the real
    interrupt path end to end rather than calling internal cleanup helpers directly.

    A real `os.kill(os.getpid(), SIGINT)` is used rather than `_thread.interrupt_main()`: the
    latter only sets a flag that the main thread notices between bytecode instructions, which
    never happens while it's blocked inside a C-level `Future.result()` lock wait, so it would
    never actually interrupt this test (and did, in fact, hang indefinitely when tried).
    """
    import signal
    import threading

    monkeypatch.setenv("FAKE_PI_HANG", "1")

    def interrupt_once_agent_started():  # Ctrl-C only after the fake pi is really running
        deadline = time.time() + 10
        while time.time() < deadline and not list(run_root.parent.glob("art-crit-runs/*-interrupt-me/*/work/fake_pi.pid")):
            time.sleep(0.05)
        os.kill(os.getpid(), signal.SIGINT)

    threading.Thread(target=interrupt_once_agent_started, daemon=True).start()

    with pytest.raises(SystemExit) as exc_info:
        main(["run", "--yes", "interrupt me", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert exc_info.value.code == 130

    assert not (run_root / "docs" / "data").exists() or not list((run_root / "docs" / "data").iterdir())

    from art_crit.config import Config

    cfg = Config.load(run_root)
    batches = list(cfg.run.dir.glob("*-interrupt-me"))
    assert len(batches) == 1
    batch = json.loads((batches[0] / "batch.json").read_text())
    assert batch["runs"][0]["state"] == "queued"

    # The fake pi's process (and its process group) must actually be gone, not just abandoned.
    pid = int(next(batches[0].glob("*/work/fake_pi.pid")).read_text())
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            break
        time.sleep(0.1)
    else:
        pytest.fail(f"fake pi (pid {pid}) still alive after Ctrl-C")


# --- metrics against the real voxel-horse session (when present) --------------------------------

REAL_RUN = Path.home() / "dev/effort-runs/2026-09-26-001158-gpt6sol-voxel-horse"


@pytest.mark.skipif(not REAL_RUN.is_dir(), reason="real effort run not on this machine")
def test_metrics_match_real_session_numbers():
    from art_crit.harness import parse_session

    expected = {
        "low": (10692, 3553, 14245, 62, 38016, 0.0645172, 10, 11),
        "medium": (11271, 4906, 16177, 985, 41216, 0.079845, 9, 9),
        "high": (25280, 7452, 32732, 3073, 105984, 0.1462768, 16, 17),
    }
    for level, (inp, out, total, reasoning, cache_read, cost, tool_calls, turns) in expected.items():
        m = parse_session(REAL_RUN / level / "session.jsonl")
        assert m["tokens"]["input"] == inp
        assert m["tokens"]["output"] == out
        assert m["tokens"]["total"] == total
        assert m["tokens"]["reasoning"] == reasoning
        assert m["tokens"]["cacheRead"] == cache_read
        assert round(m["cost_usd"], 4) == round(cost, 4)
        assert m["tool_calls"] == tool_calls
        assert m["turns"] == turns


# --- web kind ------------------------------------------------------------------------------------
needs_esbuild = pytest.mark.skipif(shutil.which("esbuild") is None, reason="esbuild not on PATH")


@needs_esbuild
def test_web_run_publishes_one_packaged_page(run_root):
    rc = main(["run", "--yes", "--kind", "web", "a spinning horse", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    assert json.loads((run_root / "docs/data/a-spinning-horse/page.json").read_text())["kind"] == "web"
    [run] = json.loads((run_root / "docs/data/a-spinning-horse/page.json").read_text())["runs"]
    assert run["kind"] == "web" and run["state"] == "complete" and run["error"] is None
    out = run["output"]
    assert (out["kind"], out["entry"], out["ok"]) == ("web", "game/index.html", True) and out["esbuild"] and out["bytes"]
    run_dir = run_root / "docs/data/a-spinning-horse/runs" / run["id"]
    assert [p.name for p in (run_dir / "game").iterdir()] == ["index.html"]  # one file
    html = (run_dir / "game/index.html").read_text()
    assert "spinning " in html and "#123" in html  # the npm package and the stylesheet are inlined
    assert 'src="main.js"' not in html and "fakepkg" not in html and "style.css" not in html
    assert str(Path.home()) not in html  # cleaned like source
    assert run["source"]["files"] == ["index.html", "main.js", "package.json", "style.css"]  # no node_modules/


@needs_esbuild
def test_web_run_that_fails_to_package_has_an_output_error_not_an_agent_error(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_PI_BAD_WEB", "1")
    rc = main(["run", "--yes", "--kind", "web", "broken page", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    [run] = json.loads((run_root / "docs/data/broken-page/page.json").read_text())["runs"]
    assert run["state"] == "complete" and run["error"] is None
    assert run["output"]["ok"] is False and run["output"]["verified"] is None and "entry" not in run["output"]
    assert run["output"]["error"].startswith("packaging failed: esbuild:") and "missing.js" in run["output"]["error"]
    assert "main.js" in run["source"]["files"]  # the source is still published


def test_web_run_needs_esbuild(run_root, monkeypatch):
    monkeypatch.setattr("art_crit.kinds.shutil.which", lambda name: None if name == "esbuild" else "/bin/" + name)
    with pytest.raises(CritError, match="needs esbuild"):
        from art_crit.runner import cmd_run

        cmd_run(Config.load(run_root), RunRequest(prompt="x", model_specs=["openai-codex/gpt-6-sol:low"], kind="web"), dry_run=True)


# --- media kind ----------------------------------------------------------------------------------

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="needs ffmpeg")


@needs_ffmpeg
def test_media_run_publishes_output_files(run_root):
    rc = main(["run", "--yes", "--kind", "media", "a red circle", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    page = json.loads((run_root / "docs/data/a-red-circle/page.json").read_text())
    assert page["kind"] == "media"
    assert "./output/" in page["final_prompt"] and "Tools available on this machine: " in page["final_prompt"]
    [run] = json.loads((run_root / "docs/data/a-red-circle/page.json").read_text())["runs"]
    assert run["kind"] == "media" and run["error"] is None
    assert (run["output"]["ok"], run["output"]["verified"], run["output"]["error"]) == (True, True, None)
    by_path = {m["path"]: m for m in run["output"]["items"]}
    assert set(by_path) == {"media/clip.mp4", "media/dot.png", "media/drawing.svg"}
    assert by_path["media/drawing.svg"]["width"] == 120
    assert by_path["media/clip.mp4"]["poster"] == "media/clip.poster.jpg"
    # Cards show 800 px JPEG thumbnails made at import (a video's from its poster), never SVGs; the run's is the first item's.
    assert by_path["media/clip.mp4"]["thumb"] == "media/clip.thumb.jpg" and by_path["media/dot.png"]["thumb"] == "media/dot.thumb.jpg"
    assert "thumb" not in by_path["media/drawing.svg"]
    assert run["thumb"] == "media/clip.thumb.jpg"  # first item, sorted by name
    run_dir = run_root / "docs/data/a-red-circle/runs" / run["id"]
    for rel in [*by_path, "media/clip.poster.jpg", "media/clip.thumb.jpg", "media/dot.thumb.jpg"]:
        assert (run_dir / rel).is_file()
    assert str(Path.home()) not in (run_dir / "media/drawing.svg").read_text()  # SVGs are cleaned
    # Source is the text code only: media files in ./output/ and the leftover binary frame aren't source.
    assert run["source"]["files"] == ["make.py"]
    pages = json.loads((run_root / "docs/data/pages.json").read_text())
    assert pages[0]["kind"] == "media"
    assert pages[0]["thumb"] == f"data/a-red-circle/runs/{run['id']}/media/clip.thumb.jpg"


@needs_ffmpeg
def test_media_run_with_bad_output_is_ok_but_not_verified_with_an_output_error(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_PI_BAD_OUTPUT", "1")
    rc = main(["run", "--yes", "--kind", "media", "bad media", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    [run] = json.loads((run_root / "docs/data/bad-media/page.json").read_text())["runs"]
    assert run["state"] == "complete" and run["error"] is None
    assert (run["output"]["ok"], run["output"]["verified"]) == (True, False)
    assert "broken.png: not a readable image" in run["output"]["error"]
    assert len(run["output"]["items"]) == 3  # the good files are still published
    # notes.txt isn't an output (it's skipped, not an error) but it's still published as source.
    assert run["source"]["files"] == ["make.py", "output/notes.txt"]


def test_kind_must_match_the_existing_page(run_root):
    assert main(["run", "--yes", "mixed page", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    rc = main(["run", "--yes", "--kind", "media", "mixed page", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 1


# --- publishing as runs finish ---------------------------------------------------------------------


def git_subjects(root):
    out = subprocess.run(["git", "-C", str(root), "log", "--format=%s"], check=True, capture_output=True, text=True)
    return out.stdout.splitlines()


def test_run_publishes_each_run_as_it_finishes_by_default(run_root, git_repo, capsys):
    """Publishing is the default: every run is imported, committed and pushed on its own, and nothing is
    left to the batch's own import at the end (which would print the preview hint)."""
    origin = git_repo(run_root)
    rc = main(["run", "--yes", "a horse as we go", "-m", "openai-codex/gpt-6-sol:low..high",
               "--root", str(run_root)])
    assert rc == 0
    out = capsys.readouterr().out
    runs = json.loads((run_root / "docs/data/a-horse-as-we-go/page.json").read_text())["runs"]
    assert len(runs) == 3
    assert f"published {len(runs)} runs to 'a-horse-as-we-go' as they finished" in out
    assert "Preview with: art-crit serve" not in out
    subjects = git_subjects(run_root)
    assert sorted(subjects) == sorted(["init", *(f"art-crit run: a-horse-as-we-go ({r['id']})" for r in runs)])
    assert git_subjects(origin) == subjects  # and pushed
    status = subprocess.run(["git", "-C", str(run_root), "status", "--porcelain"], check=True, capture_output=True, text=True)
    assert not status.stdout.strip(), "every published file is committed"


def test_run_publish_does_not_sweep_up_unrelated_changes(run_root, git_repo, capsys):
    """Each run's commit holds that run's files and nothing else: a change staged in the working copy (here
    src/, which publish never stages) or a pending edit under docs/ stays out of the publish commit."""
    git_repo(run_root)
    (run_root / "src").mkdir(exist_ok=True)
    (run_root / "src" / "unrelated.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", str(run_root), "add", "src/unrelated.py"], check=True)
    (run_root / "docs" / "assets").mkdir(parents=True, exist_ok=True)
    (run_root / "docs" / "assets" / "viewer.js").write_text("// pending tweak\n")

    assert main(["run", "--yes", "a clean publish", "-m", "openai-codex/gpt-6-sol:low..high",
                 "--root", str(run_root)]) == 0

    changed = subprocess.run(["git", "-C", str(run_root), "show", "--name-only", "--format=", "HEAD"],
                             check=True, capture_output=True, text=True).stdout.split()
    assert changed and all(p.startswith("docs/data/a-clean-publish/") or p == "docs/data/pages.json" for p in changed), changed
    status = subprocess.run(["git", "-C", str(run_root), "status", "--porcelain"],
                            check=True, capture_output=True, text=True).stdout
    assert "src/unrelated.py" in status and "docs/assets/" in status


def test_run_no_publish_imports_only(run_root, capsys):
    """--no-publish imports the batch at the end and leaves the push to `art-crit publish`, so nothing is
    committed on its own."""
    rc = main(["run", "--yes", "--no-publish", "a quiet horse", "-m", "openai-codex/gpt-6-sol:low",
               "--root", str(run_root)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Preview with: art-crit serve" in out and "publish with: art-crit publish" in out
    assert "as they finished" not in out
    assert git_subjects(run_root) == ["init"]  # nothing published
    assert len(json.loads((run_root / "docs/data/a-quiet-horse/page.json").read_text())["runs"]) == 1


def test_run_publish_falls_back_to_the_batch_import_for_a_missed_run(run_root, monkeypatch, capsys):
    """A run that couldn't be published is picked up by the batch's own import at the end (the path that
    also reports the failure and exits non-zero when it fails again)."""
    monkeypatch.setattr("art_crit.runner.Publisher.publish", lambda self, run_id: None)
    rc = main(["run", "--yes", "a missed horse", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Preview with: art-crit serve" in out
    assert "as they finished" not in out
    assert len(json.loads((run_root / "docs/data/a-missed-horse/page.json").read_text())["runs"]) == 1


# --- a new kind -----------------------------------------------------------------------------------


def test_a_new_kind_is_only_a_kind_class(run_root, monkeypatch):
    """A toy kind (a brief and a finalize that makes one file) runs end to end with the fake pi: the
    runner and the importer have no `if kind ==` for it. The viewer shows any output with an `entry`
    in the sandbox (the demo fixture's "custom" kind is covered in test_web.py)."""
    from art_crit.kinds import KINDS, Kind, Staged

    class Toy(Kind):
        name = "toy"

        def brief(self):
            return "{prompt}\n\nWrite a README.md."

        def finalize(self, work_dir, out_dir):
            out_dir.mkdir(parents=True)
            (out_dir / "index.html").write_text(f"<h1>{(work_dir / 'README.md').read_text()}</h1>")
            return True, None

        def stage(self, out_dir, run_dir, ctx):
            ctx.write_text(out_dir / "index.html", run_dir / "game" / "index.html")
            return Staged({"entry": "game/index.html"})

    monkeypatch.setitem(KINDS, "toy", Toy)
    assert main(["run", "--yes", "--kind", "toy", "a toy", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    page = json.loads((run_root / "docs/data/a-toy/page.json").read_text())
    [run] = page["runs"]
    assert page["kind"] == "toy" and page["final_prompt"] == "a toy\n\nWrite a README.md."
    assert run["output"] == {"kind": "toy", "entry": "game/index.html", "ok": True, "verified": None, "error": None}
    assert "fake project" in (run_root / "docs/data/a-toy/runs" / run["id"] / "game/index.html").read_text()
    assert "README.md" in run["source"]["files"]


# --- model sets ------------------------------------------------------------------------------------


def write_sets(run_root, body):
    cfg = run_root / "art-crit.toml"
    cfg.write_text(cfg.read_text() + "\n[sets]\n" + body)


def test_set_from_bench_toml_expands_like_m_flags(run_root, capsys):
    write_sets(run_root, 'duo = ["openai-codex/gpt-6-sol:low,high", "test/limited"]\n')
    rc = main(["run", "--dry-run", "cube", "--set", "duo", "-e", "medium", "--root", str(run_root)])
    assert rc == 0
    out = capsys.readouterr().out
    for spec in ("openai-codex/gpt-6-sol:low", "openai-codex/gpt-6-sol:high", "test/limited:medium"):
        assert spec in out
    assert "test/limited:low" not in out  # -e applies to set entries without levels


def test_set_from_a_file_combines_with_m(run_root, tmp_path, capsys):
    f = tmp_path / "mine.txt"
    f.write_text("# my models\nopenai-codex/gpt-6-luna:minimal   # cheapest\n\ntest/limited:high\n")
    rc = main(["run", "--dry-run", "cube", "-s", str(f), "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1. openai-codex/gpt-6-luna:minimal" in out and "test/limited:high" in out and "openai-codex/gpt-6-sol:low" in out


def test_unknown_set_lists_the_defined_ones(run_root, capsys):
    write_sets(run_root, 'duo = ["test/limited"]\n')
    rc = main(["run", "--dry-run", "cube", "--set", "nope", "--root", str(run_root)])
    assert rc == 1
    err = capsys.readouterr().err
    assert "unknown model set 'nope'" in err and "(duo)" in err


def test_set_entries_are_checked_like_m_flags(run_root, capsys):
    write_sets(run_root, 'bad = ["test/limited:xhigh"]\n')
    assert main(["run", "--dry-run", "cube", "--set", "bad", "--root", str(run_root)]) == 1
    err = capsys.readouterr().err
    assert "xhigh" in err and "not supported" in err


def test_malformed_set_is_an_error(run_root, capsys):
    write_sets(run_root, 'notalist = "test/limited"\n')
    assert main(["run", "--dry-run", "cube", "--set", "notalist", "--root", str(run_root)]) == 1
    assert "[sets].notalist must be a list" in capsys.readouterr().err


# --- adding runs to an existing page --------------------------------------------------------------


@needs_ffmpeg
def test_page_alone_reuses_the_pages_prompt_and_kind(run_root):
    assert main(["run", "--yes", "--kind", "media", "a red circle", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    rc = main(["run", "--yes", "--page", "a-red-circle", "-m", "openai-codex/gpt-6-luna:minimal", "--root", str(run_root)])
    assert rc == 0
    results = json.loads((run_root / "docs/data/a-red-circle/page.json").read_text())["runs"]
    assert {(r["model"], r["effort"], r["kind"]) for r in results} == {
        ("openai-codex/gpt-6-sol", "low", "media"), ("openai-codex/gpt-6-luna", "minimal", "media")}
    assert json.loads((run_root / "docs/data/a-red-circle/page.json").read_text())["prompt"] == "a red circle"


@needs_ffmpeg
def test_page_alone_reuses_the_pages_references(run_root, tmp_path, capsys):
    (run_root / "references").mkdir()
    (run_root / "references/toy.txt").write_text("a reference")
    (run_root / "references/other.txt").write_text("another reference")
    base = ["run", "--yes", "--kind", "media", "draw the toy", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]
    assert main(base + ["--ref", "toy.txt"]) == 0
    capsys.readouterr()
    assert main(["run", "--yes", "--page", "draw-the-toy", "-m", "openai-codex/gpt-6-luna:minimal", "--root", str(run_root)]) == 0
    out = capsys.readouterr().out
    assert "references: toy.txt (reused from the page)" in out

    runs_dir = tmp_path / "art-crit-runs"
    reused_batch = max(runs_dir.glob("*-draw-the-toy"), key=lambda d: d.name)
    assert (reused_batch / "references/toy.txt").read_text() == "a reference"
    [run_dir] = [d for d in reused_batch.iterdir() if (d / "work").is_dir()]
    assert (run_dir / "work/references/toy.txt").read_text() == "a reference"
    assert "- ./references/toy.txt" in (run_dir / "harness/brief.md").read_text()

    # an explicit --ref replaces the page's set rather than adding to it
    assert main(["run", "--yes", "--page", "draw-the-toy", "-m", "openai-codex/gpt-6-luna:low",
                 "--ref", "other.txt", "--root", str(run_root)]) == 0
    assert "references: other.txt" in capsys.readouterr().out
    explicit_batch = max(runs_dir.glob("*-draw-the-toy"), key=lambda d: d.name)
    assert explicit_batch != reused_batch
    [run_dir] = [d for d in explicit_batch.iterdir() if (d / "work").is_dir()]
    brief = (run_dir / "harness/brief.md").read_text()
    assert "- ./references/other.txt" in brief and "toy.txt" not in brief
    assert not (run_dir / "work/references/toy.txt").exists()


def test_a_different_prompt_for_an_existing_page_is_refused(run_root, capsys):
    assert main(["run", "--yes", "a spinning cube", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 0
    rc = main(["run", "--yes", "--page", "a-spinning-cube", "a spinning red cube", "-m", "openai-codex/gpt-6-sol:high", "--root", str(run_root)])
    assert rc == 1
    err = capsys.readouterr().err
    assert "different prompt" in err and "a spinning cube" in err and "--change-prompt" in err
    assert len(json.loads((run_root / "docs/data/a-spinning-cube/page.json").read_text())["runs"]) == 1

    # the same prompt is fine, and --change-prompt replaces it on purpose
    assert main(["run", "--yes", "--page", "a-spinning-cube", "a spinning cube", "-m", "openai-codex/gpt-6-sol:medium", "--root", str(run_root)]) == 0
    rc = main(["run", "--yes", "--change-prompt", "--page", "a-spinning-cube", "a spinning red cube", "-m", "openai-codex/gpt-6-sol:high", "--root", str(run_root)])
    assert rc == 0
    assert json.loads((run_root / "docs/data/a-spinning-cube/page.json").read_text())["prompt"] == "a spinning red cube"
    assert len(json.loads((run_root / "docs/data/a-spinning-cube/page.json").read_text())["runs"]) == 3


def test_page_without_prompt_must_exist(run_root, capsys):
    assert main(["run", "--yes", "--page", "nope", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 1
    assert "reuse its prompt" in capsys.readouterr().err



# --- Agy and Grok Build harness -------------------------------------------------------------------


def test_agy_and_grok_planning():
    assert plan_for(["agy:gemini-3.8-flash"], None) == [
        ("agy", "gemini-3.8-flash", "low"), ("agy", "gemini-3.8-flash", "high")]
    with pytest.raises(CritError, match="medium not supported"):
        plan_for(["agy:gemini-3.8-flash:medium"])
    assert plan_for(["grok-build:grok-4.7:low,xhigh"]) == [
        ("grok-build", "grok-4.7", "low"), ("grok-build", "grok-4.7", "xhigh")]
    with pytest.raises(CritError, match="xhigh not supported"):
        plan_for(["grok-build:grok-4.5:xhigh"])


@pytest.mark.parametrize("harness,model,env_name", [
    ("agy", "gemini-3.8-flash:high", "FAKE_AGY_ARGV"),
    ("grok-build", "grok-4.7:high", "FAKE_GROK_ARGV"),
])
def test_new_harnesses_run_and_publish_transcripts(run_root, tmp_path, monkeypatch, harness, model, env_name):
    argv_path = tmp_path / "argv.json"
    monkeypatch.setenv(env_name, str(argv_path))
    assert main(["run", "--yes", "--kind", "media", "draw a circle", "-m", f"{harness}:{model}",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/draw-a-circle/page.json").read_text())["runs"]
    assert run["harness"]["name"] == harness and run["state"] == "complete"
    assert run["output"]["ok"] is True
    assert run["metrics"]["tool_calls"] == 1
    assert run["metrics"]["tokens_total"] == (14 if harness == "agy" else 30)
    assert run["metrics"]["tokens_reasoning"] == (2 if harness == "agy" else 4)
    assert run["metrics"]["cost_usd"] == (0 if harness == "agy" else 0.008)
    argv = json.loads(argv_path.read_text())
    assert argv[argv.index("--model") + 1] == ("gemini-3.8-flash-high" if harness == "agy" else "grok-4.7")
    if harness == "agy":
        assert "--effort" not in argv and "--dangerously-skip-permissions" in argv
    else:
        assert argv[argv.index("--reasoning-effort") + 1] == "high"
        assert "streaming-messages-json" in argv and "Agent" in argv and "--no-subagents" in argv
    run_dir = run_root / "docs/data/draw-a-circle/runs" / run["id"]
    assert not (run_dir / "session/events.jsonl").exists()
    convo = json.loads((run_dir / "session/conversation.json").read_text())
    msgs = [e["message"] for e in convo if e["type"] == "message"]
    assert msgs[0]["role"] == "user"
    calls = [b for m in msgs for b in m["content"] if b["type"] == "toolCall"]
    assert calls[0]["name"] == ("bash" if harness == "agy" else "read")
    assert len([m for m in msgs if m["role"] == "toolResult"]) == 1
    assert "Done" in json.dumps(convo)


@pytest.mark.parametrize("harness,model,error", [("agy", "gemini-3.8-flash:low", "FAKE_AGY_ERROR"),
                                                ("grok-build", "grok-4.7:low", "FAKE_GROK_ERROR")])
def test_new_harness_error_result(run_root, monkeypatch, harness, model, error):
    monkeypatch.setenv(error, "1")
    assert main(["run", "--yes", "--kind", "media", "broken circle", "-m", f"{harness}:{model}",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/broken-circle/page.json").read_text())["runs"]
    assert run["state"] == "failed" and "model error" in run["error"]


def test_agy_stream_deduplicates_steps_and_preserves_result_fallback():
    events = [{"event": "step_update", "step_update": {"step_index": 3, "step_type": "tool", "state": "ACTIVE"}},
              {"event": "step_update", "step_update": {"step_index": 3, "step_type": "tool", "state": "DONE",
                                                        "tool_info": {"name": "run_command", "parameters": {"CommandLine": "pwd"}, "output": "ok"}}},
              {"event": "result", "result": {"status": "SUCCESS", "response": "finished"}}]
    entries = convert_agy_stream(events, "brief", "high")
    assert sum(b.get("type") == "toolCall" for e in entries for b in e.get("message", {}).get("content", [])) == 1
    assert entries[-1]["message"]["content"][0]["text"] == "finished"
    assert agy_metrics(events, "high")["tool_calls"] == 1
    assert agy_metrics(events[:-1], "high")["ended_in_error"]


def test_agy_stream_joins_a_response_into_one_message():
    # A response streams as many ACTIVE deltas, and its DONE event carries the remainder: one assistant message, not one per delta.
    deltas = [("ACTIVE", "I made **a"), ("ACTIVE", "n octopus** and"), ("DONE", " [a link](x).")]
    events = [{"event": "step_update", "step_update": {"step_index": 5, "step_type": "agent_response", "state": state, "text_delta": text}}
              for state, text in deltas]
    entries = convert_agy_stream(events + [{"event": "result", "result": {"status": "SUCCESS"}}], "brief", "high")
    texts = [b["text"] for e in entries if e.get("type") == "message" and e["message"]["role"] == "assistant"
             for b in e["message"]["content"]]
    assert texts == ["I made **an octopus** and [a link](x)."]


def test_grok_missing_result_fails_instead_of_publishing_success(tmp_path):
    (tmp_path / "events.jsonl").write_text(json.dumps({"type": "assistant", "message": {"id": "m", "content": []}}) + "\n")
    m = GrokBuild().metrics(tmp_path, "low")
    assert m["ended_in_error"] and "no final result" in m["error_message"]


def test_new_harness_model_listing(capsys):
    assert main(["models", "--harness", "agy", "gemini-3.8"]) == 0
    assert "gemini-3.8-flash: low, high" in capsys.readouterr().out
    assert main(["models", "--harness", "grok-build", "grok-4.5"]) == 0
    assert "grok-4.5: low, medium, high" in capsys.readouterr().out


# --- Muse Code harness -----------------------------------------------------------------------------


def test_muse_code_planning():
    assert plan_for(["muse-code:muse-spark-1.3:low,max"]) == [
        ("muse-code", "muse-spark-1.3", "low"), ("muse-code", "muse-spark-1.3", "max")]
    with pytest.raises(CritError, match="max not supported"):
        plan_for(["muse-code:muse-spark-1.2:xhigh,max"])


def test_muse_code_runs_and_publishes_transcript(run_root, tmp_path, monkeypatch):
    argv_path = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_MUSE_ARGV", str(argv_path))
    assert main(["run", "--yes", "--kind", "media", "draw a circle", "-m", "muse-code:muse-spark-1.3:high",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/draw-a-circle/page.json").read_text())["runs"]
    assert run["harness"]["name"] == "muse-code" and run["model"] == "meta/muse-spark-1.3"
    assert run["state"] == "complete" and run["output"]["ok"] is True
    assert "-mc-" in run["id"]
    # input excludes cached tokens (100-60 + 130-100); the reminder run's usage is not counted
    assert run["metrics"]["tokens_total"] == 100 and run["metrics"]["tokens_reasoning"] == 10
    assert run["metrics"]["turns"] == 2 and run["metrics"]["tool_calls"] == 1
    assert run["metrics"]["cost_usd"] == pytest.approx((70 * 1.25 + 160 * 0.15 + 30 * 4.25) / 1_000_000)
    assert run["metrics"]["cost_estimated"] is True
    argv = json.loads(argv_path.read_text())
    assert argv[argv.index("--model") + 1] == "muse-spark-1.3"
    assert argv[argv.index("--reasoning-effort") + 1] == "high"
    assert "--json" in argv and "--disable-reminders" in argv and "--disable-web-tools" in argv
    assert "--yolo" not in argv and argv[-2] == "--" and "draw a circle" in argv[-1]
    run_dir = run_root / "docs/data/draw-a-circle/runs" / run["id"]
    assert not (run_dir / "session/export.json").exists() and not (run_dir / "session/events.jsonl").exists()
    msgs = [e["message"] for e in json.loads((run_dir / "session/conversation.json").read_text()) if e["type"] == "message"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "toolResult", "assistant"]
    call = msgs[1]["content"][1]
    assert msgs[1]["content"][0]["type"] == "thinking" and call["name"] == "read" and call["arguments"] == {"path": "output/circle.svg"}
    assert msgs[1]["usage"]["input"] == 40 and msgs[1]["usage"]["cacheRead"] == 60
    assert msgs[2]["toolCallId"] == call["id"] == "call_1" and msgs[2]["durationMs"] == 100
    assert msgs[3]["content"][0]["text"] == "Done."


@pytest.mark.parametrize("model, expected", [
    ("meta/muse-spark-1.3-contributor", (20 * .10 + 60 * .002 + 30 * .20) / 1_000_000),
    ("meta/muse-wonder-1.0", (20 * 4 + 60 * .20 + 30 * 20) / 1_000_000),
    ("meta/muse-wonder-full-1.0", (20 * 4 + 60 * .20 + 30 * 20) / 1_000_000),
    ("meta/muse-wonder-full-1.0-contributor", (20 * 4 + 60 * .20 + 30 * 20) / 1_000_000),
    ("meta/muse-wonder-1.0-contributor", (20 * 4 + 60 * .20 + 30 * 20) / 1_000_000),
    ("meta/unknown", None),
])
def test_muse_api_equivalent_cost(model, expected):
    metrics = {"turns": 2, "tokens": {"input": 10, "cacheWrite": 10, "cacheRead": 60, "output": 30, "reasoning": 8},
               "cost_usd": 0.0}
    result = MuseCode().finish(None, model, metrics)
    if expected is None:
        assert result["cost_usd"] == 0 and "cost_estimated" not in result
    else:
        assert result["cost_usd"] == pytest.approx(expected) and result["cost_estimated"] is True
        if "muse-wonder" in model and ("contributor" in model or "full" in model):
            assert result["cost_estimate_proxy"] == "meta/muse-wonder-1.0"
        else:
            assert "cost_estimate_proxy" not in result
    assert MuseCode().finish(None, model, {"turns": 0, "tokens": metrics["tokens"], "cost_usd": 0})["cost_usd"] == 0


def test_reimport_prices_an_older_muse_run(run_root):
    assert main(["run", "--yes", "--no-publish", "--kind", "media", "draw a circle",
                 "-m", "muse-code:muse-spark-1.3:low", "--root", str(run_root)]) == 0
    [batch] = (run_root.parent / "art-crit-runs").glob("*")
    [run_dir] = [d for d in batch.iterdir() if (d / "run.json").is_file()]
    record = json.loads((run_dir / "run.json").read_text())
    record["metrics"]["cost_usd"] = 0
    record["metrics"].pop("cost_estimated")
    (run_dir / "run.json").write_text(json.dumps(record))
    assert main(["import", str(run_dir), "--root", str(run_root)]) == 0
    published = json.loads((run_root / "docs/data/draw-a-circle/runs" / record["id"] / "run.json").read_text())
    assert published["metrics"]["cost_estimated"] is True
    assert published["metrics"]["cost_usd"] > 0
    assert json.loads((run_dir / "run.json").read_text())["metrics"]["cost_usd"] == 0  # archive untouched


def test_muse_code_failed_terminal_fails_the_run(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_MUSE_ERROR", "1")
    assert main(["run", "--yes", "--kind", "media", "broken circle", "-m", "muse-code:muse-spark-1.3:low",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/broken-circle/page.json").read_text())["runs"]
    assert run["state"] == "failed" and "model error" in run["error"]


def test_muse_export_without_a_terminal_event_is_an_error():
    assert muse_metrics({}, "low")["ended_in_error"]
    entries = convert_muse_export({}, "brief", "low")
    assert [e["type"] for e in entries] == ["session", "model_change", "thinking_level_change", "message"]


def test_muse_command_exports_the_session_after_exec(tmp_path):
    cmd = MuseCode().command("muse-spark-1.3", "low", "brief", tmp_path)
    assert cmd[:2] == ["bash", "-c"] and cmd[3] == "muse-code" and cmd[4] == "muse"
    assert cmd[cmd.index("--session-id") + 1] == cmd[5] and cmd[6] == str(tmp_path / "export.json")


def test_muse_models_come_from_the_cached_catalog(tmp_path, monkeypatch):
    tiers = lambda *names: [{"tier": n, "description": None} for n in names]
    rows = [{"model_id": "muse-wonder-1.0", "reasoning_effort_variants": tiers("max", "low", "ultra")},
            {"model_id": "muse-wonder-1.0-contributor", "visibility": "hidden", "reasoning_effort_variants": tiers("low")},
            {"model_id": "muse-image-1.0", "reasoning_effort_variants": None}]
    (tmp_path / "meta.json").write_text(json.dumps({"rows": rows}))
    (tmp_path / "broken.json").write_text("{")
    monkeypatch.setattr(MuseCode, "CATALOG_DIR", tmp_path)
    muse = MuseCode()
    assert muse.models() == ["muse-wonder-1.0", "muse-wonder-1.0-contributor"]
    assert muse.levels("muse-wonder-1.0") == ["low", "max"]  # LEVEL_ORDER only, in order
    assert plan_for(["muse-code:muse-wonder-1.0:max"]) == [("muse-code", "muse-wonder-1.0", "max")]
    with pytest.raises(CritError, match="muse-spark-1.3"):
        plan_for(["muse-code:muse-spark-1.3:low"])


def test_muse_model_listing(capsys):
    assert main(["models", "--harness", "muse-code", "muse-wonder"]) == 0
    assert "muse-wonder-1.0-contributor: minimal, low, medium, high, xhigh, max" in capsys.readouterr().out


# --- Codex harness -----------------------------------------------------------------------------------


def test_codex_planning():
    assert plan_for(["codex:gpt-6-sol:low,max"]) == [
        ("codex", "gpt-6-sol", "low"), ("codex", "gpt-6-sol", "max")]
    with pytest.raises(CritError, match="xhigh not supported"):
        plan_for(["codex:gpt-6-luna:xhigh"])
    with pytest.raises(CritError, match="unknown model 'gpt-hidden'"):
        plan_for(["codex:gpt-hidden:low"])  # hidden catalog rows aren't listed


def test_codex_runs_and_publishes_transcript(run_root, tmp_path, monkeypatch):
    argv_path = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_CODEX_ARGV", str(argv_path))
    assert main(["run", "--yes", "--kind", "media", "draw a circle", "-m", "codex:gpt-6-sol:high",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/draw-a-circle/page.json").read_text())["runs"]
    assert run["harness"]["name"] == "codex" and run["model"] == "openai/gpt-6-sol"
    assert run["state"] == "complete" and run["output"]["ok"] is True
    assert "-cx-" in run["id"]
    # input excludes cached + cache-write tokens (130-100-10); reasoning is part of output
    assert run["metrics"]["tokens_total"] == 50 and run["metrics"]["tokens_reasoning"] == 7
    assert run["metrics"]["turns"] == 1 and run["metrics"]["tool_calls"] == 2
    assert run["metrics"]["cost_usd"] == 0
    argv = json.loads(argv_path.read_text())
    assert argv[argv.index("-m") + 1] == "gpt-6-sol"
    assert 'model_reasoning_effort="high"' in argv and "--json" in argv and "--ephemeral" in argv
    assert "--dangerously-bypass-approvals-and-sandbox" in argv
    run_dir = run_root / "docs/data/draw-a-circle/runs" / run["id"]
    assert not (run_dir / "session/events.jsonl").exists()  # the raw stream is never published
    msgs = [e["message"] for e in json.loads((run_dir / "session/conversation.json").read_text()) if e["type"] == "message"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "toolResult", "assistant", "toolResult", "assistant"]
    assert msgs[1]["content"][0]["type"] == "thinking"
    call = msgs[1]["content"][1]
    assert call["name"] == "bash" and call["arguments"] == {"command": "ls"}
    assert msgs[2]["toolCallId"] == call["id"] and msgs[2]["isError"] is False
    assert msgs[3]["content"][0]["name"] == "file_change"
    assert msgs[5]["content"][0]["text"] == "Done: built it."
    assert msgs[5]["usage"]["input"] == 20 and msgs[5]["usage"]["cacheRead"] == 100


def test_codex_failed_turn_fails_the_run(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_CODEX_ERROR", "1")
    assert main(["run", "--yes", "--kind", "media", "broken circle", "-m", "codex:gpt-6-luna:low",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/broken-circle/page.json").read_text())["runs"]
    assert run["state"] == "failed" and "model error" in run["error"]


def test_codex_missing_result_fails_instead_of_publishing_success(tmp_path):
    (tmp_path / "events.jsonl").write_text(json.dumps({"type": "turn.started"}) + "\n")
    m = Codex().metrics(tmp_path, "low")
    assert m["ended_in_error"] and "no final result" in m["error_message"]
    entries = convert_codex_stream([{"type": "turn.started"}], "brief", "low")
    assert [e["type"] for e in entries] == ["session", "model_change", "thinking_level_change", "message"]


def test_codex_command_and_model_listing(tmp_path, capsys):
    cmd = Codex().command("gpt-6-sol", "low", "brief", tmp_path)
    assert cmd[:2] == ["codex", "exec"] and cmd[-1] == "brief"
    assert main(["models", "--harness", "codex", "gpt-6"]) == 0
    out = capsys.readouterr().out
    assert "gpt-6-sol: low, medium, high, xhigh, max" in out  # `ultra` dropped: not in LEVEL_ORDER
    assert "gpt-hidden" not in out


# --- Ori harness -----------------------------------------------------------------------------------

ORI_ROWS = [
    {"id": "deepseek/deepseek-v4.1-flash", "supported_parameters": ["tools", "reasoning", "reasoning_effort"],
     "architecture": {"output_modalities": ["text"]}},
    {"id": "nvidia/nemotron-3.5-super-vl:free", "supported_parameters": ["tools", "reasoning"],
     "architecture": {"output_modalities": ["text"]}},
    {"id": "someone/painter", "supported_parameters": [],
     "architecture": {"output_modalities": ["image"]}},
]


@pytest.fixture
def ori_catalog(monkeypatch):
    """Ori's model rows as OpenRouter publishes them, without the network (see conftest)."""
    monkeypatch.setattr(Ori, "openrouter_catalog", lambda self: ORI_ROWS)


@pytest.fixture
def fake_ori_on_path(fake_pi_on_path, monkeypatch):
    """The fake `ori` (tests/fixtures/fake_pi/ori, on PATH through the autouse fixture above), with no knobs set."""
    monkeypatch.delenv("FAKE_ORI_ERROR", raising=False)
    monkeypatch.delenv("FAKE_ORI_ARGV", raising=False)


def test_ori_models_and_levels_come_from_openrouter(ori_catalog):
    assert Ori().models() == ["deepseek/deepseek-v4.1-flash", "nvidia/nemotron-3.5-super-vl:free"]  # no image models
    assert Ori().levels("deepseek/deepseek-v4.1-flash") == ["off", "minimal", "low", "medium", "high", "xhigh", "max"]
    assert Ori().levels("nvidia/nemotron-3.5-super-vl:free") == ["off"]  # no reasoning_effort: `off` only, like pi
    assert plan_for(["ori:deepseek/deepseek-v4.1-flash:high"]) == [("ori", "deepseek/deepseek-v4.1-flash", "high")]
    assert plan_for(["ori:deepseek/deepseek-v4.1-flash:off"]) == [("ori", "deepseek/deepseek-v4.1-flash", "off")]
    with pytest.raises(CritError, match="xhigh not supported"):
        plan_for(["ori:nvidia/nemotron-3.5-super-vl:free:xhigh"])
    with pytest.raises(CritError, match="unknown model 'someone/painter'"):
        plan_for(["ori:someone/painter:low"])


def test_ori_unreadable_catalog_is_a_clear_error():
    with pytest.raises(CritError, match="cannot read OpenRouter's model list.*no network in tests"):
        Ori().models()  # the real fetch; conftest fails every urlopen


def test_ori_version_reads_its_json_envelope(fake_ori_on_path):
    assert Ori().version() == "9.9.9-fake"  # piped, ori answers {"data": {"version": ...}}


def test_ori_runs_and_publishes_transcript(run_root, tmp_path, monkeypatch, ori_catalog, fake_ori_on_path):
    argv_path = tmp_path / "argv.json"
    monkeypatch.setenv("FAKE_ORI_ARGV", str(argv_path))
    assert main(["run", "--yes", "--kind", "media", "draw a circle", "-m", "ori:deepseek/deepseek-v4.1-flash:high",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/draw-a-circle/page.json").read_text())["runs"]
    assert run["harness"]["name"] == "ori" and run["harness"]["version"] == "9.9.9-fake"
    assert run["model"] == "deepseek/deepseek-v4.1-flash"  # the OpenRouter slug: the site groups it by vendor
    assert run["state"] == "complete" and run["output"]["ok"] is True and "-ori-" in run["id"]
    # OpenRouter's own numbers: input excludes the cached tokens, and its cost is what it charged
    assert run["metrics"]["tokens_total"] == 60 and run["metrics"]["tokens_cache_read"] == 100
    assert run["metrics"]["turns"] == 1 and run["metrics"]["tool_calls"] == 1
    assert run["metrics"]["cost_usd"] == 0.005
    argv = json.loads(argv_path.read_text())
    assert argv[:3] == ["code", "--harness", "ori"] and argv[argv.index("--output") + 1] == "jsonl"
    assert argv[argv.index("--model") + 1] == "deepseek/deepseek-v4.1-flash"
    assert argv[argv.index("--reasoning-effort") + 1] == "high"
    assert argv[argv.index("--approvals") + 1] == "self-drive"
    run_dir = run_root / "docs/data/draw-a-circle/runs" / run["id"]
    assert not (run_dir / "session/events.jsonl").exists()  # the raw stream is never published
    msgs = [e["message"] for e in json.loads((run_dir / "session/conversation.json").read_text()) if e["type"] == "message"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "toolResult", "assistant"]
    assert msgs[1]["content"] == [{"type": "thinking", "thinking": "Plan the files."},
                                  {"type": "toolCall", "id": "call_1", "name": "shell", "arguments": {"command": "ls"}}]
    assert msgs[1]["stopReason"] == "toolUse"
    assert msgs[2]["toolCallId"] == "call_1" and msgs[2]["isError"] is False
    assert msgs[2]["durationMs"] == 26 and msgs[2]["content"][0]["text"] == "output/circle.svg"
    assert msgs[3]["content"] == [{"type": "text", "text": "Done: built it."}]  # deltas joined
    assert msgs[3]["usage"]["input"] == 30 and msgs[3]["usage"]["cacheRead"] == 100


def test_ori_failed_turn_fails_the_run(run_root, monkeypatch, ori_catalog, fake_ori_on_path):
    monkeypatch.setenv("FAKE_ORI_ERROR", "1")
    assert main(["run", "--yes", "--kind", "media", "broken circle", "-m", "ori:deepseek/deepseek-v4.1-flash:low",
                 "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/broken-circle/page.json").read_text())["runs"]
    assert run["state"] == "failed" and run["error"] == "The turn was cancelled."  # ori's own message, not its log
    transcript = json.loads((run_root / "docs/data/broken-circle/runs" / run["id"] / "session/conversation.json").read_text())
    results = [e["message"] for e in transcript if (e.get("message") or {}).get("role") == "toolResult"]
    assert results[0]["isError"] is True and results[0]["content"][0]["text"] == "no such file"
    last = [e["message"] for e in transcript if e["type"] == "message"][-1]
    assert last["stopReason"] == "error" and last["content"][0]["text"] == "The turn was cancelled."


def test_ori_stream_without_a_settled_turn_fails_instead_of_publishing_success(tmp_path):
    (tmp_path / "events.jsonl").write_text(json.dumps({"kind": "event", "event": {"type": "runtime.event", "event": {
        "type": "turn.started", "payload": {"prompt": "p"}}}}) + "\n")
    metrics = Ori().metrics(tmp_path, "low")
    assert metrics["ended_in_error"] and "no final result" in metrics["error_message"]
    entries = convert_ori_stream([{"kind": "event", "event": {"type": "runtime.event", "event": {
        "type": "turn.started", "payload": {}}}}], "brief", "low")
    assert [e["type"] for e in entries] == ["session", "model_change", "thinking_level_change", "message"]


def test_ori_result_error_without_a_turn_is_reported(tmp_path):
    lines = [{"kind": "event", "event": {"type": "audit.event", "audit": {}}},
             {"kind": "result", "ok": False, "sessionId": "s",
              "error": {"message": "The requested model ID does not exist.", "code": "ORI_MODEL_UNKNOWN"}}]
    (tmp_path / "events.jsonl").write_text("".join(json.dumps(line) + "\n" for line in lines))
    metrics = Ori().metrics(tmp_path, "low")
    assert metrics["ended_in_error"] and metrics["error_message"] == "The requested model ID does not exist."
    entries = convert_ori_stream(lines, "brief", "low")
    assert entries[-1]["message"]["stopReason"] == "error"


def test_ori_command_and_model_listing(tmp_path, capsys, ori_catalog):
    cmd = Ori().command("deepseek/deepseek-v4.1-flash", "off", "brief", tmp_path)
    assert cmd[-2:] == ["-p", "brief"] and cmd[cmd.index("--reasoning-effort") + 1] == "none"  # art-crit's off
    assert main(["models", "--harness", "ori", "deepseek"]) == 0
    assert capsys.readouterr().out == "deepseek/deepseek-v4.1-flash: off, minimal, low, medium, high, xhigh, max\n"


# --- Claude Code harness ---------------------------------------------------------------------------


def test_claude_code_prefix_resolves_aliases_and_levels():
    assert plan_for(["claude-code:opus:high"], None) == [("claude-code", "claude-opus-5-5", "high")]
    assert plan_for(["claude-code:sonnet:high"], None) == [("claude-code", "claude-sonnet-5-5", "high")]
    assert plan_for(["claude-code:haiku:low"], None) == [("claude-code", "claude-haiku-5-5", "low")]
    assert [l for _, _, l in plan_for(["claude-code:claude-sonnet-5"], None)] == ["low", "medium", "high", "xhigh", "max"]
    with pytest.raises(CritError, match="minimal.*not supported"):
        plan_for(["claude-code:claude-opus-5-5:minimal"], None)
    with pytest.raises(CritError, match="unknown model 'claude-opus-9'.*claude-opus-5-5"):
        plan_for(["claude-code:claude-opus-9:high"], None)
    # A level the CLI would silently clamp isn't offered, so a run never claims it.
    assert [l for _, _, l in plan_for(["claude-code:claude-opus-4-6"], None)] == ["low", "medium", "high", "max"]
    assert [l for _, _, l in plan_for(["claude-code:claude-sonnet-4-6"], None)] == ["low", "medium", "high", "max"]
    with pytest.raises(CritError, match="xhigh not supported"):
        plan_for(["claude-code:claude-opus-4-6:xhigh"], None)
    with pytest.raises(CritError, match="unknown model 'claude-haiku-4-5'"):
        plan_for(["claude-code:claude-haiku-4-5:low"], None)


def _claude_image_result(data):
    events = [
        {"type": "assistant", "message": {"id": "m1", "content": [{"type": "tool_use", "id": "t1", "name": "Read", "input": {"file_path": "shot.png"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": [
            {"type": "text", "text": "read it"}, {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}}]}]}},
    ]
    [result] = [e["message"] for e in convert_claude_stream(events, "brief", "low") if e.get("message", {}).get("role") == "toolResult"]
    return result["content"]


def test_claude_image_tool_results_keep_only_their_size_when_not_an_image():
    text, image = _claude_image_result("A" * 4096)  # decodes, but isn't an image: no thumbnail, never the raw data
    assert text == {"type": "text", "text": "read it"}
    assert image == {"type": "image", "mimeType": "image/jpeg", "sourceMimeType": "image/png", "bytes": 3072}


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_claude_image_tool_results_become_small_jpeg_thumbnails():
    png = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=1280x720", "-frames:v", "1",
                          "-f", "image2pipe", "-c:v", "png", "pipe:1"], capture_output=True, check=True).stdout
    _, image = _claude_image_result(base64.b64encode(png).decode())
    thumb = base64.b64decode(image["data"])
    assert image["bytes"] == len(png) and image["sourceMimeType"] == "image/png"
    assert thumb.startswith(b"\xff\xd8") and len(thumb) < 40_000  # a JPEG, much smaller than the original


def test_mixed_harness_batch_records_each_runs_harness_and_session(run_root, monkeypatch, tmp_path):
    argv_file = tmp_path / "claude-argv.json"
    monkeypatch.setenv("FAKE_CLAUDE_ARGV", str(argv_file))
    monkeypatch.setenv("CLAUDECODE", "1")  # as when art-crit itself runs inside Claude Code
    rc = main(["run", "--yes", "mixed harness", "-m", "claude-code:claude-opus-5-5:high",
               "-m", "anthropic/claude-opus-5-5:high", "--root", str(run_root)])
    assert rc == 0
    results = {r["harness"]["name"]: r for r in json.loads((run_root / "docs/data/mixed-harness/page.json").read_text())["runs"]}
    assert set(results) == {"pi", "claude-code"}
    cc, pi = results["claude-code"], results["pi"]
    assert cc["model"] == pi["model"] == "anthropic/claude-opus-5-5"
    assert cc["id"].startswith("claude-opus-5-5-cc-high-") and pi["id"].startswith("claude-opus-5-5-high-")
    assert cc["harness"]["version"] == "9.9.9-fake"
    assert cc["state"] == "complete"
    m = cc["metrics"]
    assert (m["turns"], m["tool_calls"], m["cost_usd"]) == (3, 2, 0.0123)
    # tokens from the final result (the stream's per-message usage undercounts output)
    assert (m["tokens_input"], m["tokens_output"], m["tokens_total"], m["tokens_cache_read"]) == (16, 180, 196, 3500)
    assert m["tokens_reasoning"] == 40

    # One direct agent, no personal setup, nothing saved to the user's history, not "nested".
    sent = json.loads(argv_file.read_text())
    for flag in ("--safe-mode", "--no-session-persistence", "--tools=Bash,Read,Write,Edit,Glob,Grep",
                 "--disallowed-tools=Agent,Task", "--disable-slash-commands", "--verbose"):
        assert flag in sent["argv"]
    assert sent["argv"][sent["argv"].index("--effort") + 1] == "high"
    assert sent["argv"][sent["argv"].index("--model") + 1] == "claude-opus-5-5"
    assert sent["env_has_claudecode"] is False

    run_dir = run_root / "docs/data/mixed-harness/runs" / cc["id"]
    assert "events" not in cc["session"] and not (run_dir / "session/events.jsonl").exists()
    convo = json.loads((run_dir / "session/conversation.json").read_text())
    assert [e["message"]["durationMs"] for e in convo if e.get("message", {}).get("role") == "toolResult"] == [5000, 5000]  # tool_use event -> tool_result event
    text = json.dumps(convo)
    assert "signature" not in text and "sess-fake" not in text
    msgs = [e["message"] for e in convo if e["type"] == "message"]
    assert msgs[0]["role"] == "user" and msgs[0]["content"][0]["text"].startswith("mixed harness")
    calls = [b for mm in msgs if mm["role"] == "assistant" for b in mm["content"] if b["type"] == "toolCall"]
    assert [(c["name"], c["arguments"].get("path")) for c in calls] == [("write", "project.godot"), ("bash", None)]
    results_by_call = {mm["toolCallId"]: mm for mm in msgs if mm["role"] == "toolResult"}
    assert results_by_call[calls[1]["id"]]["isError"] is True
    assert [mm["content"][0]["type"] for mm in msgs if mm["role"] == "assistant"] == ["thinking", "toolCall", "text"]
    # timestamps come from the stream: a merged message keeps its first event's, the brief gets the first one
    assert [e["timestamp"][-8:-5] for e in convo if e["type"] == "message"] == [":00", ":00", ":10", ":15", ":20", ":25"]
    page =json.loads((run_root / "docs/data/mixed-harness/page.json").read_text())
    assert page["final_prompt"].startswith("mixed harness\n\nBuild this")


def test_claude_code_error_result_is_a_failed_run(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_ERROR", "1")
    assert main(["run", "--yes", "cc error", "-m", "claude-code:haiku:low", "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/cc-error/page.json").read_text())["runs"]
    assert run["state"] == "failed" and "overloaded" in run["error"]


def test_claude_code_timeout(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_CLAUDE_HANG", "1")
    assert main(["run", "--yes", "--timeout", "1s", "cc hang", "-m", "claude-code:haiku:low", "--root", str(run_root)]) == 0
    [run] = json.loads((run_root / "docs/data/cc-hang/page.json").read_text())["runs"]
    assert run["state"] == "timeout"


def test_claude_code_in_a_model_set_and_models_listing(run_root, capsys):
    write_sets(run_root, 'mix = ["claude-code:sonnet:low", "openai-codex/gpt-6-sol:low"]\n')
    assert main(["run", "--dry-run", "cube", "--set", "mix", "--root", str(run_root)]) == 0
    out = capsys.readouterr().out
    assert "claude-code:claude-sonnet-5-5:low" in out and "openai-codex/gpt-6-sol:low" in out
    assert "harness: claude-code 9.9.9-fake, pi 0.1.0-fake" in out
    assert main(["models", "--harness", "claude-code", "opus"]) == 0
    assert "claude-opus-5-5: low, medium, high, xhigh, max" in capsys.readouterr().out


def test_every_long_option_has_a_short_form():
    import argparse

    from art_crit.cli import build_parser

    sub = next(a for a in build_parser()._actions if isinstance(a, argparse._SubParsersAction))
    for name, parser in sub.choices.items():
        for action in parser._actions:
            longs = [o for o in action.option_strings if o.startswith("--")]
            shorts = [o for o in action.option_strings if not o.startswith("--")]
            # a --no-... option is the negation of one that already has a short form
            assert not longs or shorts or longs[0].startswith("--no-"), f"art-crit {name} {longs[0]} has no short form"
    args = build_parser().parse_args(["run", "-n", "-y", "-k", "web", "-p", "pg", "-t", "T", "-T", "5m", "-b", "b.md", "-c", "-C", "/tmp", "x"])
    assert (args.dry_run, args.yes, args.kind, args.page, args.title, args.timeout, str(args.brief), args.change_prompt, args.publish) == \
        (True, True, "web", "pg", "T", "5m", "b.md", True, True)  # publish defaults to on
    assert build_parser().parse_args(["run", "--no-publish", "x"]).publish is False


def test_bad_run_inputs_fail_before_a_batch_dir_exists(run_root, tmp_path, capsys):
    runs_dir = Config.load(run_root).run.dir
    assert main(["run", "--yes", "--timeout", "banana", "x", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) != 0
    assert "bad duration" in capsys.readouterr().err
    empty_set = tmp_path / "empty.txt"
    empty_set.write_text("# nothing here\n")
    assert main(["run", "--yes", "x", "--set", str(empty_set), "--root", str(run_root)]) != 0
    assert "at least one -m" in capsys.readouterr().err
    assert not runs_dir.exists() or not list(runs_dir.iterdir())


def test_a_monitor_stop_kills_the_agent(run_root, monkeypatch):
    """`art-crit serve`'s monitor only writes harness/stop; the runner owns the process and kills it."""
    import threading

    from art_crit.serve import stop_run
    monkeypatch.setenv("FAKE_PI_HANG", "1")
    args = ["run", "--yes", "stop me", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]
    threading.Thread(target=main, daemon=True, args=(args,)).start()
    deadline = time.time() + 20
    runs = run_root.parent / "art-crit-runs"
    while time.time() < deadline and not list(runs.glob("*-stop-me/*/work/fake_pi.pid")):
        time.sleep(0.05)
    [pid_file] = runs.glob("*-stop-me/*/work/fake_pi.pid")
    run_dir = pid_file.parent.parent
    assert stop_run(run_root / "docs", run_dir.parent.name, run_dir.name) is None
    while time.time() < deadline and not (run_dir / "run.json").is_file():
        time.sleep(0.1)
    record = json.loads((run_dir / "run.json").read_text())
    assert (record["state"], record["error"]) == ("failed", "stopped from the local monitor")
    assert (run_dir / "harness" / "stop").is_file()


# --- Greater Good Bench: the six pages in prompts/README.md (ADR-0037) ---------------------------------------------------

REPO = Path(__file__).parent.parent
FRONTIER = Config.load(REPO).sets["frontier"]
# (kind, page, title) of each page, in prompts/README.md's order.
BENCH_PAGES = [("media", "svg", "SVG"), ("web", "website", "Website"), ("blender", "3d-model", "3D model"),
               ("godot", "game", "Game"), ("media", "animation", "Animation"), ("text", "essay", "Essay")]


@pytest.mark.parametrize("kind, page, title", BENCH_PAGES)
def test_bench_page_dry_run_plans_the_frontier_set(run_root, monkeypatch, capsys, kind, page, title):
    """Each page's documented dry run plans all nine frontier models at -e's level, against the repo's own set."""
    flags = f'--kind {kind} -p {page} -t "{title}" --set frontier -e high -T 2h -j 4'
    readme = (REPO / "prompts/README.md").read_text()
    assert f"uv run art-crit run --dry-run {flags} -f prompts/{page}.md" in readme
    assert f"uv run art-crit run {flags} -f prompts/{page}.md" in readme
    assert len(FRONTIER) == 9 and all(m.startswith("openrouter/") and ":" not in m for m in FRONTIER)
    monkeypatch.setenv("FAKE_PI_EXTRA_MODELS", ",".join(FRONTIER))
    cfg = run_root / "art-crit.toml"
    cfg.write_text(cfg.read_text() + "\n[sets]\nfrontier = " + json.dumps(FRONTIER) + "\n")
    argv = ["run", "--dry-run", "--kind", kind, "-p", page, "-t", title, "--set", "frontier", "-e", "high",
            "-T", "2h", "-j", "4", "-f", str(REPO / "prompts" / f"{page}.md"), "--root", str(run_root)]
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert f"kind: {kind}" in out and f"page: {page} (new, title: '{title}')" in out
    assert f"prompt: {(REPO / 'prompts' / f'{page}.md').read_text().strip()}" in out  # the whole file, nothing else
    for i, model in enumerate(FRONTIER, 1):
        assert f"{i}. {model}:high" in out
