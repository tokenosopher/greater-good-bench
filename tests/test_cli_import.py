"""art-crit import: publishing run directories: ids/slugs, Godot engine dedupe + html rewrite, cleaning,
secrets, dry-run, idempotency. Uses the synthetic batch_dir fixture from conftest.py."""

import json
import shutil
from pathlib import Path

import pytest

from datetime import datetime

from art_crit import clean
from art_crit.cli import main
from art_crit.util import make_run_id, title_from_slug


def run_data_json(root, slug):
    return json.loads((root / "docs/data" / slug / "page.json").read_text())["runs"]


def run_dir(root, slug, run_id):
    return root / "docs/data" / slug / "runs" / run_id


# --- run id derivation (pure functions) ----------------------------------------------------


def test_make_run_id_matches_spec_example():
    run_id = make_run_id("openai-codex/gpt-6-sol", "high", datetime(2026, 9, 26, 0, 11, 58))
    assert run_id == "gpt-6-sol-high-20260926-001158"


def test_title_from_slug():
    assert title_from_slug("voxel-horse") == "Voxel horse"


# --- import end to end -----------------------------------------------------------------------


def test_import_creates_a_run_per_level(bench_root, batch_dir, capsys):
    rc = main(["import", str(batch_dir), "--root", str(bench_root)])
    assert rc == 0
    runs = run_data_json(bench_root, "voxel-horse")
    assert sorted(r["effort"] for r in runs) == ["high", "low"]
    ids = {r["id"] for r in runs}
    assert ids == {"gpt-6-sol-low-20260926-001158", "gpt-6-sol-high-20260926-001158"}
    out = capsys.readouterr().out
    assert "gpt-6-sol-low-20260926-001158" in out and "bytes" in out


def test_page_override(bench_root, batch_dir):
    rc = main(["import", str(batch_dir), "--page", "custom-slug", "--root", str(bench_root)])
    assert rc == 0
    runs = run_data_json(bench_root, "custom-slug")
    assert len(runs) == 2
    assert all(r["page"] == "custom-slug" for r in runs)


# --- reference files (--ref) -----------------------------------------------------------------


def test_import_publishes_references_and_rebuild_lists_them(bench_root, batch_factory):
    batch = batch_factory(refs={"robie.jpg": b"JPEG-DATA", "second.png": b"PNG-DATA"})
    main(["import", str(batch), "--root", str(bench_root)])
    refs = bench_root / "docs/data/voxel-horse/references"
    assert sorted(p.name for p in refs.iterdir()) == ["robie.jpg", "second.png"]
    assert (refs / "robie.jpg").read_bytes() == b"JPEG-DATA"
    page = json.loads((bench_root / "docs/data/voxel-horse/page.json").read_text())
    assert page["references"] == ["robie.jpg", "second.png"]
    # a re-import replaces the set, and rebuild derives the list from what is on disk
    batch2 = batch_factory(started=datetime(2026, 9, 26, 0, 12, 58), refs={"only.png": b"NEW"})
    main(["import", str(batch2), "--page", "voxel-horse", "--root", str(bench_root)])
    page = json.loads((bench_root / "docs/data/voxel-horse/page.json").read_text())
    assert page["references"] == ["only.png"]
    main(["rebuild", "--root", str(bench_root)])
    page = json.loads((bench_root / "docs/data/voxel-horse/page.json").read_text())
    assert page["references"] == ["only.png"]


def test_import_without_references_leaves_no_list(bench_root, batch_dir):
    main(["import", str(batch_dir), "--root", str(bench_root)])
    page = json.loads((bench_root / "docs/data/voxel-horse/page.json").read_text())
    assert "references" not in page
    assert not (bench_root / "docs/data/voxel-horse/references").exists()


def test_engine_dedupe_one_dir_for_two_levels(bench_root, batch_dir):
    main(["import", str(batch_dir), "--root", str(bench_root)])
    engines = list((bench_root / "docs/engines").iterdir())
    assert len(engines) == 1
    runs = run_data_json(bench_root, "voxel-horse")
    assert len({r["output"]["engine"] for r in runs}) == 1
    assert runs[0]["output"]["engine"] == engines[0].name
    # engine files never end up inside a run's own directory
    for r in runs:
        rd = run_dir(bench_root, "voxel-horse", r["id"])
        assert not list(rd.rglob("*.wasm"))
        assert not (rd / "game" / "index.js").exists()


