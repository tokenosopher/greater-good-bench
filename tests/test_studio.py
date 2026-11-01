"""The video studio: what a spec may hold, the timeline the preview and the render share, real renders from a fixture
site (ffmpeg + Chrome, no model), and the local-only API (GET api/studio, POST api/studio/plan, POST api/video, the job
list and the files)."""

import json
import time
import urllib.error
import urllib.request

import pytest

from art_crit import studio, video, video_sound
from art_crit.serve import serve_in_thread
from art_crit.util import CritError
from test_video import GAME, HIGH, OTHER, needs_tools, probe, site  # noqa: F401 (site is a fixture)
from test_web_kind import in_thread

ART = lambda run: {"page": "art", "run": run}  # noqa: E731


def card(type, at, secs=3, **kw):
    return {"id": f"{type}{at}", "type": type, "heading": kw.get("heading", "Hello"), "sub": "", "link": kw.get("link", ""),
            "look": "dark", "secs": secs, "at": at}


def test_the_catalog_matches_the_scene_and_the_page():
    c = studio.catalog()
    assert set(c["templates"]) == {"reveal", "grid", "wide", "duel", "lineup", "wipe", "ladder", "countdown", "montage"}
    for t in c["templates"].values():
        assert t["format"] in studio.FORMATS and t["size"] == studio.FORMATS[t["format"]]
    assert {k for k, t in studio.TEMPLATES.items() if t["together"]} == set(studio.TILE_BOX)
    assert set(c["music"]) == {"none", *video_sound.STYLES}
    assert studio.slot_labels("lineup", 4) == ["1", "2", "3", "4"] and studio.slot_labels("lineup", 9) == ["1", "2", "3"]
    assert len(studio.slot_labels("reveal")) == 4 and len(studio.slot_labels("reveal", 12)) == 12  # 4 unless asked
    assert {k for k, card in c["cards"].items() if card.get("scene")} == {"hook", "finale"}
    assert set(studio.FINALE_BOX) == set(studio.FORMATS)
    # the cards with a link default to the site's address ([site] url without the scheme)
    assert {k: card["link"] for k, card in c["cards"].items() if "link" in card} == {"finale": "bench.example.com", "vote": "bench.example.com"}
    assert studio.catalog("bench.test/x")["cards"]["vote"]["link"] == "bench.test/x"


def test_a_runs_type_and_length():
    still = {"kind": "media", "output": {"items": [{"type": "image"}]}}
    clip = {"kind": "media", "output": {"items": [{"type": "image"}, {"type": "video", "duration_s": 7.4}]}}
    assert [studio.slot_type(r) for r in (still, clip, {"kind": "godot", "output": {}}, {"kind": "web", "output": {}},
                                          {"kind": "blender", "output": {"items": [{"type": "model"}]}})] == ["image", "video", "game", "web", "model"]
    assert studio.clip_seconds(still, 5) == 5 and studio.clip_seconds(clip, 5) == 7.4
    assert studio.clip_seconds({"output": {"items": [{"type": "video", "duration_s": 40}]}}, 3) == 10  # capped
    assert studio.clip_seconds({"kind": "godot"}, 3) == 4 and studio.clip_seconds({"kind": "godot"}, 3, 8) == 8  # a recording: `record`


def test_a_bad_spec_is_refused_with_the_reason(site):  # noqa: F811
    good = {"template": "duel", "slots": [ART(HIGH), ART(OTHER)]}
    assert studio.check_spec(site, good)[0]["count"] == 2
    for patch, error in [
        ({"template": "nope"}, "template must be one of"),
        ({"slots": [ART(HIGH), ART(OTHER), ART(HIGH)]}, "has 2 slots"),
        ({"slots": [ART(HIGH)]}, "slot Right is empty"),
        ({"slots": [{"page": "../art", "run": HIGH}, None]}, "no such page"),
        ({"slots": [ART("nope"), None]}, "no such run"),
        ({"slots": [ART("model-x-low-20260102-000000"), None]}, "nothing to show"),
        ({"slots": ["x", None]}, "{page, run} or null"),
        ({"cards": [{**card("title", 0), "type": "poster"}]}, "card type"),
        ({"cards": [{**card("title", 0), "look": "neon"}]}, "look must be"),
        ({"cards": [card("title", 0, secs=4)]}, "a card's length"),
        ({"cards": [card("title", 0, heading="x" * 91)]}, "at most 90"),
        ({"cards": [card("title", -1)]}, "whole number"),
        ({"cards": [card("title", 0)] * 13}, "at most 12 cards"),
        ({"still": 7}, "seconds for a still"),
        ({"sync": "fast"}, "sync must be"),
        ({"music": "jazz"}, "music must be"),
        ({"labels": "yes"}, "true or false"),
        ({"wipe": 120}, "0 to 100"),
        ({"record": 5}, "seconds for a recording"),
    ]:
        with pytest.raises(CritError, match=error.replace("{", r"\{").replace("}", r"\}")):
            studio.check_spec(site, {**good, **patch}, complete="slots" not in patch or "empty" in error)
    spec, runs = studio.check_spec(site, {"template": "duel", "slots": [ART(HIGH)]}, complete=False)  # the preview allows gaps
    assert runs[1] is None and spec["slots"][1] is None
    assert studio.check_spec(site, {**good, "cards": [card("title", 0, link="x")]})[0]["cards"][0]["link"] == ""  # only vote and finale cards have one
    checked = studio.check_spec(site, {**good, "cards": [{**card("finale", 99, link="x"), "look": "peach"}]})[0]
    assert (checked["cards"][0]["link"], checked["cards"][0]["look"]) == ("x", "glow")  # the set pieces are always on the glow
    assert (checked["metrics"], checked["record"]) == (True, 4)  # like `art-crit video`: numbers on, 4 s recordings


