"""art-crit video: the layouts' geometry, the request checks, real videos made from a fixture site (ffmpeg + Chrome, no
model) and recording a game. The local API (which renders the video studio's videos) is tested in test_studio.py."""

import json
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from art_crit import video, video_sound
from art_crit.cli import main
from art_crit.site import rebuild
from art_crit.util import CritError
from test_web_kind import in_thread

REPO = Path(__file__).resolve().parents[1]
FIXTURE_DATA = REPO / "tests/fixtures/site/data"
HIGH = "model-x-high-20260102-000000"
OTHER = "model-y-high-20260102-000000"
GAME = "game-z-high-20260102-000000"

needs_tools = pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="needs ffmpeg")

GAME_HTML = """<!doctype html><body style="margin:0;background:#123"><div id=b style="position:absolute;width:60px;height:60px;background:#f80"></div>
<script>let x=0;setInterval(()=>{x=(x+7)%300;document.getElementById('b').style.left=x+'px';document.getElementById('b').style.top=(x*0.7)+'px'},30)</script>"""


@pytest.fixture
def site(tmp_path):
    """A repo root whose docs/ has the viewer, the fixture pages, a second good run on `art` and a tiny "game"."""
    root = tmp_path / "site"
    docs = root / "docs"
    docs.mkdir(parents=True)
    for f in REPO.glob("docs/*.html"):
        shutil.copy(f, docs / f.name)
    shutil.copytree(REPO / "docs/assets", docs / "assets")
    shutil.copytree(FIXTURE_DATA, docs / "data")
    runs = docs / "data/art/runs"
    shutil.copytree(runs / HIGH, runs / OTHER)
    record = json.loads((runs / HIGH / "run.json").read_text())
    (runs / OTHER / "run.json").write_text(json.dumps({**record, "id": OTHER, "model": "other-org/model-y", "effort": "high"}))
    (runs / GAME).mkdir()
    (runs / GAME / "index.html").write_text(GAME_HTML)
    game = {**record, "id": GAME, "model": "game-org/model-z", "output": {"kind": "godot", "ok": True, "verified": True, "error": None, "entry": "index.html"}}
    (runs / GAME / "run.json").write_text(json.dumps(game))
    rebuild(root)
    return root


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    return data["streams"][0]["width"], data["streams"][0]["height"], float(data["format"]["duration"])


def test_tiles_fit_their_box_without_overlapping():
    for layout, box in video.TILE_BOX.items():
        bx, by, bw, bh = box
        for n in range(2, video.MAX_RUNS + 1):
            tiles = video.tile_boxes(n, box)
            assert len(tiles) == n
            for x, y, side in tiles:
                assert bx <= x and x + side <= bx + bw and by <= y and y + side <= by + bh and side >= 200, (layout, n)
            for i, (x, y, side) in enumerate(tiles):
                for x2, y2, side2 in tiles[i + 1:]:
                    assert x + side <= x2 or x2 + side2 <= x or y + side <= y2 or y2 + side2 <= y
    assert len({y for _, y, _ in video.tile_boxes(6, video.TILE_BOX["wide"])}) == 2  # 3 + 3, not 4 + 2


def test_a_caption_has_the_model_and_what_it_cost():
    run = {"model": "openrouter/deepseek/deepseek-v4.1-flash@deepinfra", "effort": "max",
           "metrics": {"duration_ms": 98000, "tokens_total": 10400, "cost_usd": 0.318}}
    assert video.run_info(run) == {"model": run["model"], "effort": "max", "duration_s": 98.0, "tokens": 10400, "cost": 0.318}
    assert video.run_info({"model": "x", "effort": "low", "metrics": {"cost_usd": 0}})["cost"] is None  # unreported, not free


def test_stickers_go_to_the_runs_that_stand_out():
    info = lambda s, c: {"duration_s": s, "cost": c}
    assert video.stickers([info(10, 1), info(20, 2), info(30, 3)]) == ["FASTEST", None, "PRICIEST"]
    assert video.stickers([info(10, 3), info(20, 1), info(30, 2)]) == ["FASTEST", "CHEAPEST", "SLOWEST"]  # one each: the priciest is already the fastest
    assert video.stickers([info(10, None), info(10, None), info(10, None)]) == [None] * 3  # all alike, cost unreported
    assert video.stickers([info(10, 1), info(20, 2)]) == [None, None]  # two runs: nothing to single out


def test_the_timeline_and_the_sound_cues_line_up(tmp_path):
    runs = [{"model": f"v/m{i}", "effort": "high", "rank": 2 if i == 1 else None, "metrics": {"duration_ms": 1000 * (i + 1), "cost_usd": i + 1}}
            for i in range(3)]
    page = {"title": "T", "prompt": "draw  a\n<b>cat</b>", "kind": "media"}
    reveal = video.scene_plan("reveal", page, runs, [60, 60, 60], 2)
    assert [s["type"] for s in reveal["segments"]] == ["hook", "run", "run", "run", "finale"]
    assert reveal["frames"] == video.frames(video.TIMING["hook"] + 3 * 2 + video.TIMING["finale"])
    assert reveal["prompt"] == "draw a <b>cat</b>" and [r["pick"] for r in reveal["runs"]] == [False, True, False]
    assert [r["sticker"] for r in reveal["runs"]] == ["FASTEST", None, "PRICIEST"]
    grid = video.scene_plan("grid", page, runs, [60, 60, 60], 4)
    assert [s["type"] for s in grid["segments"]] == ["hook", "grid", "finale"] and grid["segments"][1]["spot"]
    for plan in (reveal, grid):
        cues = video.cues(plan)
        assert all(0 <= at < plan["frames"] / video.FPS for at, _ in cues)
        assert sum(kind == "cut" for _, kind in cues) == len(plan["segments"]) - 1  # one per cut
        assert ("ding" in {kind for _, kind in cues})  # the owner's pick
    wav = tmp_path / "s.wav"
    video_sound.soundtrack(video.cues(reveal), 3.5, wav)
    with wave.open(str(wav)) as w:
        assert w.getnframes() == round(3.5 * video_sound.RATE) and w.getsampwidth() == 2
    assert len(video.scene_plan("reveal", {**page, "prompt": "x" * 2000}, runs, [60] * 3, 2)["prompt"]) == video.MAX_PROMPT