def test_html_rewrite_sets_executable_mainpack_filesizes_and_script_src(bench_root, batch_dir):
    import os
    import re
    from pathlib import Path

    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs = run_data_json(bench_root, "voxel-horse")
    sha12 = runs[0]["output"]["engine"]
    r = run_dir(bench_root, "voxel-horse", runs[0]["id"])
    html = (r / "game" / "index.html").read_text()
    final_game_dir = Path("data") / "voxel-horse" / "runs" / runs[0]["id"] / "game"
    rel = os.path.relpath(Path("engines") / sha12 / "godot", final_game_dir)
    assert f'<script src="{rel}.js"></script>' in html

    cfg = json.loads(re.search(r"const GODOT_CONFIG = (\{.*?\});", html).group(1))
    assert cfg["executable"] == rel
    assert cfg["mainPack"] == "index.pck"
    assert f"{rel}.wasm" in cfg["fileSizes"]
    assert "index.wasm" not in cfg["fileSizes"]
    # and it actually resolves to the stored engine file from the run's game dir
    resolved = (r / "game" / f"{rel}.wasm").resolve()
    assert resolved == (bench_root / "docs/engines" / sha12 / "godot.wasm").resolve()


def test_threads_refused_without_flag_and_allowed_with_it(bench_root, batch_factory):
    run = batch_factory(slug="thready", levels=["high"], threads=True)
    rc = main(["import", str(run), "--root", str(bench_root)])
    assert rc != 0
    assert not (bench_root / "docs/data/thready").exists()

    rc = main(["import", str(run), "--allow-threads", "--root", str(bench_root)])
    assert rc == 0
    runs = run_data_json(bench_root, "thready")
    assert runs[0]["output"]["threads"] is True


def test_output_record_carries_ok_verified_and_error(bench_root, batch_dir):
    main(["import", str(batch_dir), "--root", str(bench_root)])
    for r in run_data_json(bench_root, "voxel-horse"):
        assert r["output"]["kind"] == "godot" and r["output"]["entry"] == "game/index.html"
        assert (r["output"]["ok"], r["output"]["verified"], r["output"]["error"]) == (True, True, None)
        assert r["thumb"] == "thumb.png" and "game" not in r and "verified" not in r


def test_source_files_exclude_session_and_editor_cache(bench_root, batch_dir):
    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs = run_data_json(bench_root, "voxel-horse")
    r = run_dir(bench_root, "voxel-horse", runs[0]["id"])
    files = runs[0]["source"]["files"]
    assert "project.godot" in files
    assert "scenes/main.tscn" in files
    assert "scripts/main.gd" in files
    assert "export_presets.cfg" in files  # one of the project's own files
    assert ".DS_Store" not in files
    assert not list((r / "source").rglob(".godot"))
    assert not (r / "source" / ".godot").exists()


# --- cleaning ---------------------------------------------------------------------------------


def test_cleaning_strips_keys_and_rewrites_home(bench_root, batch_dir):
    from pathlib import Path

    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs = run_data_json(bench_root, "voxel-horse")
    r = run_dir(bench_root, "voxel-horse", runs[0]["id"])
    convo = (r / "session/conversation.json").read_text()
    assert "thinkingSignature" not in convo
    assert "encrypted_content" not in convo
    assert '"pid"' not in convo
    assert '"sessionId"' not in convo
    assert str(Path.home()) not in convo
    assert "~" in convo

    # only the transcript is published from harness/ (the raw stdout, the brief and the like stay local)
    assert sorted(p.name for p in (r / "session").iterdir()) == ["conversation.json"]
    assert runs[0]["session"] == {"conversation": "session/conversation.json"}