def test_cards_go_between_the_results_in_play_order():
    run = {"kind": "media", "output": {"items": [{"type": "image"}]}}
    base = {"still": 2, "record": 4, "cards": []}
    together, total = studio.timeline({**base, "template": "duel", "cards": [card("vote", 99), card("title", 0)]}, [run, run])
    assert [(s["type"], s.get("card")) for s in together] == [("card", "title0"), ("slots", None), ("card", "vote99")]
    assert [s["start"] for s in together] == [0, 3, 5] and total == 8
    one_by_one, total = studio.timeline({**base, "template": "ladder", "cards": [card("section", 2, secs=5), card("title", 0)]}, [run, None, run, run])
    assert [s.get("slot", s.get("card")) for s in one_by_one] == ["title0", 0, 1, "section2", 2, 3]
    assert total == 3 + 4 * 2 + 5  # an empty slot counts as a still in the preview


def test_renders_on_disk_are_listed_and_deleted(tmp_path):
    folder = studio.renders_dir(tmp_path)
    folder.mkdir(parents=True)
    (folder / "20261019-100000-wipe.mp4").write_bytes(b"old")  # from before renders had a .json: named by its file
    (folder / "20261020-100000-duel.mp4").write_bytes(b"new")
    (folder / "20261020-100000-duel.json").write_text(json.dumps({"title": "Hi", "template": "Head to head", "format": "16:9", "slots": 2, "length": 9}))
    (folder / "notes.txt").write_text("not a video")
    listed = studio.renders(tmp_path)
    assert [(r["name"], r["title"], r["template"], r["length"]) for r in listed] == [
        ("20261020-100000-duel.mp4", "Hi", "Head to head", 9), ("20261019-100000-wipe.mp4", "20261019-100000-wipe", "Wipe", None)]
    for bad in ("notes.txt", "../x.mp4", None):
        with pytest.raises(CritError, match="no such video"):
            studio.delete_render(tmp_path, bad)
    studio.delete_render(tmp_path, "20261020-100000-duel.mp4")
    assert sorted(p.name for p in folder.iterdir()) == ["20261019-100000-wipe.mp4", "notes.txt"]


def test_the_sound_cues_follow_the_segments():
    slot = {"sticker": None, "pick": False}
    plan = {"timing": {**video.TIMING, "type_s": 1}, "metrics": True, "prompt": "", "slots": [{**slot, "sticker": "FASTEST"}, slot], "segments": [
        {"type": "card", "start": 0, "frames": 60, "card": {"type": "vote", "link": "x"}},
        {"type": "slot", "start": 60, "frames": 60, "slot": 0, "card": None}, {"type": "slot", "start": 120, "frames": 60, "slot": 1, "card": None}]}
    cues = studio.cues(plan)
    assert cues[0] == (0, "hit") and sum(k == "cut" for _, k in cues) == 2
    assert sum(k == "pop" for _, k in cues) == 5  # the card's heading and link, each run's name, the sticker
    assert any(k == "tick" for _, k in cues) and all(at < 6 for at, _ in cues)
    finale = {**plan, "slots": [slot, {**slot, "pick": True}], "segments": [{"type": "card", "start": 0, "frames": 150, "card": {"type": "finale", "link": ""}}]}
    assert ("ding" in {k for _, k in studio.cues(finale)}) and sum(k == "pop" for _, k in studio.cues(finale)) == 3


