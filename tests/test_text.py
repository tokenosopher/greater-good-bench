"""The `text` kind: one Markdown file in ./output/ (finalize, verify, stage, keep_source), and `art-crit run --kind text`
end to end with the fake pi (tests/fixtures/fake_pi/pi writes ./output/essay.md for a text brief)."""

import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from art_crit.cli import main
from art_crit.kinds import KINDS
from art_crit.kinds.text import MAX_BYTES, Text, excerpt_of, title_of

FAKE_PI = Path(__file__).parent / "fixtures" / "fake_pi"
ESSAY = """# A *Small* Essay

Chairs are **furniture** with a [long history](https://example.com/chairs) and `four` legs.

## Why

- they hold you up
- they ~~fall~~ wobble

> Sit down.
"""


@pytest.fixture
def work(tmp_path):
    (tmp_path / "work" / "output").mkdir(parents=True)
    return tmp_path / "work"


def finalize(work):
    out = work.parent / "out"
    return Text().finalize(work, out), out


def manifest(out):
    return json.loads((out / "manifest.json").read_text())


def test_text_is_a_registered_kind_needing_no_tools():
    kind = KINDS["text"]()
    assert kind.tools == () and kind.missing_tools() == [] and kind.activity == "checking"
    brief = kind.brief()
    assert brief.startswith("{prompt}\n") and "{tools}" not in brief and "./output/" in brief and "200 KB" in brief


def test_no_markdown_file_is_the_error(work):
    (work / "output" / "notes.txt").write_text("not markdown")
    (ok, error), out = finalize(work)
    assert (ok, error) == (False, "no Markdown file in ./output/")
    assert manifest(out)["ok"] is False and not (out / "text.md").exists()


def test_a_missing_output_dir_is_the_same_error(tmp_path):
    (ok, error), _ = finalize(tmp_path / "empty")
    assert (ok, error) == (False, "no Markdown file in ./output/")


def test_two_markdown_files_are_named_in_the_error(work):
    (work / "output" / "a.md").write_text("# A\n")
    (work / "output" / "sub").mkdir()
    (work / "output" / "sub" / "b.md").write_text("# B\n")
    (ok, error), _ = finalize(work)
    assert not ok and error == "2 Markdown files in ./output/ (a.md, sub-b.md); expected exactly one"


def test_one_good_file_is_the_output_and_other_files_are_ignored(work):
    (work / "output" / "essay.md").write_text(ESSAY)
    (work / "output" / "draft.txt").write_text("ignored")
    (ok, error), out = finalize(work)
    assert (ok, error) == (True, None)
    assert (out / "text.md").read_text() == ESSAY
    m = manifest(out)
    assert m == {"ok": True, "bytes": len(ESSAY.encode()), "words": len(ESSAY.split()), "title": "A Small Essay", "errors": []}
    assert Text().verify(out) == {"ok": True, "bytes": m["bytes"], "words": m["words"]}