def test_bench_toml_extra_rewrite(bench_root, batch_dir):
    (bench_root / "art-crit.toml").write_text('[clean]\nrewrite = { "/Volumes/M2SSD" = "<vol>" }\n')
    convo_path = batch_dir / "gpt-6-sol-low-20260926-001158" / "harness" / "conversation.json"
    convo_path.write_text(convo_path.read_text().replace("effort-runs/x", "/Volumes/M2SSD/effort-runs/x"))

    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs = run_data_json(bench_root, "voxel-horse")
    low_id = next(r["id"] for r in runs if r["effort"] == "low")
    convo = (run_dir(bench_root, "voxel-horse", low_id) / "session/conversation.json").read_text()
    assert "/Volumes/M2SSD" not in convo
    assert "<vol>" in convo


# --- secrets ------------------------------------------------------------------------------------


def test_secret_hit_aborts_before_writing_anything(bench_root, batch_factory, capsys):
    run = batch_factory(slug="secretrun", secret="sk-" + "A" * 24)
    rc = main(["import", str(run), "--root", str(bench_root)])
    assert rc != 0
    assert not (bench_root / "docs/data/secretrun").exists()
    err = capsys.readouterr().err
    assert "secret" in err.lower()
    assert "sk-A" in err or "sk-A…"[:5] in err  # masked prefix printed, not the full secret
    assert "A" * 24 not in err


def test_secret_redact_continues_and_scrubs(bench_root, batch_factory):
    run = batch_factory(slug="redactrun", secret="sk-" + "B" * 24)
    rc = main(["import", str(run), "--redact", "--root", str(bench_root)])
    assert rc == 0
    runs = run_data_json(bench_root, "redactrun")
    low_id = next(r["id"] for r in runs if r["effort"] == "low")
    convo = (run_dir(bench_root, "redactrun", low_id) / "session/conversation.json").read_text()
    assert "B" * 24 not in convo
    assert "[REDACTED]" in convo


def test_image_data_skips_rewrites_and_secret_scan_but_text_does_not():
    home = str(Path.home())
    lucky = "AKIA" + "Q" * 16 + "/" + home.replace("/", "+") + "=="  # base64 that looks like an AWS key
    convo = [{"type": "message", "message": {"role": "toolResult", "content": [
        {"type": "text", "text": f"opened {home}/shot.png"},
        {"type": "image", "mimeType": "image/jpeg", "data": lucky},
        {"type": "image", "mimeType": "image/jpeg", "data": "not base64: AKIA" + "Z" * 16},
    ]}}]
    images = []
    text, _ = clean.clean_json(json.dumps(convo), [(home, "~")], images)
    hits = clean.scan_secrets(text)
    assert [h[1] for h in hits] == ["AKIA" + "Z" * 16]  # only the data that isn't base64 is still scanned
    content = json.loads(clean.restore_images(text, images))[0]["message"]["content"]
    assert content[0]["text"] == "opened ~/shot.png" and content[1]["data"] == lucky


# --- dry-run / idempotency ------------------------------------------------------------------


def test_dry_run_writes_nothing(bench_root, batch_dir, capsys):
    rc = main(["import", str(batch_dir), "--dry-run", "--root", str(bench_root)])
    assert rc == 0
    assert not (bench_root / "docs/data").exists() or not list((bench_root / "docs/data").iterdir())
    out = capsys.readouterr().out
    assert "dry-run" in out


def test_a_single_run_directory_can_be_imported(bench_root, batch_dir):
    assert main(["import", str(batch_dir / "gpt-6-sol-high-20260926-001158"), "--root", str(bench_root)]) == 0
    assert [r["effort"] for r in run_data_json(bench_root, "voxel-horse")] == ["high"]


def test_import_needs_a_run_or_batch_directory(bench_root, tmp_path, capsys):
    (tmp_path / "empty").mkdir()
    assert main(["import", str(tmp_path / "empty"), "--root", str(bench_root)]) == 1
    assert "no run.json" in capsys.readouterr().err


