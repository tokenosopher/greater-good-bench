"""Playwright tests for the static viewer in docs/, against the hand-made fixture
site data in tests/fixtures/site/data/ (page "demo" with 3 runs: low/medium/high).

Serves a temp copy of docs/*.html + docs/assets + the fixture data via a plain
ThreadingHTTPServer (no dependency on the CLI's own serve command).
"""

import functools
import http.server
import json
import re
import shutil
import threading
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

REPO = Path(__file__).resolve().parents[1]
FIXTURE_DATA = REPO / "tests/fixtures/site/data"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """The fixture server runs in a background thread; its access logs otherwise leak past pytest's capture
    and scramble the progress output on the shell. `art-crit serve._Handler` silences log_message the same way."""

    def log_message(self, fmt, *args):
        pass


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("site")
    for f in REPO.glob("docs/*.html"):
        shutil.copy(f, root / f.name)
    shutil.copytree(REPO / "docs/classic", root / "classic")
    shutil.copytree(REPO / "docs/assets", root / "assets")
    shutil.copytree(FIXTURE_DATA, root / "data")

    handler = functools.partial(QuietHandler, directory=str(root))
    # a deep accept queue, like `art-crit serve`: Chrome fetches the viewer's ES modules in parallel, and the default (5)
    # resets some of them, leaving a page on Loading… (the flaky timeouts this used to cause)
    server = type("Server", (http.server.ThreadingHTTPServer,), {"request_queue_size": 64})
    httpd = server(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/"
    finally:
        httpd.shutdown()
        thread.join()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        yield b
        b.close()


@pytest.fixture
def page(browser):
    pg = browser.new_page(viewport={"width": 1280, "height": 900})
    console_errors = []
    page_errors = []
    pg.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: page_errors.append(str(e)))
    pg._console_errors = console_errors
    pg._page_errors = page_errors
    yield pg
    pg.close()


def medium_exported(pg, cost=None):
    """Routes demo's page.json so the medium run's export worked (in the fixture it failed), optionally with `cost`."""
    def fulfill(route):
        body = route.fetch().json()
        for r in body["runs"]:
            if r["id"] == MEDIUM_ID:
                r["output"] = {"kind": "godot", "ok": True, "verified": None}
                if cost is not None:
                    r["metrics"]["cost_usd"] = cost
        route.fulfill(json=body)

    pg.route("**/data/demo/page.json*", fulfill)


def assert_no_errors(pg):
    """No uncaught exceptions, and no console errors other than resource 404s
    that a test deliberately provoked (those are checked separately)."""
    assert not pg._page_errors, f"page errors: {pg._page_errors}"
    real_errors = [m for m in pg._console_errors if "404" not in m and "Failed to load resource" not in m]
    assert not real_errors, f"console errors: {real_errors}"


LOW_ID = "model-x-low-20260101-000000"
MEDIUM_ID = "model-x-medium-20260101-000500"
HIGH_ID = "model-x-high-20260101-001000"
ART_HIGH_ID = "model-x-high-20260102-000000"


# ---------------------------------------------------------------- home page
def test_home_lists_page(site, page):
    page.goto(site + "classic/index.html")
    page.wait_for_selector(".card")
    cards = page.locator(".card")
    assert cards.count() == 2
    assert "Demo" in cards.filter(has_text="Demo").inner_text()
    assert page.locator(".card .thumb").count() == 2  # demo: high run's thumb; art: its SVG, no games loaded
    icons = cards.filter(has_text="Demo").locator(".vendor-icon")  # one ring per vendor, its models in the tooltip
    assert icons.count() >= 1 and ":" in icons.first.get_attribute("title")
    assert page.locator("iframe").count() == 0
    assert_no_errors(page)


def test_request_a_prompt_is_local_only(site, page):
    page.goto(site + "classic/index.html")  # the published site has no api/requests: no button, no list
    page.wait_for_selector(".card")
    assert page.locator("#request-open").count() == 0 and page.locator("#requests").is_hidden()
    assert_no_errors(page)


def test_request_a_prompt_saves_and_lists_it_with_its_run_command(site, page):
    saved, puts = [], []

    def api(route):  # what `art-crit serve` answers (src/art_crit/serve.py)
        url, req = route.request.url, route.request
        if url.endswith("/api/local"):
            return route.fulfill(json={"rank": True, "requests": True})
        if "/api/requests" in url and req.method == "GET":
            return route.fulfill(json={"requests": saved, "sets": ["frontier"]})
        if "/api/requests" in url and req.method == "PUT":
            body = req.post_data_json
            puts.append(body)
            saved.append({"id": "r1", "created": "2026-10-13T00:00:00Z", **{k: v for k, v in body["add"].items() if v}})
            return route.fulfill(json={"requests": saved})
        route.fallback()

    page.route("**/api/**", api)
    page.goto(site + "classic/index.html")
    page.locator("#request-open").click()
    dialog = page.locator(".request-dialog")
    assert dialog.is_visible()
    dialog.locator("textarea[name=prompt]").fill("a pelican's bicycle")
    dialog.locator("input[name=kind][value=web]").check(force=True)
    dialog.locator("select[name=set]").select_option("frontier")
    assert dialog.locator("pre.request-cmd").inner_text() == "uv run art-crit run -k web -s frontier 'a pelican'\\''s bicycle'"
    dialog.locator("button[type=submit]").click()
    expect(page.locator(".request-card")).to_have_count(1)
    assert not dialog.is_visible()
    assert puts == [{"add": {"prompt": "a pelican's bicycle", "kind": "web", "title": "", "note": "", "set": "frontier"}}]
    card = page.locator(".request-card")
    assert "Web" in card.locator(".kind-chip").inner_text() and "a pelican's bicycle" in card.inner_text()
    assert_no_errors(page)


# ---------------------------------------------------------------- page.html
def test_page_table_and_sorting(site, page):
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    rows = page.locator("table.runs tbody tr")
    assert rows.count() == 3

    # sort by duration ascending then descending and check row order flips
    page.locator('th[data-key="duration_ms"]').click()
    first_asc = rows.nth(0).inner_text()
    page.locator('th[data-key="duration_ms"]').click()
    first_desc = rows.nth(0).inner_text()
    assert first_asc != first_desc

    assert page.locator("iframe").count() == 0
    assert_no_errors(page)


def test_muse_api_estimates_are_marked_in_all_views(site, page):
    def estimate(route):
        body = route.fetch().json()
        body["runs"][0]["metrics"].update(cost_usd=0.000042, cost_estimated=True,
                                          cost_estimate_proxy="meta/muse-wonder-1.0")
        route.fulfill(json=body)

    page.route("**/data/demo/page.json*", estimate)
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    assert "≈$0.000042" in page.locator('td[data-col="cost_usd"]').first.inner_text()
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    assert "≈$0.000042" in page.locator(".compare-metrics").first.inner_text()
    page.goto(f"{site}run.html?p=demo&r={LOW_ID}")
    page.wait_for_selector(".stat-tiles")
    assert "≈$0.000042" in page.locator(".stat-tiles").inner_text()
    assert_no_errors(page)


def test_clicking_a_row_expands_the_game_inline(site, page):
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr.run-row")
    assert page.locator("iframe").count() == 0

    rows = page.locator("tr.run-row")
    row = lambda effort: rows.filter(has=page.locator("td", has_text=effort)).first
    high = row("high")
    high.locator('td[data-col="effort"]').click()  # click a plain cell
    assert high.get_attribute("aria-expanded") == "true"
    frame = page.locator("tr.run-detail iframe")
    assert frame.count() == 1
    assert "allow-same-origin" not in frame.get_attribute("sandbox")
    assert frame.get_attribute("src").endswith(f"/{HIGH_ID}/game/index.html")

    high.locator('td[data-col="effort"]').click()  # collapse removes the game
    assert page.locator("tr.run-detail").count() == 0 and page.locator("iframe").count() == 0

    # keyboard works too; a run without a game says so
    high.locator("input.run-select").click()  # ticking a row's box doesn't expand it
    assert high.get_attribute("aria-expanded") == "false" and page.locator("tr.run-detail").count() == 0
    row("low").focus()
    page.keyboard.press("Enter")
    assert "No playable build" in page.locator("tr.run-detail").inner_text()
    assert page.locator("iframe").count() == 0
    assert_no_errors(page)


def test_page_harness_column_and_failed_badge(site, page):
    page.set_viewport_size({"width": 1440, "height": 900})  # wide enough for every column beside the details sidebar
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    rows = page.locator("tr.run-row")
    row = lambda effort: rows.filter(has=page.locator("td", has_text=effort)).first

    high_text = row("high").inner_text()
    assert "pi" in high_text and "0.87.1" in high_text
    assert row("medium").locator('td[data-col="harness"] .harness-version').inner_text() == "2.1.284"

    low = row("low")
    assert "failed" in low.locator(".badge-bad").inner_text()

    # expanding the failed row shows its error above the "No playable build" line
    low.locator('td[data-col="effort"]').click()  # plain cell (effort), not a link/button
    detail = page.locator("tr.run-detail")
    assert "pi exited 1: rate limited" in detail.locator(".run-error").inner_text()
    assert "No playable build" in detail.inner_text()
    assert_no_errors(page)


def test_page_shows_labeled_prompt(site, page):
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("#prompt-box:not([hidden])")
    assert page.locator("#prompt-box .prompt-label").inner_text().strip().lower() == "prompt"
    assert page.locator("#prompt").inner_text().startswith("build a tiny demo project")
    # final prompt: present but collapsed to one line until clicked
    final = page.locator("details.final-prompt")
    assert final.is_visible() and final.get_attribute("open") is None
    assert not page.locator("#final-prompt").is_visible()
    final.locator("summary").click()
    assert page.locator("#final-prompt").inner_text().startswith("Task: Goal: build a tiny demo")
    assert_no_errors(page)


def test_page_shows_reference_thumbnails(site, page):
    page.goto(f"{site}classic/page.html?p=demo")
    page.wait_for_selector("#refs-box:not([hidden])")
    imgs = page.locator("#refs img")
    assert imgs.count() == 2  # any number of references, one thumbnail each
    assert "/references/front.png" in imgs.nth(0).get_attribute("src")
    assert imgs.nth(0).get_attribute("alt") == "Reference: front.png"
    imgs.nth(0).click()  # a thumbnail expands to the sidebar's full width, click again collapses
    assert "full" in (imgs.nth(0).get_attribute("class") or "")
    imgs.nth(0).click()
    assert "full" not in (imgs.nth(0).get_attribute("class") or "")
    assert_no_errors(page)


def test_every_column_header_has_hover_help(site, page):
    page.set_viewport_size({"width": 1440, "height": 900})  # wide enough for every column beside the details sidebar
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    headers = page.locator("table.runs thead th")
    assert headers.count() == 13  # caret, thumb, 11 data columns
    helps = {headers.nth(i).inner_text().strip(" ▲▼"): headers.nth(i).get_attribute("data-help") for i in range(13)}
    assert all(t and len(t) > 20 for t in helps.values()), helps
    assert "reasoning" in helps["Reasoning"].lower()
    assert headers.nth(0).get_attribute("title") is None  # no slow native tooltip competing

    # custom tooltip: not instant, shown after ~0.5s, stays on screen, hidden on leave
    tip = page.locator(".col-tip")
    page.locator('th[data-key="tool_calls"]').hover()
    page.wait_for_timeout(150)
    assert not tip.is_visible()
    page.wait_for_timeout(600)
    assert tip.is_visible() and "tools the agent invoked" in tip.inner_text()
    box = tip.bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= page.viewport_size["width"]
    page.locator("h1").hover()
    assert not tip.is_visible()
    assert_no_errors(page)