def test_the_scene_plan_shares_a_prompt_and_a_pick_only_within_one_page(site):  # noqa: F811
    spec, runs = studio.check_spec(site, {"template": "reveal", "count": 3, "slots": [ART(HIGH), ART(OTHER), ART(GAME)],
                                          "cards": [card("hook", 0), card("finale", 99)]})
    runs[0]["rank"], runs[1]["rank"], runs[2]["rank"] = 3, 2, 1
    plan = studio.scene_plan(spec, runs, [60, 60, 60])
    assert plan["prompt"] and plan["timing"]["type_s"] > 0 and len(plan["finale_tiles"]) == 3
    assert [s["pick"] for s in plan["slots"]] == [False, False, True] and [s["label"] for s in plan["slots"]] == ["1", "2", "3"]
    mixed, mixed_runs = studio.check_spec(site, {"template": "duel", "slots": [ART(HIGH), {"page": "demo", "run": "model-x-high-20260101-001000"}]})
    mixed_runs[0]["rank"] = 1
    plan = studio.scene_plan(mixed, mixed_runs, [60, 60])
    assert plan["prompt"] == "" and not any(s["pick"] for s in plan["slots"])  # two prompts: no typed prompt, no crown


@needs_tools
@pytest.mark.parametrize("template, slots, cards, size", [
    ("duel", [ART(HIGH), ART(OTHER)], [card("title", 0, secs=2), card("vote", 99, secs=2, link="bench.example.com")], (1920, 1080)),
    ("ladder", [ART(HIGH), ART(OTHER), ART(HIGH), ART(OTHER)], [card("section", 2, secs=2)], (1080, 1920)),  # a run twice: recorded once
    ("reveal", [ART(HIGH), ART(OTHER)], [card("hook", 0, heading=""), card("finale", 99, secs=5, link="bench.example.com")], (1080, 1920)),
    ("grid", [ART(HIGH), ART(OTHER)], [card("hook", 0, heading=""), card("finale", 99, secs=5)], (1080, 1920)),
    ("wide", [ART(HIGH), ART(OTHER)], [card("finale", 99, secs=3)], (1920, 1080)),
])
def test_a_template_renders_at_its_format_and_length(site, tmp_path, template, slots, cards, size):  # noqa: F811
    spec = {"template": template, "count": len(slots), "slots": slots, "cards": cards, "still": 2, "music": "lofi", "metrics": True}
    said = []
    out = in_thread(studio.make_studio_video, site, spec, tmp_path, said.append)
    width, height, seconds = probe(out)
    checked, runs = studio.check_spec(site, spec)
    assert (width, height) == size and seconds == pytest.approx(studio.timeline(checked, runs)[1], abs=0.2)
    assert sum("recording" in s for s in said) == 2


@needs_tools
def test_text_on_a_card_never_becomes_markup(site, tmp_path):  # noqa: F811
    """The studio scene puts card text in with textContent: a heading full of tags draws as text."""
    def render():
        spec, runs = studio.check_spec(site, {"template": "duel", "slots": [ART(HIGH), ART(OTHER)],
                                              "cards": [card("title", 0, heading='<img src=x onerror="document.title=1"><b id=evil>'),
                                                        card("hook", 0, heading='<i id=evil2>'), card("finale", 99, heading='<u id=evil3>')]})
        work = tmp_path / "work"
        work.mkdir()
        with video.studio(site / "docs", work) as chrome:
            clips = [video.extract_frames(video.make_source(chrome, site / "docs", "art", r, 2, work, print), work / "clips" / str(n)) for n, r in enumerate(runs)]
            (work / "plan-studio.json").write_text(json.dumps(studio.scene_plan(spec, runs, clips)))
            tab = chrome.renderer.new_page(viewport={"width": 1920, "height": 1080})
            tab.goto(f"{chrome.scene}/studio.html?plan=plan-studio.json")
            tab.wait_for_function("() => window.sceneReady === true")
            tab.evaluate("(f) => window.renderFrame(f)", 30)
            return tab.evaluate("() => [['evil', 'evil2', 'evil3'].map((id) => document.getElementById(id)), document.title,"
                                " ['<b id=evil>', '<i id=evil2>', '<u id=evil3>'].every((t) => document.body.textContent.includes(t))]")
    assert in_thread(render) == [[None, None, None], "art-crit video scene", True]


# --- the local API -------------------------------------------------------------------------------------------------

def call(base, path, body=None, headers=None):
    request = urllib.request.Request(base + path, method="POST" if body is not None else "GET", headers={"Content-Type": "application/json", **(headers or {})},
                                     data=None if body is None else json.dumps(body).encode())
    try:
        with urllib.request.urlopen(request) as res:
            return res.status, res.read(), res.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers


@pytest.fixture
def api(site):  # noqa: F811
    server = serve_in_thread(site / "docs")
    yield f"http://127.0.0.1:{server.server_address[1]}/", server.server_address[1]
    server.shutdown()
    server.server_close()