def test_a_failed_agent_run_is_published_without_output(bench_root, batch_dir):
    import json as _json

    path = batch_dir / "gpt-6-sol-low-20260926-001158"
    record = _json.loads((path / "run.json").read_text())
    record.update(state="failed", error="harness exited 1", output=None)
    (path / "run.json").write_text(_json.dumps(record))
    main(["import", str(path), "--root", str(bench_root)])
    [run] = run_data_json(bench_root, "voxel-horse")
    assert (run["state"], run["error"], run["output"], run["thumb"]) == ("failed", "harness exited 1", None, None)
    assert not list((bench_root / "docs/engines").iterdir())  # nothing was exported, so no engine is stored


def test_reimport_is_idempotent(bench_root, batch_dir):
    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs_before = run_data_json(bench_root, "voxel-horse")
    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs_after = run_data_json(bench_root, "voxel-horse")
    assert len(runs_after) == len(runs_before) == 2
    assert {r["id"] for r in runs_after} == {r["id"] for r in runs_before}
    # engine still deduped to one dir after re-import
    assert len(list((bench_root / "docs/engines").iterdir())) == 1


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_big_transcript_images_are_published_as_small_jpegs(tmp_path):
    """An agent reading a big render: the published transcript keeps an 800px JPEG plus the original's type and size."""
    import base64
    import subprocess

    from art_crit.importer import IMAGE_MAX_BYTES, shrink_images

    png = tmp_path / "big.png"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=1600x1200", "-frames:v", "1", str(png)], check=True)
    raw = png.read_bytes()
    assert len(raw) > IMAGE_MAX_BYTES
    small = base64.b64encode(b"tiny").decode()
    entries = [{"message": {"role": "toolResult", "content": [
        {"type": "image", "mimeType": "image/png", "data": base64.b64encode(raw).decode()},
        {"type": "image", "mimeType": "image/png", "data": small},  # small: left alone
        {"type": "image", "mimeType": "image/jpeg", "sourceMimeType": "image/png", "bytes": 9, "data": small},  # already done
    ]}}]
    assert shrink_images(entries) == 1
    big, tiny, done = entries[0]["message"]["content"]
    assert (big["mimeType"], big["sourceMimeType"], big["bytes"]) == ("image/jpeg", "image/png", len(raw))
    thumb = base64.b64decode(big["data"])
    assert thumb[:2] == b"\xff\xd8" and len(thumb) < len(raw)
    assert tiny["data"] == small and "sourceMimeType" not in tiny
    assert done["data"] == small


def test_big_transcript_image_without_ffmpeg_keeps_only_its_record(monkeypatch):
    import base64

    monkeypatch.setattr("art_crit.importer.thumbnail", lambda raw, width: None)
    from art_crit.importer import shrink_images

    block = {"type": "image", "mimeType": "image/png", "data": base64.b64encode(b"x" * 100_000).decode()}
    assert shrink_images([block]) == 1
    assert block == {"type": "image", "mimeType": "image/jpeg", "sourceMimeType": "image/png", "bytes": 100_000}


# --- what a publish commits (only the run's own files) ---------------------------------------


def _git(root, *args):
    import subprocess

    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout


def test_publish_commits_only_the_paths_it_is_given(bench_root, batch_dir, git_repo):
    """A publish with pathspecs leaves the rest of the working copy alone: publishing a run must not sweep
    up unrelated files, however they got there (staged by hand, or a pending viewer edit)."""
    from art_crit.cli import cmd_publish
    from art_crit.config import Config
    from art_crit.importer import cmd_import

    git_repo(bench_root)
    written = cmd_import(Config.load(bench_root), batch_dir)  # what `art-crit run` publishes
    # a decoy staged outside docs/, and a pending docs edit from nobody's run
    (bench_root / "src").mkdir()
    (bench_root / "src" / "unrelated.py").write_text("x = 1\n")
    _git(bench_root, "add", "src/unrelated.py")
    (bench_root / "docs" / "assets").mkdir()
    (bench_root / "docs" / "assets" / "viewer.js").write_text("// tweak\n")

    cmd_publish(bench_root, "art-crit run: voxel-horse (r1)", written)

    committed = _git(bench_root, "show", "--name-only", "--format=", "HEAD").split()
    assert committed and all(p.startswith(("docs/data/", "docs/engines/")) for p in committed), committed
    assert "docs/data/voxel-horse/page.json" in committed
    assert "src/unrelated.py" not in committed and "docs/assets/viewer.js" not in committed
    status = _git(bench_root, "status", "--porcelain")
    assert "src/unrelated.py" in status and "docs/assets/" in status