@pytest.mark.parametrize("width", [1440, 1280, 1100, 900, 721])
def test_runs_table_never_scrolls_horizontally(site, browser, width):
    """Above the phone breakpoint the table fits its wrapper; low-priority columns hide instead of scrolling.
    The fixture has a claude-code harness label, and one run gets a long pinned-upstream model name."""
    ctx = browser.new_context(viewport={"width": width, "height": 900})
    pg = ctx.new_page()
    long_model = "openrouter/deepseek/deepseek-v4.1-flash@deepinfra/fp8"

    def long_name(route):
        body = route.fetch().json()
        body["runs"][0]["model"] = long_model
        route.fulfill(json=body)

    pg.route("**/data/demo/page.json*", long_name)
    pg.goto(f"{site}classic/page.html?p=demo&view=table")
    pg.wait_for_selector("table.runs tbody tr")
    assert pg.locator(".model-via").first.is_visible()
    m = pg.evaluate("""() => { const w = document.querySelector('.table-wrap');
      return { wrap: w.clientWidth, table: w.querySelector('table').scrollWidth }; }""")
    assert m["table"] <= m["wrap"], (width, m)
    for col in ("model", "effort", "verified", "duration_ms", "cost_usd"):
        assert pg.locator(f'tr.run-row:first-child td[data-col="{col}"]').is_visible(), (width, col)
    if m["wrap"] >= 1168:  # the table's own width decides (the details sidebar may sit beside it)
        assert pg.locator('th[data-key="tokens_reasoning"]').is_visible()
    ctx.close()


def test_unreported_zero_cost_is_never_the_cheapest(site, page):
    medium_exported(page, cost=0)  # medium reports no cost, as Agy and Muse do: only high has one, nothing to compare
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    hl = page.locator("#highlights")
    assert hl.locator(".hl", has_text="Cheapest").count() == 0
    assert hl.locator(".hl", has_text="Fastest").count() == 1  # its other metrics still compete
    assert page.locator('td.is-best[data-col="cost_usd"]').count() == 0
    assert_no_errors(page)


def test_page_details_sidebar_collapses_and_remembers(site, browser):
    """Wide: the prompt and highlights sit in a sidebar beside the runs; closing it gives the runs the full width
    (more table columns) and is remembered. Narrow: it is a drawer, closed until opened."""
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(f"{site}classic/page.html?p=demo&view=table")
    pg.wait_for_selector("table.runs tbody tr")
    aside, toggle = pg.locator("#page-aside"), pg.locator("#aside-toggle")
    assert aside.is_visible() and aside.locator("#prompt").is_visible() and aside.locator("#highlights").is_visible()
    assert toggle.get_attribute("aria-expanded") == "true"
    assert not pg.locator('th[data-key="tokens_reasoning"]').is_visible()  # the sidebar takes room from the table
    pg.locator("#aside-close").click()
    assert aside.is_hidden() and toggle.get_attribute("aria-expanded") == "false"
    assert pg.locator('th[data-key="tokens_reasoning"]').is_visible()
    pg.reload()
    pg.wait_for_selector("table.runs tbody tr")
    assert aside.is_hidden()  # remembered
    toggle.click()
    assert aside.is_visible()

    pg.set_viewport_size({"width": 800, "height": 900})  # narrow: a drawer, closed at first
    pg.wait_for_timeout(300)
    assert not aside.is_visible() and toggle.get_attribute("aria-expanded") == "false"
    toggle.click()
    pg.wait_for_timeout(300)
    assert aside.is_visible() and pg.locator("#aside-backdrop").is_visible()
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(300)
    assert not aside.is_visible()
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")
    ctx.close()


def test_runs_table_has_run_time_and_no_output_tokens_column(site, page):
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    assert page.locator('th[data-key="tokens_output"]').count() == 0
    assert page.locator('td[data-col="tokens_output"]').count() == 0
    cell = page.locator('tr.run-row:first-child td[data-col="started_at"]')
    assert cell.is_visible()
    assert cell.inner_text() != "–"
    assert re.search(r"\d{4}", cell.get_attribute("title"))  # the full date (with year) is on hover


def test_runs_table_shows_each_runs_image(site, page):
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    assert page.locator("#gallery").count() == 0  # images live in the table, no separate gallery
    thumbs = page.locator("table.runs img.row-thumb")
    assert thumbs.count() == 2  # medium + high have a thumb, low doesn't
    page.wait_for_function("() => [...document.querySelectorAll('img.row-thumb')].every(i => i.complete && i.naturalWidth > 0)")
    for i in range(2):
        href = thumbs.nth(i).locator("xpath=..").get_attribute("href")
        assert href.startswith("run.html?p=demo&r=model-x-")
    # thumbs stay with their row when sorting
    page.locator('th[data-key="effort"]').click()
    efforts = page.locator("table.runs tbody tr td[data-col='effort']").all_inner_texts()
    has_img = [page.locator("table.runs tbody tr").nth(i).locator("img.row-thumb").count() for i in range(3)]
    assert dict(zip(efforts, has_img)) == {"low": 0, "medium": 1, "high": 1}
    assert page.locator("iframe").count() == 0
    assert_no_errors(page)


def test_page_orders_by_effort_and_highlights_best_completed_run(site, page):
    medium_exported(page)
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    efforts = lambda: page.locator("table.runs tbody tr td[data-col='effort']").all_inner_texts()
    assert efforts() == ["low", "medium", "high"]  # default: model, then effort low -> max (not alphabetical)
    page.locator('th[data-key="effort"]').click()
    assert efforts() == ["low", "medium", "high"]
    page.locator('th[data-key="effort"]').click()
    assert efforts() == ["high", "medium", "low"]

    # the failed low run is cheaper but doesn't compete: medium is the cheapest/fastest completed run
    hl = page.locator("#highlights")
    assert hl.is_visible()
    cheapest = hl.locator(".hl", has_text="Cheapest")
    assert "$0.019" in cheapest.inner_text() and "medium" in cheapest.inner_text()
    assert cheapest.get_attribute("href") == f"run.html?p=demo&r={MEDIUM_ID}"
    assert "1 / 3" in hl.locator(".hl", has_text="Verified").inner_text()  # only high is verified
    best = page.locator("td.is-best")
    assert best.count() == 3 and all(
        best.nth(i).locator("xpath=..").locator("td[data-col='effort']").inner_text() == "medium" for i in range(3)
    )
    assert_no_errors(page)


def test_runs_are_tinted_by_vendor(site, page):
    for url, sel in ((f"{site}classic/page.html?p=demo&view=table", "table.runs tbody tr.run-row"), (f"{site}classic/compare.html?p=demo", ".compare-col")):
        page.goto(url)
        page.wait_for_selector(sel)
        vendors = page.locator(sel).evaluate_all("els => els.map(e => [e.dataset.vendor, e.style.getPropertyValue('--vh')])")
        assert len(vendors) == 3 and len({tuple(v) for v in vendors}) == 1 and vendors[0][0] and vendors[0][1]
        assert_no_errors(page)


def test_run_page_ranks_and_tabs(site, page):
    medium_exported(page)
    page.goto(f"{site}run.html?p=demo&r={MEDIUM_ID}")
    page.wait_for_selector("#metric-strip .stat")
    assert "cheapest of 2" in page.locator("#metric-strip").inner_text()  # the failed run isn't ranked
    page.unroute("**/data/demo/page.json*")
    page.goto(f"{site}run.html?p=demo&r={HIGH_ID}#source")  # the tab is linkable
    page.wait_for_selector("#panel-source:not([hidden]) .source-view pre")
    assert page.locator(".source-files button.active").count() == 1  # first file opens right away
    assert_no_errors(page)


def test_page_defaults_to_the_grid_and_remembers_the_view(site, page):
    page.goto(f"{site}classic/page.html?p=demo")
    page.wait_for_selector("#grid .compare-col")
    assert page.locator("#grid .compare-col").count() == 3
    assert page.locator("#table-wrap").is_hidden() and page.locator("iframe").count() == 0  # games wait for a click
    assert page.locator('[data-view="grid"]').get_attribute("aria-pressed") == "true"
    assert page.locator("#grid [data-play]").count() == 1 and page.locator("#grid a.popout").count() == 1
    assert page.locator("#highlights").is_visible()
    play_all = page.locator("#play-all")
    assert play_all.is_visible()
    play_all.click()
    assert page.locator("#grid iframe").count() == 1 and play_all.is_disabled()

    page.locator('[data-view="table"]').click()
    assert "view=table" in page.url and page.locator("tr.run-row").count() == 3
    assert page.locator("#grid").is_hidden() and play_all.is_hidden()
    page.goto(f"{site}classic/page.html?p=demo")  # remembered in localStorage
    page.wait_for_selector("tr.run-row")
    assert page.locator("#grid").is_hidden() and page.locator('[data-view="table"]').get_attribute("aria-pressed") == "true"
    page.goto(f"{site}classic/page.html?p=demo&view=grid")  # the URL wins
    page.wait_for_selector("#grid .compare-col")
    assert page.locator("#table-wrap").is_hidden()
    page.goto(f"{site}classic/page.html?p=art&view=grid")  # media pages have nothing to play
    page.wait_for_selector("#grid .compare-col")
    assert page.locator("#play-all").is_hidden()
    assert_no_errors(page)


def test_grid_orders_by_rank_and_tints_by_vendor(site, page):
    page.goto(f"{site}classic/page.html?p=art")
    page.wait_for_selector("#grid .compare-col")
    first = page.locator("#grid .compare-col").first
    assert first.locator(".rank-chip").inner_text() == "🥇" and "high" in first.inner_text()
    assert first.get_attribute("data-vendor") and first.evaluate("e => e.style.getPropertyValue('--vh')")
    assert_no_errors(page)


def test_filter_runs_is_a_pure_helper(site, page):
    page.goto(f"{site}classic/page.html?p=demo")
    page.wait_for_selector("#grid .compare-col")
    res = page.evaluate("""async () => {
      const { filterRuns } = await import("./assets/runs.js");
      const run = (id, model, effort, extra = {}) => ({ id, model, effort, state: "complete", output: { ok: true, verified: true }, ...extra });
      const runs = [run("a", "anthropic/c", "low"), run("b", "openai-codex/g", "high"), run("c", "openrouter/deepseek/d", "high", { output: { ok: true, verified: false } }),
                    run("d", "anthropic/c", "high", { state: "failed", output: null }), run("e", "anthropic/c", "high", { output: { ok: false, verified: null } })];
      const ids = (f) => filterRuns(runs, { vendors: [], efforts: [], models: [], verified: false, hideFailed: false, ...f }).map((r) => r.id).join("");
      return [ids({}), ids({ vendors: ["anthropic"] }), ids({ vendors: ["anthropic", "deepseek"], efforts: ["high"] }), ids({ models: ["openai-codex/g"] }), ids({ verified: true }), ids({ hideFailed: true })];
    }""")
    assert res == ["abcde", "ade", "cde", "b", "ab", "abc"]