def test_the_api_offers_the_catalog_and_the_previews_timeline(api):
    base, _ = api
    status, out, headers = call(base, "api/studio")
    assert status == 200 and json.loads(out)["templates"]["duel"]["name"] == "Head to head"
    assert "Access-Control-Allow-Origin" not in headers
    status, out, headers = call(base, "api/studio/plan", {"template": "duel", "slots": [ART(HIGH), None], "cards": [card("title", 0)]})
    plan = json.loads(out)
    assert status == 200 and [s["type"] for s in plan["segments"]] == ["card", "slots"] and plan["total"] == 6
    assert plan["slots"] == [{"type": "video", "secs": 2}, None]  # the fixture run has a short video (played at least 2 s) and plan["labels"] == ["Left", "Right"]
    assert "Access-Control-Allow-Origin" not in headers
    status, out, _ = call(base, "api/studio/plan", {"template": "nope"})
    assert status == 400 and "template" in json.loads(out)["error"]


@needs_tools
def test_the_api_renders_in_the_background_and_serves_only_its_files(api, site):  # noqa: F811
    base, _ = api
    assert json.loads(call(base, "api/local")[1])["video"] is True
    for body, error in [({"runs": [HIGH]}, "expected {studio: spec}"), ({"studio": {"template": "duel", "slots": [ART(HIGH)]}}, "is empty")]:
        status, out, _ = call(base, "api/video", body)
        assert status == 400 and error in json.loads(out)["error"]
    spec = {"template": "duel", "slots": [ART(HIGH), ART(OTHER)], "cards": [card("title", 0, secs=2, heading="Robots")], "still": 2, "music": "none"}
    status, out, _ = call(base, "api/video", {"studio": spec})
    assert status == 200
    job = json.loads(out)["job"]
    assert call(base, "api/video", {"studio": spec})[0] == 400  # one at a time
    for _ in range(240):
        state = json.loads(call(base, f"api/video?job={job}")[1])
        if state["state"] != "running":
            break
        time.sleep(0.5)
    assert state["state"] == "done" and len(state["files"]) == 1, state
    assert (state["title"], state["template"], state["format"], state["slots"], state["length"]) == ("Robots", "Head to head", "16:9", 2, 4)
    name = state["files"][0]
    listing = json.loads(call(base, "api/video/jobs")[1])
    assert listing["jobs"] == []  # a finished render is listed as a file, with its .json's details
    assert [(r["name"], r["title"], r["template"], r["length"]) for r in listing["renders"]] == [(name, "Robots", "Head to head", 4)]
    status, data, headers = call(base, f"api/video/file?name={name}")
    assert status == 200 and headers["Content-Type"] == "video/mp4" and b"ftyp" in data[:32]
    assert "Access-Control-Allow-Origin" not in headers  # another website can't read it
    for bad in ("../../docs/index.html", "page.json", "", name.replace(".mp4", ".json")):
        assert call(base, f"api/video/file?name={bad}")[0] == 404
    assert (site / "videos/studio" / name).is_file()  # outside docs/: never published
    assert call(base, "api/video?job=nope")[0] == 404

    # delete: only a listed video, and its .json goes with it
    for body in ({"name": "../../docs/index.html"}, {"name": "nope.mp4"}, {"job": "nope"}, {"name": 3}):
        assert call(base, "api/video/delete", body)[0] == 400
    assert call(base, "api/video/delete", {"name": name})[0] == 200
    assert not list((site / "videos/studio").iterdir())
    assert json.loads(call(base, "api/video/jobs")[1]) == {"jobs": [], "renders": []}


def test_the_api_refuses_other_hosts_and_other_sites(api, site):  # noqa: F811
    base, port = api
    spec = {"studio": {"template": "duel", "slots": [ART(HIGH), ART(OTHER)]}}
    evil = {"Host": f"evil.example:{port}", "Origin": f"http://evil.example:{port}"}
    assert call(base, "api/video", spec, evil)[0] == 403
    assert call(base, "api/studio/plan", spec["studio"], evil)[0] == 403
    for path in ("api/video?job=x", "api/video/jobs", "api/studio"):
        assert call(base, path, None, {"Host": f"evil.example:{port}"})[0] == 403
    assert call(base, "api/video", spec, {"Origin": "https://evil.example"})[0] == 403
    assert call(base, "api/video/delete", {"name": "x.mp4"}, {"Origin": "https://evil.example"})[0] == 403
    req = urllib.request.Request(base + "api/video", method="POST", data=b"{}", headers={"Content-Type": "text/plain"})
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(req)
    assert e.value.code == 415
    assert not (site / "videos").exists()