def test_import_returns_the_paths_it_wrote(bench_root, batch_dir):
    """`art-crit run` publishes each run through these, so the import has to report what it touched."""
    from art_crit.importer import cmd_import
    from art_crit.config import Config

    written = {str(p) for p in cmd_import(Config.load(bench_root), batch_dir)}
    assert "docs/data/voxel-horse/page.json" in written and "docs/data/pages.json" in written
    assert "docs/engines/6d75082047da" in written  # the engine this page stored
    run = "docs/data/voxel-horse/runs/gpt-6-sol-high-20260926-001158"
    assert run in written


# --- the model's own summary (run.summary) --------------------------------------------------------


def test_import_records_the_last_assistant_text_as_summary_from_the_cleaned_transcript(bench_root, batch_dir):
    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs = run_data_json(bench_root, "voxel-horse")  # page.json carries it like any other run field
    for r in runs:
        assert r["summary"] == "Working in ~/effort-runs/x now."  # the cleaned text: the home dir is rewritten
        on_disk = json.loads((run_dir(bench_root, "voxel-horse", r["id"]) / "run.json").read_text())
        assert on_disk["summary"] == r["summary"]


def test_import_summary_is_null_without_a_transcript(bench_root, batch_dir):
    (batch_dir / "gpt-6-sol-low-20260926-001158" / "harness" / "conversation.json").unlink()
    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs = {r["effort"]: r for r in run_data_json(bench_root, "voxel-horse")}
    assert runs["low"]["summary"] is None and runs["low"]["session"] is None
    assert runs["high"]["summary"]


def test_import_summary_is_redacted_like_the_transcript(bench_root, batch_factory):
    run = batch_factory(slug="redactsum", secret="sk-" + "C" * 24)
    main(["import", str(run), "--redact", "--root", str(bench_root)])
    low = next(r for r in run_data_json(bench_root, "redactsum") if r["effort"] == "low")
    assert "C" * 24 not in low["summary"] and "[REDACTED]" in low["summary"]


def test_summary_skips_thinking_and_tool_calls_and_walks_back_to_text():
    from art_crit.summary import last_assistant_text

    def asst(*parts):
        return {"type": "message", "message": {"role": "assistant", "content": list(parts)}}

    entries = [
        {"type": "message", "message": {"role": "user", "content": "make a game"}},
        asst({"type": "text", "text": "Starting."}, {"type": "toolCall", "name": "bash", "arguments": {}}),
        asst({"type": "thinking", "thinking": "secret plan"}, {"type": "text", "text": "I made **Orbit**, a game."},
             {"type": "text", "text": "Arrow keys move."}, {"type": "toolCall", "name": "read", "arguments": {}}),
        {"type": "message", "message": {"role": "toolResult", "content": [{"type": "text", "text": "ok"}]}},
        asst({"type": "thinking", "thinking": "done?"}, {"type": "toolCall", "name": "bash", "arguments": {}}),
        asst({"type": "text", "text": "   "}),
    ]
    assert last_assistant_text(entries) == "I made **Orbit**, a game.\n\nArrow keys move."
    assert last_assistant_text(entries[:1]) is None
    assert last_assistant_text([asst({"type": "text", "text": "plain"})]) == "plain"
    assert last_assistant_text([{"type": "message", "message": {"role": "assistant", "content": "a string"}}]) == "a string"