def test_filter_bar_narrows_grid_and_table_and_lives_in_the_url(site, page):
    many_runs(page, 6)  # r0..r5: even = openai (low, high, medium...), odd = anthropic
    page.goto(f"{site}classic/page.html?p=demo")
    page.wait_for_selector("#grid .compare-col")
    assert page.locator("#grid .compare-col").count() == 6 and page.locator(".vendor-group").count() == 0  # few runs: flat
    assert page.locator("#runs-count").inner_text() == "6 runs"
    chips = page.locator("#filters .filter-chip")
    assert page.locator("#filters .filter-chip[data-vendor]").count() == 2  # tinted vendor chips

    chips.filter(has_text="Anthropic").click()
    assert page.locator("#grid .compare-col").count() == 3 and page.locator("#runs-count").inner_text() == "3 of 6 runs"
    assert "vendor=anthropic" in page.url
    assert page.locator("#filters .filter-chip", has_text="Anthropic").get_attribute("aria-pressed") == "true"
    chips.filter(has_text=re.compile("^high$")).click()
    assert page.locator("#grid .compare-col").count() == 1 and "effort=high" in page.url

    page.locator('[data-view="table"]').click()  # the same filters in the table
    assert page.locator("tr.run-row").count() == 1 and page.locator("#runs-count").inner_text() == "1 of 6 runs"
    page.reload()  # shareable: restored from the URL
    page.wait_for_selector("tr.run-row")
    assert page.locator("tr.run-row").count() == 1
    assert page.locator("#filters .filter-chip", has_text="Anthropic").get_attribute("aria-pressed") == "true"

    page.get_by_text("Clear filters").click()
    assert page.locator("tr.run-row").count() == 6 and "vendor=" not in page.url and "effort=" not in page.url
    assert_no_errors(page)


def test_verified_and_failed_toggles_and_empty_result(site, page):
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("tr.run-row")
    assert page.locator("#filters .filter-chip").count() == 3  # one vendor and one model: only the effort chips
    page.get_by_label("Hide failed").check()  # low (agent failed) and medium (export failed) have nothing to show
    assert page.locator("tr.run-row").count() == 1 and "failed=hide" in page.url
    page.get_by_label("Hide failed").uncheck()
    page.get_by_label("Verified only").check()
    assert page.locator("tr.run-row").count() == 1 and "verified=1" in page.url
    assert page.locator("td.is-best").count() == 0  # a single run isn't compared with anything
    page.goto(f"{site}classic/page.html?p=demo&view=grid&vendor=nobody")
    page.wait_for_selector("#grid .msg")
    assert "No runs match" in page.locator("#grid").inner_text()
    assert_no_errors(page)


def test_selecting_runs_shows_a_bar_that_compares_them(site, page):
    page.goto(f"{site}classic/page.html?p=demo")
    page.wait_for_selector("#grid .compare-col")
    bar = page.locator("#select-bar")
    assert bar.is_hidden()
    boxes = page.locator("#grid input.run-select")
    assert boxes.count() == 3
    boxes.nth(0).check()  # low
    boxes.nth(2).check()  # high
    assert bar.is_visible() and "2 selected" in bar.inner_text()
    link = page.locator("#compare-selected")
    assert link.get_attribute("href") == f"classic/compare.html?p=demo&r={LOW_ID},{HIGH_ID}"

    page.locator('[data-view="table"]').click()  # survives the other view...
    ticked = page.locator("tr.run-row input.run-select").evaluate_all("els => els.map(e => e.checked)")
    assert ticked == [True, False, True]
    page.locator("#filters .filter-chip", has_text=re.compile("^medium$")).click()  # ...and a filter
    assert page.locator("tr.run-row").count() == 1 and "2 selected" in bar.inner_text()
    page.reload()  # ...and a reload
    page.wait_for_selector("tr.run-row")
    assert "2 selected" in page.locator("#select-bar").inner_text()

    page.locator("#select-clear").click()
    assert bar.is_hidden()
    page.get_by_text("Clear filters").click()
    assert page.locator("tr.run-row input.run-select:checked").count() == 0

    page.locator("tr.run-row input.run-select").nth(1).check()  # medium and high
    page.locator("tr.run-row input.run-select").nth(2).check()
    with page.expect_navigation():
        page.locator("#compare-selected").click()
    page.wait_for_selector(".compare-col")
    assert page.url.endswith(f"classic/compare.html?p=demo&r={MEDIUM_ID},{HIGH_ID}")
    assert page.locator(".compare-col").count() == 2 and page.locator(".vendor-group").count() == 0
    assert_no_errors(page)


def test_page_missing_param_shows_message(site, page):
    page.goto(f"{site}classic/page.html")
    page.wait_for_selector(".msg")
    assert "p=" in page.locator(".msg").inner_text() or "slug" in page.locator(".msg").inner_text().lower()


def test_page_invalid_slug_shows_message(site, page):
    page.goto(f"{site}classic/page.html?p=does-not-exist")
    page.wait_for_selector(".msg-error")
    assert not page.locator("table.runs tbody tr").count()
    assert not page._page_errors


# ---------------------------------------------------------------- run.html
def test_run_game_tab_click_to_play(site, page):
    page.goto(f"{site}run.html?p=demo&r={HIGH_ID}")
    page.wait_for_selector("[data-play]")
    assert page.locator("iframe").count() == 0

    overlay = page.locator("[data-play]")
    assert overlay.count() == 1
    overlay.click()

    frame = page.locator("iframe")
    assert frame.count() == 1
    sandbox = frame.get_attribute("sandbox")
    assert "allow-scripts" in sandbox
    assert "allow-same-origin" not in sandbox
    assert page.locator("[data-play]").count() == 0  # overlay replaced, not just hidden

    assert page.locator('a:has-text("Open full screen")').count() == 1
    assert_no_errors(page)


def test_run_whose_export_failed_is_a_finished_agent_run_without_a_build(site, page):
    page.goto(f"{site}run.html?p=demo&r={MEDIUM_ID}")
    page.wait_for_selector("#panel-game")
    panel = page.locator("#panel-game").inner_text()
    assert "no index.html produced" in panel and "No playable build" in panel  # the output step's error, then the message
    assert page.locator("[data-play]").count() == 0 and page.locator(".game-links").count() == 0
    badges = page.locator("#metric-strip .badge-bad").all_inner_texts()
    assert badges == ["export failed"]  # a distinct badge; the agent's state is complete, so no "failed" one
    assert page.locator("#metric-strip .run-error").count() == 0  # and the agent has no error line
    assert "not verified" in page.locator("#metric-strip .run-meta").inner_text()
    page.locator('#tabs button[data-tab="metrics"]').click()
    metrics = page.locator("#panel-metrics").inner_text()
    assert "output.ok" in metrics and "output.error" in metrics
    assert_no_errors(page)


def test_page_shows_export_failed_as_a_badge_and_keeps_it_out_of_the_highlights(site, page):
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("table.runs tbody tr")
    row = page.locator("tr.run-row").filter(has=page.locator("td", has_text="medium")).first
    assert row.locator('td[data-col="verified"] .badge-bad').inner_text() == "export failed"
    hl = page.locator("#highlights")
    assert "medium" not in hl.inner_text()  # no output: it never wins a highlight, though the agent completed
    assert not row.locator("td.is-best").count()
    row.locator('td[data-col="effort"]').click()
    detail = page.locator("tr.run-detail")
    assert "no index.html produced" in detail.locator(".run-error").inner_text()
    assert "No playable build" in detail.inner_text()
    assert_no_errors(page)


def test_run_transcript_tool_calls_and_filters(site, page):
    page.goto(f"{site}run.html?p=demo&r={HIGH_ID}")
    page.locator('#tabs button[data-tab="transcript"]').click()
    page.wait_for_selector(".transcript .turn")

    assert page.locator(".tool-block").count() == 5  # bash, ls, write, edit, read
    assert page.locator(".badge-error").count() == 1  # the bash call errors
    assert page.locator(".tool-duration").first.inner_text() == "480ms"  # durationMs on the toolResult

    # a long write is collapsed behind "File (N lines)" and opens on click
    file_toggle = page.locator("details.out-collapse summary", has_text="File (31 lines)")
    assert file_toggle.count() == 1
    written = page.locator("details.out-collapse:has(summary:has-text('File')) pre.code")
    assert not written.is_visible()
    file_toggle.click()
    assert written.is_visible() and "print('line 30')" in written.inner_text()

    # an image in a tool result is shown as an <img> thumbnail with a caption, never as base64 text
    text = page.locator(".transcript").inner_text()
    assert "[image: image/png, 7 KB]" in text and "iVBORw0KGgo" not in text
    thumb = page.locator("figure.tool-image img")
    assert thumb.count() == 1 and thumb.get_attribute("src").startswith("data:image/png;base64,")
    assert thumb.evaluate("img => img.decode().then(() => img.naturalWidth)") == 48

    # each turn shows +m:ss since the session started, with the clock time on hover
    elapsed = page.locator(".turn-head .elapsed").first
    assert elapsed.inner_text().startswith("+0:") and elapsed.get_attribute("title")

    # thinking hidden by default, shown after toggle
    thinking = page.locator(".thinking-block").first
    assert not thinking.is_visible()
    page.locator('button:has-text("Show thinking")').click()
    assert thinking.is_visible()

    total_turns = page.locator(".transcript .turn").count()
    page.locator('[data-filter-btn="errors"]').click()
    visible_after_errors = page.locator(".transcript .turn:visible").count()
    assert 0 < visible_after_errors < total_turns

    page.locator('[data-filter-btn="tools"]').click()
    visible_tools = page.locator(".transcript .turn:visible").count()
    assert visible_tools >= visible_after_errors

    page.locator('[data-filter-btn="all"]').click()
    assert page.locator(".transcript .turn:visible").count() == total_turns

    # XSS: literal <script> in assistant text must render as visible text, not execute
    assert "<script>" in page.locator(".transcript").inner_text()
    # code blocks keep literal < > & (no double escaping); javascript: links are neutralized
    assert "if x < 5 && y > 2:" in page.locator(".transcript").inner_text()
    assert page.locator(".transcript a[href^='javascript']").count() == 0
    assert page.locator(".transcript a[href='https://example.com']").count() == 1
    assert_no_errors(page)


def test_run_transcript_null_session(site, page):
    page.goto(f"{site}run.html?p=demo&r={LOW_ID}")
    page.locator('#tabs button[data-tab="transcript"]').click()
    page.wait_for_selector("#panel-transcript .msg")
    assert "No transcript" in page.locator("#panel-transcript").inner_text()
    assert_no_errors(page)


def test_run_source_tab_shows_file_content(site, page):
    page.goto(f"{site}run.html?p=demo&r={HIGH_ID}")
    page.locator('#tabs button[data-tab="source"]').click()
    page.wait_for_selector(".source-files button")
    assert page.locator(".source-files button").count() == 2
    page.locator('.source-files button:has-text("README.md")').click()
    page.wait_for_function("() => document.querySelector('.source-view pre').textContent.includes('Demo')")
    assert "Demo" in page.locator(".source-view pre").inner_text()
    assert_no_errors(page)


def test_run_shows_harness_and_failed_state(site, page):
    page.goto(f"{site}run.html?p=demo&r={LOW_ID}")
    page.wait_for_selector("#metric-strip")
    strip_text = page.locator("#metric-strip").inner_text()
    assert "pi 0.87.1" in strip_text
    assert "failed" in page.locator("#metric-strip .badge-bad").inner_text()
    assert "pi exited 1: rate limited" in page.locator(".run-error").inner_text()

    page.locator('#tabs button[data-tab="metrics"]').click()
    metrics_text = page.locator("#panel-metrics").inner_text()
    assert "harness" in metrics_text.lower() and "pi 0.87.1" in metrics_text
    assert "failed" in metrics_text
    assert "pi exited 1: rate limited" in metrics_text
    assert_no_errors(page)


def test_run_invalid_run_id_shows_message(site, page):
    page.goto(f"{site}run.html?p=demo&r=does-not-exist")
    page.wait_for_selector(".msg-error")
    assert not page._page_errors