@needs_tools
def test_a_bad_request_is_refused_before_anything_starts(site):
    for ids, layouts, seconds, message in [
        ([HIGH], None, 6, "compares 2 to 12"),
        ([HIGH, "nope"], None, 6, "no such run"),
        ([HIGH, "model-x-low-20260102-000000"], None, 6, "failed runs"),
        ([HIGH, OTHER], ["square"], 6, "unknown layout"),
        ([HIGH, OTHER], None, 99, "between 2 and 20"),
    ]:
        with pytest.raises(CritError, match=message):
            video.check_request(site, "art", ids, layouts, seconds)
    with pytest.raises(CritError, match="no such page"):
        video.check_request(site, "missing", [HIGH, OTHER], None, 6)


@needs_tools
def test_every_layout_is_made_from_pictures_and_a_video(site, tmp_path):
    said = []
    out = tmp_path / "out"
    files = in_thread(video.make_videos, site, "art", [HIGH, OTHER], None, 2, out, said.append)
    assert [f.name.rsplit("-", 1)[1] for f in files] == ["reveal.mp4", "grid.mp4", "wide.mp4"]
    sizes = {f.stem.rsplit("-", 1)[1]: probe(f) for f in files}
    assert sizes["reveal"][:2] == (1080, 1920) and sizes["grid"][:2] == (1080, 1920) and sizes["wide"][:2] == (1920, 1080)
    hook, finale = video.TIMING["hook"], video.TIMING["finale"]
    assert sizes["reveal"][2] == pytest.approx(hook + 2 * 2 + finale, abs=0.2)  # the opening, a run each, the question
    assert sizes["grid"][2] == pytest.approx(hook + 2 + 2 * video.TIMING["stagger"] + finale, abs=0.2)  # everyone at once
    assert audio_codec(files[0]) == "aac"
    assert not list(out.glob("*.txt")) and not list(out.glob("*.wav"))  # no leftovers beside the videos
    assert any("recording 2/2" in s for s in said) and any("rendering wide" in s for s in said)


def audio_codec(path):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(path)],
                          capture_output=True, text=True, check=True).stdout.strip()


@needs_tools
def test_a_game_is_recorded_not_just_its_thumbnail(site, tmp_path):
    def frames_of_the_game():
        docs, work = site / "docs", tmp_path / "work"
        work.mkdir()
        page = json.loads((docs / "data/art/page.json").read_text())
        game = next(r for r in page["runs"] if r["id"] == GAME)
        with video.studio(docs, work) as chrome:
            clip = video.make_source(chrome, docs, "art", game, 2, work, print)
            return video.extract_frames(clip, work / "clips/0"), work / "clips/0/f"
    count, frames = in_thread(frames_of_the_game)
    assert count == 2 * video.FPS
    assert (frames / "0001.jpg").read_bytes() != (frames / f"{count:04d}.jpg").read_bytes()  # the square moved


@needs_tools
def test_text_from_a_run_never_becomes_markup(site, tmp_path):
    """The scene shows the prompt and model ids with textContent: a prompt full of tags draws as text."""
    def render():
        docs, work = site / "docs", tmp_path / "work"
        work.mkdir()
        page = json.loads((docs / "data/art/page.json").read_text())
        page["prompt"] = '<img src=x onerror="document.title=1"><b id=evil>hi</b>'
        runs = [r for r in page["runs"] if r["id"] in (HIGH, OTHER)]
        with video.studio(docs, work) as chrome:
            clips = [video.extract_frames(video.make_source(chrome, docs, "art", r, 2, work, print), work / "clips" / str(n)) for n, r in enumerate(runs)]
            plan = video.scene_plan("reveal", page, runs, clips, 2)
            (work / "plan-reveal.json").write_text(json.dumps(plan))
            tab = chrome.renderer.new_page(viewport={"width": 1080, "height": 1920})
            tab.goto(f"{chrome.scene}/scene.html?plan=plan-reveal.json")
            tab.wait_for_function("() => window.sceneReady === true")
            tab.evaluate("(f) => window.renderFrame(f)", 80)
            return tab.evaluate("() => [document.getElementById('evil'), document.title, document.body.textContent.includes('<b id=evil>hi</b>'),"
                                " [...document.images].every((i) => !i.getAttribute('src') || /^(clips|assets)\\//.test(i.getAttribute('src')))]")
    assert in_thread(render) == [None, "art-crit video scene", True, True]


@needs_tools
def test_the_cli_prints_the_files_and_the_link_for_the_post(site, tmp_path, capsys):
    (site / "art-crit.toml").write_text('[site]\nurl = "https://bench.test/sub"\n')  # the link is under [site] url
    rc = in_thread(main, ["video", "art", HIGH, OTHER, "-l", "wide", "-d", "2", "--no-sound", "-o", str(tmp_path / "v"), "--root", str(site)])
    out = capsys.readouterr().out
    assert rc == 0 and out.count(".mp4") == 1 and (tmp_path / "v").is_dir()
    assert f"link for the post: https://bench.test/sub/compare.html?p=art&r={HIGH}%2C{OTHER}" in out
    assert main(["video", "art", HIGH, "--root", str(site)]) == 1  # one run isn't a comparison