def test_summary_is_cut_at_4000_characters_on_a_paragraph_or_sentence():
    from art_crit.summary import MAX_CHARS, cut

    assert cut("short.") == "short."
    paragraphs = "\n\n".join(f"Paragraph {i} " + "word " * 60 for i in range(40))
    out = cut(paragraphs)
    assert len(out) <= MAX_CHARS and out.endswith("\n\n…") and paragraphs.startswith(out[:-3])
    sentences = " ".join(f"Sentence {i} is here." for i in range(400))  # one long paragraph
    out = cut(sentences)
    assert len(out) <= MAX_CHARS and out.endswith("here. …")
    words = "x" * 10 + " " + "word " * 1200  # no paragraph or sentence break at all
    out = cut(words)
    assert len(out) <= MAX_CHARS and out.endswith("word…")
    fenced = "Intro.\n\n```\n" + "code line\n" * 600 + "```\n"
    out = cut(fenced)
    assert len(out) <= MAX_CHARS and out.endswith("\n```")  # a fence cut open is closed again


def published_summary(tmp_path, text):
    """summary_of() for a run whose published transcript ends with an assistant message saying `text`."""
    from art_crit.summary import summary_of

    session = tmp_path / "session"
    session.mkdir(exist_ok=True)
    (session / "conversation.json").write_text(json.dumps([
        {"type": "message", "message": {"role": "user", "content": "make a game"}},
        {"type": "message", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}},
    ]))
    return summary_of(tmp_path)


def test_summary_is_the_blurb_line_alone_when_the_closing_message_has_one(tmp_path):
    closing = ("I've built **Ripple**. Run `godot --path .` to play.\n\n## How to play\n- arrows move\n\n"
               "Blurb: Ripple is a game that teaches players\nto spot online misinformation.")
    assert published_summary(tmp_path, closing) == "Ripple is a game that teaches players to spot online misinformation."
    # anywhere in the message, any case, its paragraph only
    closing = "Done.\n\nBLURB: Common Ground is a turn-based commons game.\n\nThanks for reading!"
    assert published_summary(tmp_path, closing) == "Common Ground is a turn-based commons game."


def test_summary_falls_back_to_the_closing_message_without_a_blurb_line(tmp_path):
    closing = "I made **Orbit**, a game.\n\nThe blurb is below: none, actually."
    assert published_summary(tmp_path, closing) == closing
    assert published_summary(tmp_path, "Blurb:   ") == "Blurb:"  # an empty blurb is no blurb


def test_blurb_is_plain_text_with_emphasis_stripped(tmp_path):
    closing = "**Blurb:** ***Common Ground*** is a _turn-based_ game about `one lake`, with snake_case and 2*3*4 kept."
    assert published_summary(tmp_path, closing) == (
        "Common Ground is a turn-based game about one lake, with snake_case and 2*3*4 kept.")


def test_blurb_is_cut_at_500_characters():
    from art_crit.summary import BLURB_MAX, blurb_of

    long = "Blurb: " + " ".join(f"Sentence {i} is here." for i in range(60))
    out = blurb_of(long)
    assert len(out) <= BLURB_MAX and out.endswith("is here.")
    words = blurb_of("Blurb: " + "word " * 200)  # no sentence end to cut at
    assert len(words) <= BLURB_MAX and words.endswith("word…")


def test_rebuild_backfills_a_missing_summary_from_the_published_transcript(bench_root, batch_dir):
    main(["import", str(batch_dir), "--root", str(bench_root)])
    runs = run_data_json(bench_root, "voxel-horse")
    for r in runs:  # as published before summaries existed
        rj = run_dir(bench_root, "voxel-horse", r["id"]) / "run.json"
        record = json.loads(rj.read_text())
        del record["summary"]
        rj.write_text(json.dumps(record, indent=2) + "\n")
    convo = run_dir(bench_root, "voxel-horse", runs[0]["id"]) / "session" / "conversation.json"
    convo.unlink()  # one run without a transcript gets null
    main(["rebuild", "--root", str(bench_root)])
    by_id = {r["id"]: r for r in run_data_json(bench_root, "voxel-horse")}
    assert by_id[runs[0]["id"]]["summary"] is None
    assert by_id[runs[1]["id"]]["summary"] == "Working in ~/effort-runs/x now."
    for r in runs:
        assert "summary" in json.loads((run_dir(bench_root, "voxel-horse", r["id"]) / "run.json").read_text())