# ---------------------------------------------------------------- compare.html
def test_compare_shows_metrics_and_games_only(site, page):
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    cols = page.locator(".compare-col")
    assert cols.count() == 3
    text = page.locator("#columns").inner_text()
    assert "Tool calls" not in text and "Source" not in text
    assert page.locator("#file-picker, .tool-summary-list").count() == 0
    for i in range(3):
        metrics = cols.nth(i).locator(".compare-metrics").inner_text()
        assert "tokens" in metrics and "$" in metrics

    # games never boot on their own; in the fixture only the high run has one
    assert page.locator("iframe").count() == 0
    assert page.locator("[data-play]").count() == 1
    page.locator("[data-play]").click()
    assert page.locator("iframe").count() == 1
    assert "allow-same-origin" not in page.locator("iframe").get_attribute("sandbox")
    assert page.locator(".compare-col", has_text="No playable build recorded").count() == 2
    assert page.locator(".compare-col", has_text="export failed").count() == 1
    assert_no_errors(page)


def test_compare_shows_harness_in_metrics_line(site, page):
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    cols = page.locator(".compare-col")
    for i in range(3):
        metrics = cols.nth(i).locator(".compare-metrics").inner_text()
        assert metrics.startswith(("pi", "claude-code"))
    # the failed run's column shows its badge next to the title and its error
    low_col = cols.filter(has_text="low").first
    assert "failed" in low_col.locator("h3 .badge-bad").inner_text()
    assert "pi exited 1: rate limited" in low_col.locator(".run-error").inner_text()
    assert_no_errors(page)


def test_compare_popout_opens_sandboxed_play_window(site, page):
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    # only the run with a game gets the button (the other two have nothing to show)
    assert page.locator(".compare-col a.popout").count() == 1
    pop = page.locator(".compare-col", has=page.locator("a.popout")).locator("a.popout")
    assert pop.get_attribute("href") == f"play.html?p=demo&r={HIGH_ID}"
    assert pop.get_attribute("data-play") is None
    with page.expect_popup() as info:
        pop.click()
    popup = info.value
    popup.on("pageerror", lambda e: page._page_errors.append(str(e)))
    popup.wait_for_selector("#play iframe")
    assert popup.url.endswith(f"play.html?p=demo&r={HIGH_ID}")
    frames = popup.locator("iframe")
    assert frames.count() == 1
    assert frames.get_attribute("sandbox") == "allow-scripts allow-pointer-lock"
    assert frames.get_attribute("src").endswith("game/index.html")
    bar = popup.locator("#play-bar").inner_text()
    assert "model-x" in bar and "high" in bar
    assert popup.locator("#play-bar a").get_attribute("href") == f"run.html?p=demo&r={HIGH_ID}"
    assert_no_errors(page)
    popup.close()


def test_play_media_run_uses_img_only(site, page):
    page.goto(f"{site}play.html?p=art&r={ART_HIGH_ID}")
    page.wait_for_selector(".media-grid")
    page.wait_for_function("() => [...document.querySelectorAll('.media-grid img')].every(i => i.complete && i.naturalWidth > 0)")
    assert page.locator(".media-grid img").count() == 2
    assert page.evaluate("window.svgRan") is None
    assert page.locator("#play svg, #play object, #play embed, #play iframe").count() == 0
    assert_no_errors(page)


def test_play_bad_params_show_messages(site, page):
    page.goto(f"{site}play.html")
    page.wait_for_selector(".msg-error")
    assert "Missing" in page.locator("#play").inner_text()
    page.goto(f"{site}play.html?p=demo&r=nope")
    page.wait_for_selector(".msg-error")
    assert 'No run "nope"' in page.locator("#play").inner_text()
    assert_no_errors(page)


def test_compare_play_all_starts_every_game(site, page):
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    btn = page.locator("#play-all")
    assert btn.is_enabled() and page.locator("iframe").count() == 0
    btn.click()
    assert page.locator("[data-play]").count() == 0
    assert page.locator("iframe").count() == 1
    assert btn.is_disabled()  # nothing left to play

    page.goto(f"{site}classic/compare.html?p=demo&r={LOW_ID}")  # no games at all
    page.wait_for_selector(".compare-col")
    assert page.locator("#play-all").is_disabled()
    assert_no_errors(page)


def test_compare_can_be_limited_to_listed_runs(site, page):
    page.goto(f"{site}classic/compare.html?p=demo&r={MEDIUM_ID},{HIGH_ID}")
    page.wait_for_selector(".compare-col")
    assert page.locator(".compare-col").count() == 2
    assert_no_errors(page)


# ---------------------------------------------------------------- media pages (kind "media")
def test_media_table_shows_file_count_and_expands_outputs(site, page):
    page.goto(f"{site}classic/page.html?p=art&view=table")
    page.wait_for_selector("tr.run-row")
    assert page.locator("#gallery").count() == 0  # the grid replaced the old gallery
    rows = page.locator("tr.run-row")
    high = rows.filter(has=page.locator("td", has_text="high")).first
    assert high.locator('td[data-col="thumb"] .media-count').inner_text() == "×3"
    assert rows.filter(has=page.locator("td", has_text="low")).first.locator(".media-count").count() == 0
    assert high.locator('td[data-col="thumb"]').get_attribute("data-col") == "thumb"

    high.locator('td[data-col="effort"]').click()
    detail = page.locator("tr.run-detail")
    assert detail.locator(".media-item").count() == 3
    assert detail.locator("video").count() == 1 and detail.locator("iframe").count() == 0
    assert_no_errors(page)


def test_media_card_has_badge_hero_and_swappable_strip(site, page):
    page.goto(f"{site}classic/page.html?p=art")
    page.wait_for_selector(".compare-col")
    card = page.locator(".compare-col").filter(has_text="high")
    assert card.locator(".media-count").inner_text() == "3 files · 1 video"
    assert card.locator(".media-count").is_visible()
    hero = card.locator(".media-box > video")
    assert hero.get_attribute("preload") == "none" and hero.get_attribute("poster").endswith("/media/clip.poster.jpg")
    assert card.locator(".media-link").count() == 0  # a video hero isn't a link: a click plays it
    box_before = card.locator(".media-box").bounding_box()
    strip = card.locator(".media-strip .media-thumb")
    assert strip.count() == 3 and strip.nth(1).get_attribute("aria-current") == "true"
    strip.nth(0).click()  # circle.svg: shown through <img> only
    assert card.locator(".media-box > video").count() == 0
    assert card.locator(".media-box > a.media-link > img").get_attribute("src").endswith("/media/circle.svg")
    assert card.locator(".media-count").inner_text() == "3 files · 1 video"
    assert strip.nth(0).get_attribute("aria-current") == "true"
    assert card.locator(".media-box").bounding_box() == box_before  # same card height
    assert page.evaluate("window.svgRan") is None
    assert card.locator("svg, object, embed, iframe").count() == 0
    # a run without output has no badge or strip
    assert page.locator(".compare-col").filter(has_text="low").locator(".media-count, .media-strip").count() == 0
    # clicking an image hero opens the run page
    card.locator(".media-link").click()
    page.wait_for_url(f"**/run.html?p=art&r={ART_HIGH_ID}")
    page.wait_for_selector(".media-grid")
    assert_no_errors(page)


def test_media_run_output_tab_shows_images_and_video(site, page):
    page.goto(f"{site}run.html?p=art&r={ART_HIGH_ID}")
    page.wait_for_selector(".media-grid")
    assert page.locator('#tabs button[data-tab="game"]').inner_text() == "Output"
    imgs = page.locator(".media-grid img")
    assert imgs.count() == 2
    page.wait_for_function("() => [...document.querySelectorAll('.media-grid img')].every(i => i.complete && i.naturalWidth > 0)")
    # full size: one output per row, each at its recorded size (circle.svg 120×80, dot.png 64×48), not a 4:3 box
    assert page.locator(".media-grid.is-full .media-box").count() == 0
    sizes = [(round(b["width"]), round(b["height"])) for b in (imgs.nth(i).bounding_box() for i in range(2))]
    assert sizes == [(120, 80), (64, 48)]
    figs = [page.locator(".media-item").nth(i).bounding_box() for i in range(3)]
    assert figs[0]["y"] < figs[1]["y"] < figs[2]["y"]
    video = page.locator(".media-grid video")
    assert video.get_attribute("poster").endswith("/media/clip.poster.jpg")
    assert video.get_attribute("autoplay") is None and video.evaluate("v => v.paused")
    # the SVG is only ever an <img>: its embedded <script> must not have run, and there's no
    # inline <svg> or <object>/<embed>/<iframe> carrying model output
    assert page.evaluate("window.svgRan") is None
    assert page.locator("#panel-game svg, #panel-game object, #panel-game embed, #panel-game iframe").count() == 0
    svg_link = page.locator(".media-grid a", has_text="download").first
    assert svg_link.get_attribute("download") == "circle.svg"
    assert "1.0s" in page.locator(".media-grid").inner_text()
    assert_no_errors(page)


def test_media_run_without_output_says_so(site, page):
    page.goto(f"{site}run.html?p=art&r=model-x-low-20260102-000000")
    page.wait_for_selector("#panel-game .msg")
    assert "No output files" in page.locator("#panel-game").inner_text()
    assert "no files in ./output/" in page.locator(".run-error").inner_text()


def test_media_compare_shows_outputs_and_no_play_all(site, page):
    page.goto(f"{site}classic/compare.html?p=art")
    page.wait_for_selector(".compare-col")
    assert page.locator(".compare-col").count() == 2
    assert page.locator(".compare-col .media-box").count() == 1 and page.locator(".compare-col .media-thumb").count() == 3
    assert page.locator(".compare-col .media-count").inner_text() == "3 files · 1 video"
    assert page.locator(".compare-col", has_text="No output files recorded").count() == 1
    assert not page.locator("#play-all").is_visible()
    assert_no_errors(page)


def test_group_by_vendor_orders_groups_by_best_rank(site, page):
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    res = page.evaluate("""async () => {
      const { groupByVendor } = await import("./assets/runs.js");
      const run = (id, model, rank) => ({ id, model, rank });
      const names = (rs) => groupByVendor(rs).map((g) => g.name + ":" + g.runs.map((r) => r.id).join(","));
      const plain = [run("a1", "anthropic/claude-x"), run("o1", "openai-codex/gpt-6"), run("a2", "anthropic/claude-x"), run("d1", "openrouter/deepseek/v4"), run("z1", "zeta/m")];
      const ranked = [run("o1", "openai-codex/gpt-6", 1), run("a1", "anthropic/claude-x", 2), run("a2", "anthropic/claude-x"), run("d1", "openrouter/deepseek/v4")];
      return [names(plain), names(ranked)];
    }""")
    assert res[0] == ["Anthropic:a1,a2", "DeepSeek:d1", "OpenAI:o1", "Zeta:z1"]  # unranked: alphabetical, order inside kept
    assert res[1] == ["OpenAI:o1", "Anthropic:a1,a2", "DeepSeek:d1"]  # best rank first, then unranked
    assert_no_errors(page)


def many_runs(page, n):
    """Serve demo's page.json with n runs from two vendors (copies of the first run under new ids)."""
    def fulfil(route):
        body = route.fetch().json()
        base = body["runs"][2]
        body["runs"] = [
            {**base, "id": f"r{i}", "model": ("anthropic/claude-x" if i % 2 else "openai-codex/gpt-6"), "effort": ["low", "medium", "high"][i % 3]}
            for i in range(n)
        ]
        route.fulfill(json=body)
    page.route("**/data/demo/page.json*", fulfil)