def test_an_oversized_file_is_an_error(work):
    (work / "output" / "big.md").write_text("word " * (MAX_BYTES // 5 + 1))
    (ok, error), _ = finalize(work)
    assert not ok and error.startswith("big.md:") and "larger than 200 KB" in error


def test_an_undecodable_file_is_an_error(work):
    (work / "output" / "bad.md").write_bytes(b"# Title\n\xff\xfe not utf-8")
    (ok, error), _ = finalize(work)
    assert (ok, error) == (False, "bad.md: not UTF-8 text")


def test_a_blank_file_is_an_error(work):
    (work / "output" / "blank.md").write_text("  \n\n\t\n")
    (ok, error), _ = finalize(work)
    assert (ok, error) == (False, "blank.md: empty")


def test_verify_rechecks_the_file_and_never_returns_none(tmp_path):
    assert Text().verify(tmp_path)["ok"] is False  # nothing there
    (tmp_path / "text.md").write_bytes(b"\xff")
    assert Text().verify(tmp_path)["ok"] is False
    (tmp_path / "text.md").write_text("hello there world")
    assert Text().verify(tmp_path) == {"ok": True, "bytes": 17, "words": 3}


def test_title_is_the_first_h1_outside_code_as_plain_text():
    assert title_of("intro\n\n## Not this\n\n```\n# nor this\n```\n# The *Real* One #\n# Later\n") == "The Real One"
    assert title_of("Setext\n======\n\n## h2 only\n") is None


def test_excerpt_is_plain_text_without_the_title_cut_at_a_word():
    assert excerpt_of(ESSAY) == "Chairs are furniture with a long history and four legs. Why they hold you up they fall wobble Sit down."
    long = "# T\n\n" + " ".join(f"word{i}" for i in range(200))
    cut = excerpt_of(long)
    assert cut.endswith("…") and len(cut) <= 301 and cut[:-1] in long and long[long.index(cut[:-1]) + len(cut) - 1] == " "
    assert excerpt_of("<b>raw</b> html and snake_case_name\n\n---\n") == "raw html and snake_case_name"


def test_stage_publishes_the_cleaned_file_with_title_words_and_excerpt(work, tmp_path):
    (work / "output" / "essay.md").write_text(ESSAY.replace("Chairs", "Chairs in SECRET-PATH"))
    _, out = finalize(work)
    run_dir = tmp_path / "run"
    cleaned = lambda src, dest: (dest.parent.mkdir(parents=True, exist_ok=True), dest.write_text(src.read_text().replace("SECRET-PATH", "~")))
    staged = Text().stage(out, run_dir, SimpleNamespace(write_text=cleaned))
    assert staged.thumb is None and staged.engine is None
    assert set(staged.fields) == {"text", "bytes", "words", "title", "excerpt"}
    assert staged.fields["text"] == "text/text.md" and staged.fields["title"] == "A Small Essay"
    assert "SECRET-PATH" not in (run_dir / "text/text.md").read_text()
    assert staged.fields["excerpt"].startswith("Chairs in ~ are furniture")  # from the cleaned copy, never the raw one


def test_keep_source_publishes_notes_but_nothing_under_output(tmp_path):
    kind = Text()
    notes, essay, binary = tmp_path / "notes.md", tmp_path / "essay.md", tmp_path / "frame.png"
    notes.write_text("outline")
    essay.write_text(ESSAY)
    binary.write_bytes(b"\x89PNG\xff\x00")
    assert kind.keep_source(Path("notes.md"), notes)
    assert not kind.keep_source(Path("output/essay.md"), essay)
    assert not kind.keep_source(Path("output/draft.txt"), notes)
    assert not kind.keep_source(Path("frame.png"), binary)


# --- `art-crit run --kind text` with the fake pi ---------------------------------------------------------------------


@pytest.fixture
def run_root(bench_root, tmp_path, git_repo, monkeypatch):
    monkeypatch.setenv("PATH", f"{FAKE_PI}{os.pathsep}{os.environ['PATH']}")
    for var in ("FAKE_PI_EXIT_CODE", "FAKE_PI_HANG", "FAKE_PI_ERROR_STOP", "FAKE_PI_BAD_TEXT"):
        monkeypatch.delenv(var, raising=False)
    (bench_root / "art-crit.toml").write_text(f'[run]\ndir = "{tmp_path / "runs"}"\nparallel = 4\ntimeout = "30m"\n')
    git_repo(bench_root)
    return bench_root


def test_text_run_publishes_the_markdown(run_root):
    rc = main(["run", "--yes", "--kind", "text", "an essay on chairs", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    page = json.loads((run_root / "docs/data/an-essay-on-chairs/page.json").read_text())
    assert page["kind"] == "text" and "one Markdown file" in page["final_prompt"]
    [run] = page["runs"]
    assert run["kind"] == "text" and run["state"] == "complete" and run["error"] is None
    out = run["output"]
    assert out["kind"] == "text" and (out["ok"], out["verified"], out["error"]) == (True, True, None)
    assert out["text"] == "text/text.md" and out["title"] == "On Fake Essays" and out["words"] > 10
    assert out["excerpt"].startswith("Written in ") and "fake agent, with a link." in out["excerpt"]
    assert "entry" not in out and "items" not in out and run["thumb"] is None
    run_dir = run_root / "docs/data/an-essay-on-chairs/runs" / run["id"]
    published = (run_dir / "text/text.md").read_text()
    assert published.startswith("# On Fake Essays") and str(Path.home()) not in published  # cleaned like source
    assert str(Path.home()) not in out["excerpt"]
    assert json.loads((run_dir / "run.json").read_text())["output"] == out
    assert run["source"]["files"] == ["notes.md"]  # the output itself is never source
    [summary] = json.loads((run_root / "docs/data/pages.json").read_text())
    assert summary["kind"] == "text" and summary["thumb"] is None

    # the site commands cope with a run that has no thumbnail
    assert main(["rebuild", "--root", str(run_root)]) == 0
    assert main(["list", "--root", str(run_root)]) == 0
    assert json.loads((run_dir / "run.json").read_text())["thumb"] is None
    # one kind per page: a media batch can't join it
    assert main(["run", "--yes", "--kind", "media", "an essay on chairs", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)]) == 1
    assert main(["rm", "an-essay-on-chairs", run["id"], "--yes", "--root", str(run_root)]) == 0
    assert not run_dir.exists()


def test_text_run_with_two_files_is_complete_with_an_output_error(run_root, monkeypatch):
    monkeypatch.setenv("FAKE_PI_BAD_TEXT", "1")
    rc = main(["run", "--yes", "--kind", "text", "two essays", "-m", "openai-codex/gpt-6-sol:low", "--root", str(run_root)])
    assert rc == 0
    [run] = json.loads((run_root / "docs/data/two-essays/page.json").read_text())["runs"]
    assert run["state"] == "complete" and run["error"] is None
    assert run["output"] == {"kind": "text", "ok": False, "verified": None,
                             "error": "2 Markdown files in ./output/ (essay.md, second.md); expected exactly one"}