def test_compare_with_few_runs_is_flat_equal_columns(site, page):
    many_runs(page, 4)  # two vendors, but 4 runs: no grouping
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    assert page.locator(".vendor-group").count() == 0
    boxes = [page.locator(".compare-col").nth(i).bounding_box() for i in range(4)]
    assert len({round(b["y"]) for b in boxes}) == 1 and len({round(b["width"]) for b in boxes}) == 1
    columns = page.locator(".compare-columns").bounding_box()
    assert boxes[3]["x"] + boxes[3]["width"] >= columns["x"] + columns["width"] - 1  # fills the page
    page.goto(f"{site}classic/compare.html?p=demo&r=r1")  # no grouping for a single run either
    page.wait_for_selector(".compare-col")
    assert page.locator(".vendor-group, .vendor-head").count() == 0
    assert_no_errors(page)


def test_compare_groups_five_or_more_runs_by_vendor(site, page):
    many_runs(page, 6)
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    assert page.locator(".vendor-group").count() == 2
    assert page.locator(".vendor-head").first.inner_text().split()[0].lower() in ("anthropic", "openai")
    assert "3 runs" in page.locator(".vendor-head").first.inner_text()
    assert page.locator(".vendor-group .compare-columns > .compare-col").count() == 6
    assert_no_errors(page)


def test_compare_lays_runs_out_in_a_wrapping_grid(site, page):
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{site}classic/compare.html?p=demo")
    page.wait_for_selector(".compare-col")
    boxes = [page.locator(".compare-col").nth(i).bounding_box() for i in range(3)]
    assert len({round(b["y"]) for b in boxes}) == 1  # wide: 3 side by side, equal widths
    assert len({round(b["width"]) for b in boxes}) == 1
    page.set_viewport_size({"width": 900, "height": 900})
    boxes = [page.locator(".compare-col").nth(i).bounding_box() for i in range(3)]
    assert boxes[0]["y"] == boxes[1]["y"] < boxes[2]["y"]  # narrower: wraps into a second row
    assert boxes[2]["x"] == boxes[0]["x"]
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")  # no sideways scrolling
    page.set_viewport_size({"width": 390, "height": 900})
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert_no_errors(page)


# ---------------------------------------------------------------- your ranking
def test_ranking_is_shown_read_only_on_the_published_site(site, page):
    page.goto(f"{site}classic/page.html?p=art&view=table")
    page.wait_for_selector("tr.run-row")
    assert page.locator('th[data-key="rank"]').get_attribute("aria-sort") == "ascending"  # ranked: default sort
    first = page.locator("tr.run-row").first
    assert first.locator('td[data-col="rank"]').inner_text() == "🥇" and "high" in first.inner_text()
    assert page.locator(".rank-select").count() == 0 and page.locator("#rank-status").count() == 0
    page.goto(f"{site}classic/page.html?p=art")  # the grid too: ranked first
    page.wait_for_selector(".compare-col")
    assert page.locator(".compare-col").first.locator(".rank-chip").inner_text() == "🥇"
    page.goto(f"{site}classic/compare.html?p=art")
    page.wait_for_selector(".compare-col")
    assert page.locator(".compare-col").first.locator(".rank-chip").inner_text() == "🥇"
    page.goto(f"{site}run.html?p=art&r={ART_HIGH_ID}")
    page.wait_for_selector("#title .rank-chip")
    assert_no_errors(page)


@pytest.fixture
def bench_served(tmp_path):
    """The viewer served by `art-crit serve` itself (which has the local ranking API) on a copy of the fixture site."""
    from art_crit.serve import serve_in_thread

    docs = tmp_path / "docs"
    docs.mkdir()
    for f in REPO.glob("docs/*.html"):
        shutil.copy(f, docs / f.name)
    shutil.copytree(REPO / "docs/classic", docs / "classic")
    shutil.copytree(REPO / "docs/assets", docs / "assets")
    shutil.copytree(FIXTURE_DATA, docs / "data")
    server = serve_in_thread(docs)
    yield docs, f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()
    server.server_close()


def test_ranking_can_be_edited_through_bench_serve(bench_served, page):
    import json
    import re

    docs, base = bench_served
    page.goto(f"{base}classic/page.html?p=demo&view=table")
    page.wait_for_selector(".rank-select")
    assert page.locator(".rank-select").count() == 3
    assert "publish" in page.locator("#rank-status").inner_text()

    row = lambda effort: page.locator("tr.run-row").filter(has=page.locator('td[data-col="effort"]', has_text=re.compile(f"^{effort}$"))).first
    row("medium").locator(".rank-select").select_option("1")
    page.wait_for_function("() => document.getElementById('rank-status').textContent.startsWith('saved')")
    assert page.locator("tr.run-detail").count() == 0  # picking a rank doesn't expand the row
    row("high").locator(".rank-select").select_option("2")
    page.wait_for_function("() => document.getElementById('rank-status').textContent.startsWith('saved')")

    ranking = json.loads((docs / "data/demo/ranking.json").read_text())["ranks"]
    assert ranking == {MEDIUM_ID: 1, HIGH_ID: 2}
    results = {r["id"]: r["rank"] for r in json.loads((docs / "data/demo/page.json").read_text())["runs"]}
    assert results == {MEDIUM_ID: 1, HIGH_ID: 2, LOW_ID: None}

    page.reload()  # sorted by the saved ranking now
    page.wait_for_selector(".rank-select")
    efforts = page.locator("table.runs tbody tr td[data-col='effort']").all_inner_texts()
    assert efforts == ["medium", "high", "low"]
    assert_no_errors(page)


def test_covers_can_be_overridden_through_bench_serve(bench_served, page):
    """Run page, local only: each image gets "Use as run thumbnail" / "Use as page cover" toggles that write covers.json."""
    import json

    docs, base = bench_served
    run_id = "model-x-high-20260102-000000"
    covers = docs / "data/art/covers.json"
    page.goto(f"{base}run.html?p=art&r={run_id}")
    page.wait_for_selector(".cover-btn")
    assert page.locator(".cover-btn").count() == 6  # a thumbnail and a page-cover button for each image (svg, png; the video has a poster)
    # this run's default thumb is its first image: that is no override, so nothing is pressed until the owner sets one
    assert page.locator(".cover-btn[aria-pressed=true]").count() == 0
    page.locator(".cover-btn", has_text="Use as run thumbnail").first.click()
    page.wait_for_function("() => document.querySelectorAll('.cover-btn[aria-pressed=true]').length === 1")
    page.locator(".cover-btn[aria-pressed=true]").click()  # clears it again
    page.wait_for_function("() => document.querySelectorAll('.cover-btn[aria-pressed=true]').length === 0")
    assert not covers.exists()
    page.reload()
    page.wait_for_selector(".cover-btn")
    assert page.locator(".cover-btn[aria-pressed=true]").count() == 0
    page.locator(".cover-btn", has_text="Use as run thumbnail").last.click()
    page.wait_for_function("() => document.querySelector('.cover-status').textContent.startsWith('Saved')")
    page.locator(".cover-btn", has_text="Use as page cover").first.click()
    page.wait_for_function("() => document.querySelectorAll('.cover-btn[aria-pressed=true]').length === 2")
    saved = json.loads(covers.read_text())
    assert set(saved) == {"thumbs", "page"} and saved["page"]["run"] == run_id
    assert saved["thumbs"][run_id] != saved["page"]["image"]
    runs = {r["id"]: r for r in json.loads((docs / "data/art/page.json").read_text())["runs"]}
    assert runs[run_id]["thumb"] == saved["thumbs"][run_id]

    for left in (1, 0):  # a pressed button clears its override
        page.locator(".cover-btn[aria-pressed=true]").first.click()
        page.wait_for_function("(n) => document.querySelectorAll('.cover-btn[aria-pressed=true]').length === n", arg=left)
    assert not covers.exists()
    assert_no_errors(page)


def test_the_owners_page_cover_starts_the_home_slideshow(bench_served, page):
    """The tile and the featured slideshow's first slide both show the picked image, not the run's default thumbnail."""
    import json

    from art_crit.site import rebuild

    docs, base = bench_served
    runs = docs / "data/art/runs"
    other = runs / "model-y-high-20260102-000000"
    shutil.copytree(runs / ART_HIGH_ID, other)  # a second model, so the featured picture is a slideshow
    record = json.loads((other / "run.json").read_text())
    (other / "run.json").write_text(json.dumps({**record, "id": other.name, "model": "other-org/model-y"}))
    (docs / "data/art/covers.json").write_text(json.dumps({"page": {"run": ART_HIGH_ID, "image": "media/dot.png"}}))
    rebuild(docs.parent)

    page.goto(base + "index.html")
    page.wait_for_selector(".v2-feature-media .slide")
    srcs = page.locator(".v2-feature-media .slide").evaluate_all("els => els.map(e => e.getAttribute('src'))")
    assert len(srcs) == 2 and srcs[0].endswith(f"{ART_HIGH_ID}/media/dot.png")
    assert page.locator(".v2-feature-media .slide.is-on").get_attribute("src") == srcs[0]
    assert_no_errors(page)


def test_the_video_studio_makes_a_video_only_on_the_local_server(bench_served, site, page):
    import json

    from art_crit.site import rebuild

    docs, base = bench_served
    runs = docs / "data/art/runs"
    other = runs / "model-y-high-20260102-000000"
    shutil.copytree(runs / ART_HIGH_ID, other)
    record = json.loads((other / "run.json").read_text())
    (other / "run.json").write_text(json.dumps({**record, "id": other.name, "model": "other-org/model-y"}))
    rebuild(docs.parent)
    ids = f"{ART_HIGH_ID},{other.name}"

    # the published site (no local API): no link to the studio, and the studio says it runs locally
    page.goto(f"{site}compare.html?p=art&r=model-x-low-20260102-000000,{ART_HIGH_ID}")
    page.wait_for_selector(".v2-col")
    assert page.locator(".v2-studio").count() == 0
    page.goto(f"{site}studio.html")
    page.wait_for_selector("text=runs on your own machine")

    # art-crit serve: the compare page opens the studio with its runs in the slots
    page.goto(f"{base}compare.html?p=art&r={ids}")
    page.locator(".v2-studio a").click()
    page.wait_for_selector(".st-slot.is-filled")
    assert "Head to head" in page.locator('.st-template[aria-pressed="true"]').inner_text()
    assert page.locator(".st-slot.is-filled").count() == 2
    page.wait_for_selector(".st-seg")  # the timeline comes from api/studio/plan
    assert page.locator(".st-seg").all_inner_texts()[0].startswith("Hook:")  # like `art-crit video`: the opening first

    # a new card: its heading shows in the preview as it is typed, and it joins the timeline
    page.get_by_role("button", name="+ Question").click()
    page.locator(".st-editor input[type=text]").fill("Robots or not?")
    assert page.locator(".st-card-heading").inner_text() == "Robots or not?"
    page.get_by_role("button", name="Done").click()
    page.wait_for_function("() => [...document.querySelectorAll('.st-seg-name')].some((n) => n.textContent === 'Question: Robots or not?')")

    # the picker lists runs of every page; Empty this slot leaves the render waiting for it
    page.get_by_role("button", name="Slot Right:").click()
    page.get_by_role("button", name="Empty this slot").click()
    assert page.locator(".st-render").is_disabled() and "1 left" in page.locator(".st-settings").inner_text()
    page.get_by_role("button", name="Slot Right:").click()
    page.locator('.st-result[aria-label^="Use Model Y"]').first.click()

    page.get_by_label("Seconds for each still image").select_option("2")
    page.get_by_label("Music").select_option("none")
    page.get_by_role("button", name="Render video").click()
    # this render is listed first, under its template's name (no title card; other tests' renders may be in this process's job list)
    row = page.locator(".st-render-row").first
    expect(row).to_contain_text("Head to head")
    expect(row.locator(".st-state")).to_have_text("Done", timeout=180000)
    assert row.locator("video").count() == 1
    assert row.locator("a[download]").get_attribute("download").endswith("-duel.mp4")
    assert len(list((docs.parent / "videos/studio").glob("*-duel.mp4"))) == 1

    # Delete asks first, then removes the file (and its .json) and the row
    page.once("dialog", lambda d: d.dismiss())
    row.get_by_role("button", name="Delete").click()
    assert len(list((docs.parent / "videos/studio").glob("*-duel.mp4"))) == 1  # dismissed: kept
    page.once("dialog", lambda d: d.accept())
    row.get_by_role("button", name="Delete").click()
    expect(page.locator(".st-render-row")).to_have_count(0)
    assert not list((docs.parent / "videos/studio").iterdir())
    assert_no_errors(page)


# ---------------------------------------------------------------- community votes
class VoteApi:
    """In-memory stand-in for the Worker's /api (cloudflare/votes.mjs): the same JSON, plus a sign-in that just flips a flag."""

    def __init__(self, runs, signed_in=False, others=None):
        self.runs, self.signed_in = runs, signed_in
        self.others = others or {}  # other people's votes: {run id: {"hearts": 2, "gold": 1}}
        self.hearts, self.medals = set(), {}
        self.fail = None  # an error message to answer every write with

    def state(self):
        totals = {r: {"hearts": 0, "gold": 0, "silver": 0, "bronze": 0, **self.others.get(r, {})} for r in self.runs}
        for run in self.hearts:
            totals[run]["hearts"] += 1
        for medal, run in self.medals.items():
            totals[run][medal] += 1
        mine = {"hearts": sorted(self.hearts), **{m: self.medals.get(m) for m in ("gold", "silver", "bronze")}}
        return {"user": {"login": "alice"} if self.signed_in else None, "totals": totals, "mine": mine if self.signed_in else None}

    def handle(self, route):
        import json
        from urllib.parse import parse_qs, urlsplit

        request = route.request
        url = urlsplit(request.url)
        name = url.path.rsplit("/api/", 1)[1]
        if name not in ("login", "logout", "votes", "heart", "medal"):
            return route.fallback()  # e.g. the ranking probe api/local
        if name == "login":  # GitHub and back, in one hop
            self.signed_in = True
            return route.fulfill(status=302, headers={"Location": parse_qs(url.query)["return"][0]})
        if name == "logout":
            self.signed_in = False
            return route.fulfill(status=200, content_type="application/json", body="{}")
        if name == "votes":
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(self.state()))
        body = json.loads(request.post_data)
        if self.fail:
            return route.fulfill(status=400, content_type="application/json", body=json.dumps({"error": self.fail}))
        if not self.signed_in:
            return route.fulfill(status=401, content_type="application/json", body=json.dumps({"error": "sign in with GitHub first"}))
        if name == "heart":
            (self.hearts.add if body["on"] else self.hearts.discard)(body["run"])
        else:  # a medal frees its old result and any other medal on the new one
            self.medals = {m: r for m, r in self.medals.items() if m != body["medal"] and r != body["run"]}
            if body["run"] is not None:
                self.medals[body["medal"]] = body["run"]
        route.fulfill(status=200, content_type="application/json", body=json.dumps(self.state()))


def vote_api(page, **kwargs):
    api = VoteApi([LOW_ID, MEDIUM_ID, HIGH_ID], **kwargs)
    page.route("**/api/**", api.handle)
    return api


def card(page, run_id):
    return page.locator(".compare-col").filter(has=page.locator(f'h3 a[href$="r={run_id}"]'))


def heart(page, run_id):
    return card(page, run_id).locator(".vote-heart")


def medal(page, run_id, name):
    return card(page, run_id).locator(".vote-medal").nth(["gold", "silver", "bronze"].index(name))


def test_no_vote_controls_where_there_is_no_vote_api(site, page):
    for view in ("classic/page.html?p=demo", "classic/page.html?p=demo&view=table", "classic/compare.html?p=demo", f"run.html?p=demo&r={HIGH_ID}"):
        page.goto(site + view)
        page.wait_for_selector("h1")
        page.wait_for_load_state("networkidle")
        assert page.locator(".votes").count() == 0 and page.locator(".auth").count() == 0, view
    assert_no_errors(page)


def test_signed_out_visitors_see_totals_and_sign_in_to_vote(site, page):
    vote_api(page, others={HIGH_ID: {"hearts": 7, "gold": 2}})
    page.goto(f"{site}classic/page.html?p=demo")
    expect(card(page, HIGH_ID).locator(".votes-label")).to_have_text("Community votes")
    expect(heart(page, HIGH_ID).locator(".vote-n")).to_have_text("7")
    expect(medal(page, HIGH_ID, "gold").locator(".vote-n")).to_have_text("2")
    expect(page.locator(".auth")).to_have_text("Sign in with GitHub")
    expect(heart(page, HIGH_ID)).to_have_attribute("title", "Sign in with GitHub to vote")

    heart(page, HIGH_ID).click()  # goes to GitHub and comes back to this very page, signed in
    expect(page.locator(".auth")).to_contain_text("@alice")
    assert page.url == f"{site}classic/page.html?p=demo"
    expect(heart(page, HIGH_ID)).to_have_attribute("aria-pressed", "false")  # that click only signed in
    heart(page, HIGH_ID).click()
    expect(heart(page, HIGH_ID)).to_have_attribute("aria-pressed", "true")
    expect(heart(page, HIGH_ID).locator(".vote-n")).to_have_text("8")
    expect(heart(page, LOW_ID).locator(".vote-n")).to_have_text("")  # other results are untouched
    assert_no_errors(page)


def test_hearts_toggle_and_a_user_can_heart_several_results(site, page):
    vote_api(page, signed_in=True)
    page.goto(f"{site}classic/page.html?p=demo")
    for run_id in (LOW_ID, HIGH_ID):
        heart(page, run_id).click()
        expect(heart(page, run_id)).to_have_attribute("aria-pressed", "true")
    expect(heart(page, MEDIUM_ID)).to_have_attribute("aria-pressed", "false")
    heart(page, LOW_ID).click()
    expect(heart(page, LOW_ID)).to_have_attribute("aria-pressed", "false")
    expect(heart(page, LOW_ID).locator(".vote-n")).to_have_text("")
    expect(heart(page, HIGH_ID)).to_have_attribute("aria-pressed", "true")
    assert_no_errors(page)


def test_medals_move_between_results_and_can_be_taken_back(site, page):
    vote_api(page, signed_in=True)
    page.goto(f"{site}classic/page.html?p=demo")
    medal(page, LOW_ID, "gold").click()
    expect(medal(page, LOW_ID, "gold")).to_have_attribute("aria-pressed", "true")
    medal(page, HIGH_ID, "gold").click()  # gold moves: a user has only one
    expect(medal(page, HIGH_ID, "gold")).to_have_attribute("aria-pressed", "true")
    expect(medal(page, LOW_ID, "gold")).to_have_attribute("aria-pressed", "false")
    expect(medal(page, LOW_ID, "gold").locator(".vote-n")).to_have_text("")
    expect(medal(page, LOW_ID, "gold")).to_have_attribute("title", "Move your gold medal here")
    expect(medal(page, HIGH_ID, "gold")).to_have_attribute("title", "Take back your gold medal")

    medal(page, HIGH_ID, "silver").click()  # a result holds one medal per user, so silver replaces its gold
    expect(medal(page, HIGH_ID, "silver")).to_have_attribute("aria-pressed", "true")
    expect(medal(page, HIGH_ID, "gold")).to_have_attribute("aria-pressed", "false")

    medal(page, HIGH_ID, "silver").click()  # click again to take it back
    expect(medal(page, HIGH_ID, "silver")).to_have_attribute("aria-pressed", "false")
    assert_no_errors(page)


def test_vote_rows_line_up_across_a_row_of_cards(site, page):
    vote_api(page)
    page.goto(f"{site}classic/page.html?p=demo")
    expect(page.locator(".votes")).to_have_count(3)
    # a long harness name or big numbers wrap one card's metrics onto a second line; the vote rows must still align
    page.evaluate("() => document.querySelectorAll('.compare-metrics')[1].append(' · ' + 'a-longer-metric '.repeat(8))")
    tops = page.eval_on_selector_all(".votes", "els => els.map((e) => Math.round(e.getBoundingClientRect().top))")
    assert len(set(tops)) == 1, tops
    assert_no_errors(page)


def test_votes_are_on_every_view_and_leave_the_owners_rank_alone(site, page):
    vote_api(page, signed_in=True)
    page.goto(f"{site}classic/compare.html?p=demo")
    expect(page.locator(".votes")).to_have_count(3)
    expect(page.locator(".auth")).to_have_count(1)
    page.goto(f"{site}run.html?p=demo&r={HIGH_ID}")
    expect(page.locator("#metric-strip .votes")).to_have_count(1)
    page.goto(f"{site}classic/page.html?p=demo&view=table")
    page.wait_for_selector("tr.run-row")
    expect(page.locator(".votes")).to_have_count(0)  # the table keeps its columns; each row's bar is in its expanded detail
    row = page.locator("tr.run-row").first
    row.locator('td[data-col="effort"]').click()
    expect(page.locator("tr.run-detail .votes")).to_have_count(1)
    page.locator("tr.run-detail .vote-heart").click()
    expect(page.locator("tr.run-detail .vote-heart")).to_have_attribute("aria-pressed", "true")
    expect(row).to_have_attribute("aria-expanded", "true")  # voting didn't collapse the row
    # the owner's ranking is a different thing and keeps its own chip
    page.goto(f"{site}classic/page.html?p=art")
    expect(page.locator(".compare-col .votes").first).to_be_visible()
    assert page.locator(".compare-col").first.locator(".rank-chip").inner_text() == "🥇"
    assert_no_errors(page)


def test_a_failed_vote_says_why_and_an_ended_session_is_noticed(site, page):
    api = vote_api(page, signed_in=True)
    page.goto(f"{site}classic/page.html?p=demo")
    api.fail = "no such run"
    heart(page, LOW_ID).click()
    expect(card(page, LOW_ID).locator(".vote-note")).to_have_text("not saved: no such run")
    expect(heart(page, LOW_ID)).to_have_attribute("aria-pressed", "false")
    api.fail, api.signed_in = None, False  # the session ended in another tab
    heart(page, MEDIUM_ID).click()
    expect(page.locator(".auth")).to_have_text("Sign in with GitHub")
    assert_no_errors(page)


def test_signing_out(site, page):
    api = vote_api(page, signed_in=True)
    page.goto(f"{site}classic/page.html?p=demo")
    expect(page.locator(".auth")).to_contain_text("@alice")
    page.locator(".auth button", has_text="Sign out").click()
    expect(page.locator(".auth")).to_have_text("Sign in with GitHub")
    assert not api.signed_in
    expect(heart(page, HIGH_ID)).to_have_attribute("aria-pressed", "false")
    assert_no_errors(page)


def test_run_title_has_no_stray_text_for_unranked_runs(site, page):
    for slug, run_id in (("demo", HIGH_ID), ("art", "model-x-low-20260102-000000")):  # no rank key / rank null
        page.goto(f"{site}run.html?p={slug}&r={run_id}")
        page.wait_for_selector("#title .effort")
        title = page.locator("#title").inner_text()
        assert "null" not in title and "undefined" not in title, title
    assert_no_errors(page)


def test_model_parts_split_off_a_pinned_openrouter_upstream(site, page):
    page.goto(f"{site}classic/index.html")
    parts = page.evaluate("""async () => {
      const { modelParts, modelLabel } = await import("./assets/runs.js");
      const label = modelLabel("openrouter/deepseek/deepseek-v4.1-flash@deepinfra/fp8");
      return { routed: modelParts("openrouter/deepseek/deepseek-v4.1-flash@deepinfra/fp8"), plain: modelParts("anthropic/claude-opus-5-5"),
               label: [...label.children].map((c) => c.className + ":" + c.textContent) };
    }""")
    assert parts["routed"] == {"provider": "openrouter/deepseek", "name": "deepseek-v4.1-flash", "via": "deepinfra/fp8",
                               "short": "deepseek-v4.1-flash via deepinfra/fp8"}
    assert parts["plain"] == {"provider": "anthropic", "name": "claude-opus-5-5", "via": "", "short": "claude-opus-5-5"}
    assert parts["label"] == ["model-name:deepseek-v4.1-flash", "model-provider:openrouter/deepseek", "model-via:via deepinfra/fp8"]


@pytest.mark.parametrize("view,selector", [
    ("index.html", ".v2-tile"),
    ("page.html?p=demo", ".v2-card"),
    (f"compare.html?p=demo&r={LOW_ID},{HIGH_ID}", ".v2-col"),
    ("classic/index.html", ".card"),
    ("classic/page.html?p=demo&view=table", "tr.run-row"),
    ("classic/compare.html?p=demo", ".compare-col"),
    (f"run.html?p=demo&r={HIGH_ID}#transcript", ".transcript .content-md"),
    (f"play.html?p=demo&r={HIGH_ID}", "iframe"),
])
def test_viewer_uses_only_local_resources(site, page, view, selector):
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    # Simulate unavailable outside network while recording any attempted request.
    page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(site) else route.abort())
    page.goto(site + view)
    page.wait_for_selector(selector)
    page.wait_for_load_state("networkidle")
    assert all(url.startswith(site) for url in requests), requests
    if not view.startswith("run.html"):
        assert not any("marked.esm.js" in url for url in requests)
    assert_no_errors(page)


@pytest.mark.parametrize("view", ["page", "run"])
def test_fullscreen_links_use_sandboxed_play(site, page, view):
    page.goto(site + (f"run.html?p=demo&r={HIGH_ID}" if view == "run" else "classic/page.html?p=demo&view=table"))
    if view == "page":
        page.locator("tr.run-row").filter(has=page.locator("td[data-col=effort]", has_text="high")).locator("td[data-col=effort]").click()
    link = page.locator(".game-links a", has_text="Open full screen")
    assert link.get_attribute("href") == f"play.html?p=demo&r={HIGH_ID}"
    assert "unsandboxed" not in link.inner_text()
    assert page.locator('a[href*="game/index.html"]').count() == 0
    with page.expect_popup() as popup:
        link.click()
    out = popup.value
    out.wait_for_selector("iframe")
    assert out.locator("iframe").get_attribute("sandbox") == "allow-scripts allow-pointer-lock"
    out.close()
    assert_no_errors(page)


def test_markdown_tokens_render_without_html_or_external_network(site, page):
    page.goto(site + "classic/index.html")
    page.wait_for_selector(".card")
    source = '''# Heading

**bold** *em* ~~gone~~ `a < b & c` &amp; &#65;

> quote

3. third
4. fourth

- [x] done
- [ ] todo

| A | B |
| :- | -: |
| one | two |

---

```python
if a < b && c > d:
    pass
```

<script>window.markdownRan = true</script>

[bad](javascript:alert%281%29) [encoded](jav&#x61;script:alert%281%29)
[data](data:text/html,evil) [safe](https://example.com) [local](page.html?p=demo)

![remote](https://example.com/tracker.png)
'''
    page.evaluate('''async source => {
      const { renderMarkdown } = await import('./assets/markdown.js');
      const container = document.createElement('div');
      container.id = 'markdown-test';
      document.body.append(container);
      renderMarkdown(container, source);
    }''', source)
    md = page.locator("#markdown-test")
    assert md.locator("h1").inner_text() == "Heading"
    assert md.locator("strong").inner_text() == "bold"
    assert md.locator("em").inner_text() == "em"
    assert md.locator("del").inner_text() == "gone"
    assert md.locator("ol").get_attribute("start") == "3"
    assert md.locator("input[checked][disabled]").count() == 1
    assert md.locator("table th").count() == 2
    assert md.locator("blockquote").inner_text() == "quote"
    assert "a < b & c" in md.inner_text() and "& A" in md.inner_text()
    assert "if a < b && c > d:" in md.locator("pre code").inner_text()
    assert "<script>" in md.inner_text()
    assert md.locator("script, img").count() == 0
    assert md.locator("a[href]").count() == 2
    assert not page.evaluate("window.markdownRan === true")
    assert_no_errors(page)


@pytest.mark.parametrize("view,selector", [
    ("page.html?p=demo", ".v2-card"),
    (f"compare.html?p=demo&r={LOW_ID},{HIGH_ID}", ".v2-col"),
    ("classic/page.html?p=demo&view=table", "tr.run-row"),
    ("classic/compare.html?p=demo", ".compare-col"),
    (f"run.html?p=demo&r={HIGH_ID}", "#title .effort"),
    (f"play.html?p=demo&r={HIGH_ID}", "iframe"),
])
def test_page_views_load_one_page_json(site, page, view, selector):
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.goto(site + view)
    page.wait_for_selector(selector)
    page.wait_for_load_state("networkidle")
    assert sum(url.endswith("/data/demo/page.json") for url in requests) == 1
    assert not any("results.json" in url or url.endswith("/run.json") for url in requests)
    assert_no_errors(page)


# ---------------------------------------------------------------- blender pages (kind "blender")
def blender_page(page):
    """Routes a one-run blender page "sculpt" (a one-triangle .glb and a PNG render) into the fixture site."""
    from test_blender import PNG_1X1, glb

    run = {"id": "model-x-low-20260103-000000", "page": "sculpt", "model": "test-org/model-x", "effort": "low",
           "kind": "blender", "started_at": "2026-01-03T00:00:00Z", "harness": {"name": "pi", "version": "0.87.1"},
           "state": "complete", "error": None, "route": None, "rank": None, "session": None, "source": None,
           "metrics": {"duration_ms": 1000, "cost_usd": 0.01, "tool_calls": 1, "turns": 1, "tokens_total": 10,
                       "tokens_input": 5, "tokens_output": 5, "tokens_reasoning": 0, "tokens_cache_read": 0},
           "thumb": "media/render.png",
           "output": {"kind": "blender", "ok": True, "verified": True, "error": None, "items": [
               {"type": "image", "path": "media/render.png", "width": 1, "height": 1, "bytes": len(PNG_1X1)},
               {"type": "model", "path": "media/scene.glb", "bytes": len(glb()), "meshes": 1, "triangles": 1, "animations": 0}]}}
    data = {"slug": "sculpt", "title": "Sculpt", "kind": "blender", "prompt": "a triangle", "final_prompt": None,
            "created": "2026-01-03T00:00:00Z", "updated": "2026-01-03T00:00:00Z", "runs": [run]}
    page.route("**/data/sculpt/page.json", lambda r: r.fulfill(json=data))
    page.route("**/media/render.png", lambda r: r.fulfill(body=PNG_1X1, content_type="image/png"))
    page.route("**/media/scene.glb", lambda r: r.fulfill(body=glb(), content_type="model/gltf-binary"))
    return run


@pytest.fixture
def gl_page(browser):
    """A page in a Chrome with software WebGL (the session browser has none in headless mode)."""
    b = browser.browser_type.launch(channel="chrome", args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader"])
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg._page_errors = []
    pg.on("pageerror", lambda e: pg._page_errors.append(str(e)))
    yield pg
    b.close()


def test_blender_card_shows_render_until_the_model_is_opened(site, gl_page):
    page = gl_page
    blender_page(page)
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page.goto(f"{site}classic/page.html?p=sculpt&view=grid")
    card = page.locator(".compare-col")
    overlay = card.locator(".media-box .model-view .play-overlay")
    expect(overlay).to_contain_text("View in 3D")
    assert "/media/render.png" in overlay.get_attribute("style")  # the render as the poster
    assert card.locator(".media-count").inner_text() == "2 files · 1 3D model"
    assert card.locator(".media-thumb.is-model").count() == 1
    assert page.locator("#play-all").is_hidden()  # Play all never opens WebGL views
    assert not any("three-gltf" in u or u.endswith(".glb") for u in requests)  # nothing loads before the click
    overlay.click()
    page.wait_for_selector(".model-stage[data-loaded='true'] canvas")
    assert page.locator(".model-view .msg").count() == 0 and page._page_errors == []


def test_blender_run_page_lists_the_model_with_its_triangles(site, gl_page):
    page = gl_page
    run = blender_page(page)
    page.goto(f"{site}run.html?p=sculpt&r={run['id']}")
    page.wait_for_selector(".media-grid.is-full .media-item.is-model")
    caption = page.locator(".media-item.is-model figcaption")
    expect(caption).to_contain_text("scene.glb · 1 triangles")
    assert caption.locator("a").get_attribute("download") == "scene.glb"
    page.locator(".media-item.is-model .play-overlay").click()
    page.wait_for_selector(".model-stage[data-loaded='true'] canvas")
    box = page.locator(".media-full.is-model").bounding_box()
    assert box["width"] > 600 and abs(box["width"] / box["height"] - 4 / 3) < 0.02
    assert page._page_errors == []


# --- local run monitor (ADR-0027) ---------------------------------------------------------------

LIVE_ID = "gpt-6-sol-low-20260101-000000"


@pytest.fixture
def monitor_setup(tmp_path):
    """The site as `art-crit serve` serves it (local API included) plus a batch with a running run: (url, batch)."""
    from art_crit.serve import serve_in_thread
    root = tmp_path / "site"
    docs = root / "docs"
    docs.mkdir(parents=True)
    for f in REPO.glob("docs/*.html"):
        shutil.copy(f, docs / f.name)
    shutil.copytree(REPO / "docs/classic", docs / "classic")
    shutil.copytree(REPO / "docs/assets", docs / "assets")
    shutil.copytree(FIXTURE_DATA, docs / "data")
    runs = root / "art-crit-runs"
    (root / "art-crit.toml").write_text(f'[run]\ndir = "{runs}"\n')
    batch = runs / "2026-01-01-000000-demo"
    (batch / LIVE_ID / "harness").mkdir(parents=True)
    line = {"type": "message", "message": {"role": "assistant", "content": [{"type": "text", "text": "looking at it"}], "usage": {"input": 100, "output": 20, "cost": {"total": 0.002}}}}
    # More turns than fit in the transcript pane, so a test can scroll it, and each with a tool call so the
    # "Tool calls" filter still shows them. No `usage`, so the live token count the other tests assert (120)
    # stays what the first line says.
    filler = [{"type": "message", "message": {"role": "assistant", "content": [
        {"type": "text", "text": f"step {i}: " + "tracing the wave and the wing shape " * 6},
        {"type": "toolCall", "id": f"call-{i}", "name": "bash", "arguments": {"command": f"echo {i}"}}]}}
        for i in range(40)]
    (batch / LIVE_ID / "harness" / "s.jsonl").write_text("\n".join(json.dumps(e) for e in [line, *filler]) + "\n")
    row = {"id": LIVE_ID, "harness": "pi", "model": "openai/gpt-6-sol", "model_arg": "gpt-6-sol", "level": "low", "state": "running"}
    meta = {"prompt": "a demo prompt", "kind": "godot", "page": "demo", "brief": "BRIEF", "runs": [row]}
    (batch / "batch.json").write_text(json.dumps(meta))
    server = serve_in_thread(docs, 0)
    yield f"http://127.0.0.1:{server.server_address[1]}/", batch
    server.shutdown()
    server.server_close()


@pytest.fixture
def monitor_site(monitor_setup):
    return monitor_setup[0]


def test_monitor_is_local_only_on_the_static_site(site, page):
    page.goto(site + "monitor.html")
    expect(page.locator("#local-only")).to_contain_text("art-crit serve")
    assert page.locator("#main").is_hidden()
    page.goto(site + "classic/index.html")
    page.wait_for_selector(".card")
    assert page.locator(".site-header .monitor-crumb").count() == 0
    assert_no_errors(page)


def test_monitor_lists_a_running_run_with_live_metrics(monitor_site, page):
    page.goto(monitor_site + "monitor.html")
    expect(page.locator("#where")).to_contain_text("1 batch")
    run = page.locator(".monitor-run")
    expect(run).to_have_count(1)
    expect(run).to_contain_text("running")
    expect(run).to_contain_text("gpt-6-sol")
    run.click()
    expect(page.locator(".monitor-stop")).to_be_visible()
    expect(page.locator(".stat-tiles")).to_contain_text("120")
    expect(page.locator(".monitor-transcript")).to_contain_text("looking at it")
    expect(page.locator("#detail h2")).to_contain_text("gpt-6-sol")
    assert_no_errors(page)


def test_monitor_poll_keeps_the_reading_position(monitor_site, page):
    """The page re-renders every 2s while a batch runs. The transcript used to jump back to the top and lose its
    filter and folded blocks on each poll (the todo's "continuous refresh reverts where I'm scrolling")."""
    page.goto(monitor_site + "monitor.html")
    page.locator(".monitor-run").click()
    expect(page.locator(".monitor-transcript")).to_contain_text("looking at it")
    page.evaluate("""() => {
      window.__renders = 0;
      new MutationObserver((ms) => { window.__renders += ms.length; })
        .observe(document.getElementById("detail"), { childList: true });
    }""")
    page.locator(".transcript-toolbar [data-filter-btn='tools']").click()
    page.evaluate("() => { document.querySelector('.monitor-block details').open = true; }")
    data = page.evaluate("""() => {
      const box = document.querySelector('.monitor-transcript');
      box.scrollTop = 250;
      window.scrollTo(0, 150);
      return { renders: window.__renders, scrollable: box.scrollHeight > box.clientHeight };
    }""")
    assert data["scrollable"], "the transcript has to overflow its pane for this test to mean anything"

    page.wait_for_function("(n) => window.__renders > n", arg=data["renders"], timeout=15000)

    after = page.evaluate("""() => ({
      scroll: document.querySelector('.monitor-transcript').scrollTop,
      y: window.scrollY,
      filter: document.querySelector('.transcript').dataset.filter,
      chip: document.querySelector(".transcript-toolbar [data-filter-btn='tools']").classList.contains('chip-active'),
      open: document.querySelector('.monitor-block details').open,
    })""")
    assert after["scroll"] == 250, after
    assert after["y"] == 150, after
    assert after["filter"] == "tools" and after["chip"], after
    assert after["open"], after
    assert_no_errors(page)


def test_monitor_transcript_keeps_its_filter_as_it_grows(monitor_setup, page):
    """A running session's transcript is rebuilt whenever it grows; the reader's filter is not part of the data."""
    url, batch = monitor_setup
    session = batch / LIVE_ID / "harness" / "s.jsonl"
    page.goto(url + "monitor.html")
    page.locator(".monitor-run").click()
    expect(page.locator(".monitor-transcript")).to_contain_text("looking at it")
    page.evaluate("""() => {
      window.__renders = 0;
      new MutationObserver((ms) => { window.__renders += ms.length; })
        .observe(document.getElementById("detail"), { childList: true });
    }""")
    page.locator(".transcript-toolbar [data-filter-btn='tools']").click()

    extra = {"type": "message", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "a later step"}, {"type": "toolCall", "id": "call-late", "name": "bash", "arguments": {"command": "ls"}}]}}
    with session.open("a") as f:
        f.write(json.dumps(extra) + "\n")

    expect(page.locator(".monitor-transcript")).to_contain_text("a later step", timeout=15000)
    after = page.evaluate("""() => ({
      filter: document.querySelector('.transcript').dataset.filter,
      chip: document.querySelector(".transcript-toolbar [data-filter-btn='tools']").classList.contains('chip-active'),
    })""")
    assert after == {"filter": "tools", "chip": True}, after
    assert_no_errors(page)


def test_monitor_link_appears_on_the_local_home_page(monitor_site, page):
    page.goto(monitor_site + "classic/index.html")
    page.wait_for_selector(".card")
    expect(page.locator(".site-header .monitor-crumb", has_text="Video studio (local)")).to_have_attribute("href", "studio.html")
    link = page.locator(".site-header .monitor-crumb", has_text="Runs (local)")
    link.click()
    page.wait_for_selector(".monitor-run")
    assert_no_errors(page)


def test_run_sidebar_lists_allowed_and_used_tools(site, page):
    tools = {"allowed": {"builtin": ["bash", "read"], "mcp": {"blender": {"allowed": ["render", "exec"], "hidden": ["screenshot"]}}},
             "used": {"bash": 3, "mcp__blender__render": 2}}

    def with_tools(route):
        response = route.fetch()
        body = response.json()
        for r in body["runs"]:
            r["tools"] = tools
        route.fulfill(json=body)

    page.route("**/data/demo/page.json*", with_tools)
    page.goto(f"{site}run.html?p=demo&r={LOW_ID}")
    box = page.locator(".run-tools")
    box.wait_for()
    assert box.locator(".tool-chip.is-used").all_inner_texts() == ["bash3", "render2"]
    assert box.locator(".tool-chip.is-hidden").all_inner_texts() == ["screenshot"]
    assert "MCP · blender" in box.inner_text() and "read" in box.inner_text()
    assert_no_errors(page)


# ---------------------------------------------------------------- the lanes design (index/page/compare, ADR-0030)
def test_lanes_home_lists_prompts_with_covers_and_kind_filters(site, page):
    page.goto(site + "index.html")
    tiles = page.locator(".v2-tile")
    expect(tiles).to_have_count(2)
    expect(page.locator(".v2-feature h2")).to_have_text("Art")
    # a cover comes from the page's highest-effort run that made its output
    assert ART_HIGH_ID in page.locator(".v2-feature-media img").first.get_attribute("src")
    expect(page.locator(".v2-feature-prompt")).to_contain_text("draw a red circle")
    pills = page.locator(".v2-section-head .v2-pill")
    expect(pills).to_have_text([re.compile(r"All\s*2"), re.compile(r"Vector\s*1"), re.compile(r"Game\s*1")])
    pills.nth(2).click()
    expect(tiles).to_have_count(1)
    expect(tiles.first).to_have_attribute("href", "page.html?p=demo")
    expect(page.locator(".site-header .v2-classic")).to_have_attribute("href", "classic/index.html")
    assert_no_errors(page)


def test_lanes_request_opens_githubs_prefilled_form_without_the_api(site, page):
    page.goto(site + "index.html")
    page.evaluate("() => { window.open = (url) => { window.__opened = url; return null; }; }")
    page.locator("#request-open").click()
    dialog = page.locator(".request-dialog")
    dialog.locator("textarea[name=prompt]").fill("Draw a pelican riding a bicycle @someone")
    dialog.locator("label.kind-option", has_text="Game").click()
    dialog.get_by_role("button", name="Open the request").click()
    expect(dialog).to_contain_text("GitHub's new-issue form opened")
    url = page.evaluate("() => window.__opened")
    assert url.startswith("https://github.com/tokenosopher/mtwabp-bench/issues/new?")
    from urllib.parse import parse_qs, urlparse
    q = parse_qs(urlparse(url).query)
    assert q["title"] == ["Prompt request: Draw a pelican riding a bicycle @someone"]
    assert q["labels"] == ["prompt request"]
    assert "```text\nDraw a pelican riding a bicycle @someone\n```" in q["body"][0]
    assert "(`--kind godot`)" in q["body"][0]
    assert_no_errors(page)


def test_lanes_request_through_the_api_links_the_new_issue(site, page):
    sent = []
    def fulfill(route):
        sent.append(route.request.post_data_json)
        route.fulfill(status=201, content_type="application/json",
                      body=json.dumps({"number": 7, "url": "https://github.com/tokenosopher/mtwabp-bench/issues/7"}))
    page.route("**/api/request", fulfill)
    page.goto(site + "index.html")
    page.locator("#request-open").click()
    dialog = page.locator(".request-dialog")
    dialog.locator("textarea[name=prompt]").fill("A voxel lighthouse at dusk")
    dialog.locator("textarea[name=note]").fill("watch the beam")
    dialog.get_by_role("button", name="Open the request").click()
    expect(dialog.locator("a")).to_have_attribute("href", "https://github.com/tokenosopher/mtwabp-bench/issues/7")
    assert sent == [{"prompt": "A voxel lighthouse at dusk", "kind": "media", "note": "watch the beam"}]
    assert_no_errors(page)


def test_lanes_page_has_a_lane_per_model_sorting_and_a_compare_tray(site, page):
    page.goto(site + "page.html?p=demo")
    expect(page.locator(".v2-lane")).to_have_count(1)
    cards = page.locator(".v2-card")
    expect(cards).to_have_count(3)
    expect(cards.locator(".v2-card-head .effort")).to_have_text(["low", "medium", "high"])
    page.locator(".v2-sort").click()
    expect(cards.locator(".v2-card-head .effort")).to_have_text(["high", "medium", "low"])
    assert "sort=effort-desc" in page.url
    expect(cards.first.locator(".votes-label")).to_have_text("Your vote:")  # inactive here: no vote API

    tray = page.locator(".v2-tray")
    assert tray.is_hidden()
    page.locator(f'.v2-card input[data-id="{HIGH_ID}"]').check()
    expect(tray).to_contain_text("pick at least one more")
    page.locator(f'.v2-card input[data-id="{LOW_ID}"]').check()
    expect(tray.locator(".v2-tray-item")).to_have_count(2)
    go = tray.locator(".v2-tray-go")
    expect(go).to_have_attribute("href", f"compare.html?p=demo&r={HIGH_ID},{LOW_ID}")
    with page.expect_navigation():
        go.click()
    expect(page.locator(".v2-col")).to_have_count(2)
    assert_no_errors(page)


def test_lanes_card_media_opens_the_run(site, page):
    page.goto(site + "page.html?p=art")
    media = page.locator(f'.v2-card:has(input[data-id="{ART_HIGH_ID}"]) .v2-media')
    expect(media.locator("video[controls]")).to_have_count(0)  # card videos show their poster, a click opens the run
    box = media.bounding_box()
    with page.expect_navigation():
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 3)
    assert page.url.endswith(f"run.html?p=art&r={ART_HIGH_ID}")


def test_lanes_compare_needs_two_runs_and_marks_the_best(site, page):
    page.goto(f"{site}compare.html?p=demo&r={HIGH_ID}")
    expect(page.locator("h1")).to_have_text("Pick at least two runs to compare")
    page.goto(f"{site}compare.html?p=demo&r={MEDIUM_ID},{HIGH_ID}")
    cols = page.locator(".v2-col")
    expect(cols).to_have_count(2)
    expect(cols.first.locator(".v2-metric")).to_have_count(3)
    expect(page.locator(".v2-back-btn")).to_have_attribute("href", "page.html?p=demo")
    expect(page.locator(".site-header .v2-classic")).to_have_attribute("href", f"classic/compare.html?p=demo&r={MEDIUM_ID},{HIGH_ID}")
    assert_no_errors(page)
