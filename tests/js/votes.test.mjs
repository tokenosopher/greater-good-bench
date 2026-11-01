// The votes API (cloudflare/votes.mjs) behind the router, against a real SQLite and a faked GitHub + Pages.
import assert from "node:assert/strict";
import { test } from "node:test";
import router from "../../cloudflare/router.mjs";
import { memoryD1 } from "./d1.mjs";

const ORIGIN = "https://fenderog.com";
const RUNS = ["run-a", "run-b", "run-c"];
const USERS = { alice: { id: 101, login: "alice" }, bob: { id: 202, login: "bob" }, carol: { id: 303, login: "carol" } };
// The vars of cloudflare/wrangler.jsonc, here for a site on a path (SITE_PREFIX "/art-crit"); the end of the file
// covers a site on a host of its own (SITE_PREFIX "").
const VARS = { SITE_PREFIX: "/art-crit", PAGES_URL: "https://art-crit.pages.dev", GITHUB_REPO: "tokenosopher/greater-good-bench" };
const env = () => ({ ...VARS, DB: memoryD1(), GITHUB_CLIENT_ID: "client-id", GITHUB_CLIENT_SECRET: "client-secret", SESSION_SECRET: "test-secret" });

const issues = []; // every issue the Worker asked GitHub to open
globalThis.fetch = async (url, options = {}) => {
  url = String(url);
  if (url === "https://art-crit.pages.dev/data/demo/page.json") return Response.json({ runs: RUNS.map((id) => ({ id })) });
  // Without docs/404.html, Pages answers a missing file with index.html and 200.
  if (url === "https://art-crit.pages.dev/data/spa/page.json") return new Response("<!doctype html>", { headers: { "Content-Type": "text/html; charset=utf-8" } });
  if (url.startsWith("https://art-crit.pages.dev/data/")) return new Response("missing", { status: 404 });
  if (url === "https://github.com/login/oauth/access_token") {
    const body = JSON.parse(options.body);
    assert.equal(body.client_secret, "client-secret");
    return Response.json(body.code.startsWith("code-") ? { access_token: `token-${body.code.slice(5)}` } : { error: "bad_verification_code" });
  }
  if (url === "https://api.github.com/user") return Response.json(USERS[options.headers.Authorization.slice("Bearer token-".length)]);
  if (url === "https://api.github.com/repos/tokenosopher/greater-good-bench/issues") {
    assert.equal(options.method, "POST");
    assert.equal(options.headers.Authorization, "Bearer bot-token");
    const issue = JSON.parse(options.body);
    issues.push(issue);
    if (issue.title.includes("make github fail")) return new Response("nope", { status: 500 });
    return Response.json({ number: issues.length, html_url: `https://github.com/tokenosopher/greater-good-bench/issues/${issues.length}` }, { status: 201 });
  }
  throw new Error(`unexpected fetch ${url}`);
};

const call = (e, path, { method = "GET", cookie, body, origin = ORIGIN, type = "application/json" } = {}) =>
  router.fetch(new Request(ORIGIN + "/art-crit/api" + path, {
    method,
    headers: { ...(cookie && { Cookie: cookie }), ...(origin && { Origin: origin }), ...(body && { "Content-Type": type }) },
    body: body && JSON.stringify(body),
  }), e);

const cookieFrom = (response, name) => response.headers.getSetCookie().find((c) => c.startsWith(`${name}=`));
const pair = (setCookie) => setCookie.split(";")[0];

// Signs in through the real login + callback pair and returns the session cookie.
async function signIn(e, who, ret = "/art-crit/page.html?p=demo") {
  const start = await call(e, `/login?return=${encodeURIComponent(ret)}`);
  const state = new URL(start.headers.get("location")).searchParams.get("state");
  const done = await call(e, `/callback?code=code-${who}&state=${state}`, { cookie: pair(cookieFrom(start, "__Secure-ac_oauth")) });
  assert.equal(done.status, 302);
  assert.equal(done.headers.get("location"), ret);
  return pair(cookieFrom(done, "__Secure-ac_session"));
}

const heart = (e, cookie, run, on) => call(e, "/heart", { method: "PUT", cookie, body: { p: "demo", run, on } });
const medal = (e, cookie, name, run) => call(e, "/medal", { method: "PUT", cookie, body: { p: "demo", medal: name, run } });

test("login sends visitors to GitHub with no scopes and a state they must bring back", async () => {
  const e = env();
  const res = await call(e, "/login?return=/art-crit/compare.html?p=demo");
  assert.equal(res.status, 302);
  const to = new URL(res.headers.get("location"));
  assert.equal(to.origin + to.pathname, "https://github.com/login/oauth/authorize");
  assert.equal(to.searchParams.get("client_id"), "client-id");
  assert.equal(to.searchParams.get("redirect_uri"), `${ORIGIN}/art-crit/api/callback`);
  assert.equal(to.searchParams.get("scope"), null);
  const cookie = cookieFrom(res, "__Secure-ac_oauth");
  assert.match(cookie, /HttpOnly; Secure; SameSite=Lax/);
  assert.match(cookie, /Path=\/art-crit\/api\//);
});

test("login only returns to pages of this site", async () => {
  const e = env();
  for (const evil of ["https://evil.example/art-crit/", "//evil.example/art-crit/", "/\\evil.example", "/other/", "/art-crit/api/votes"]) {
    const start = await call(e, `/login?return=${encodeURIComponent(evil)}`);
    const state = new URL(start.headers.get("location")).searchParams.get("state");
    const done = await call(e, `/callback?code=code-alice&state=${state}`, { cookie: pair(cookieFrom(start, "__Secure-ac_oauth")) });
    assert.equal(done.headers.get("location"), "/art-crit/", evil);
  }
});

test("callback rejects a missing, foreign or tampered state; a declined sign-in sets no session", async () => {
  const e = env();
  const start = await call(e, "/login");
  const oauth = pair(cookieFrom(start, "__Secure-ac_oauth"));
  const state = new URL(start.headers.get("location")).searchParams.get("state");
  assert.equal((await call(e, `/callback?code=code-alice&state=${state}`)).status, 400); // no cookie
  assert.equal((await call(e, `/callback?code=code-alice&state=other`, { cookie: oauth })).status, 400);
  const tampered = oauth.slice(0, -2) + (oauth.endsWith("AA") ? "BB" : "AA");
  assert.equal((await call(e, `/callback?code=code-alice&state=${state}`, { cookie: tampered })).status, 400);
  assert.equal((await call(e, `/callback?code=nope&state=${state}`, { cookie: oauth })).status, 502); // GitHub refuses the code
  const declined = await call(e, `/callback?error=access_denied&state=${state}`, { cookie: oauth });
  assert.equal(declined.status, 302);
  assert.equal(cookieFrom(declined, "__Secure-ac_session"), undefined);
});

test("votes are public to read and zeroed for every run of the page", async () => {
  const e = env();
  const res = await call(e, "/votes?p=demo");
  assert.equal(res.status, 200);
  assert.equal(res.headers.get("cache-control"), "no-store");
  const body = await res.json();
  assert.equal(body.user, null);
  assert.equal(body.mine, null);
  assert.deepEqual(Object.keys(body.totals), RUNS);
  assert.deepEqual(body.totals["run-a"], { hearts: 0, gold: 0, silver: 0, bronze: 0 });
  assert.equal((await call(e, "/votes?p=missing")).status, 404);
  assert.equal((await call(e, "/votes?p=spa")).status, 404); // a 200 that isn't JSON is a missing page too, not a 500
  assert.equal((await call(e, "/votes?p=Bad_Slug")).status, 400);
  assert.equal((await call(e, "/votes")).status, 400);
});

test("hearts: one per user per run, any number of runs, undone by turning off", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  const bob = await signIn(e, "bob");
  await heart(e, alice, "run-a", true);
  await heart(e, alice, "run-a", true); // twice is still one
  await heart(e, alice, "run-b", true);
  let res = await (await heart(e, bob, "run-a", true)).json();
  assert.equal(res.totals["run-a"].hearts, 2);
  assert.equal(res.totals["run-b"].hearts, 1);
  assert.deepEqual(res.mine.hearts, ["run-a"]);
  assert.equal(res.user.login, "bob");
  res = await (await heart(e, alice, "run-a", false)).json();
  assert.equal(res.totals["run-a"].hearts, 1);
  assert.deepEqual(res.mine.hearts, ["run-b"]);
  const anonymous = await (await call(e, "/votes?p=demo")).json(); // anyone sees the totals, but not whose
  assert.equal(anonymous.totals["run-b"].hearts, 1);
  assert.equal(anonymous.mine, null);
});

test("medals: one gold, one silver, one bronze per user, each on a different run", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  const bob = await signIn(e, "bob");
  await medal(e, alice, "gold", "run-a");
  await medal(e, alice, "silver", "run-b");
  let res = await (await medal(e, alice, "bronze", "run-c")).json();
  assert.deepEqual([res.mine.gold, res.mine.silver, res.mine.bronze], ["run-a", "run-b", "run-c"]);

  res = await (await medal(e, alice, "gold", "run-b")).json(); // moving gold onto run-b displaces run-b's silver too
  assert.deepEqual([res.mine.gold, res.mine.silver, res.mine.bronze], ["run-b", null, "run-c"]);
  assert.deepEqual(res.totals["run-a"], { hearts: 0, gold: 0, silver: 0, bronze: 0 });
  assert.deepEqual(res.totals["run-b"], { hearts: 0, gold: 1, silver: 0, bronze: 0 });

  await medal(e, bob, "gold", "run-b"); // another user's medals are independent and add up
  res = await (await medal(e, alice, "gold", null)).json(); // and a medal can be taken back
  assert.equal(res.mine.gold, null);
  assert.equal(res.totals["run-b"].gold, 1);
  assert.equal(res.totals["run-c"].bronze, 1);
});

test("the totals stay equal to the votes themselves through hearts, medal moves and take-backs", async () => {
  const e = env();
  const people = [await signIn(e, "alice"), await signIn(e, "bob"), await signIn(e, "carol")];
  let seed = 7; // a fixed pseudo-random run of 300 actions (mulberry32), so a failure reproduces
  const pick = (n) => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return Math.floor((((t ^ (t >>> 14)) >>> 0) / 4294967296) * n);
  };
  for (let i = 0; i < 300; i++) {
    const cookie = people[pick(3)];
    const run = RUNS[pick(3)];
    if (pick(2)) await heart(e, cookie, run, pick(2) === 1);
    else await medal(e, cookie, ["gold", "silver", "bronze"][pick(3)], pick(4) === 0 ? null : run);
  }
  const counted = Object.fromEntries(RUNS.map((id) => [id, { hearts: 0, gold: 0, silver: 0, bronze: 0 }]));
  for (const { run } of e.DB.sql("SELECT run FROM hearts WHERE page = 'demo'")) counted[run].hearts++;
  for (const { run, medal } of e.DB.sql("SELECT run, medal FROM medals WHERE page = 'demo'")) counted[run][medal]++;
  const shown = (await (await call(e, "/votes?p=demo")).json()).totals;
  assert.deepEqual(shown, counted);
  assert.ok(Object.values(counted).some((t) => t.hearts > 0) && Object.values(counted).some((t) => t.gold + t.silver + t.bronze > 0));
  assert.ok(Object.values(shown).every((t) => Object.values(t).every((n) => n >= 0)));
});

test("re-applying the schema recounts the tallies, e.g. for votes cast before they existed", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  await heart(e, alice, "run-a", true);
  await medal(e, alice, "gold", "run-b");
  e.DB.run("DELETE FROM tallies"); // as if the votes predate the tallies table
  assert.equal((await (await call(e, "/votes?p=demo")).json()).totals["run-a"].hearts, 0);
  e.DB.reapplySchema();
  const totals = (await (await call(e, "/votes?p=demo")).json()).totals;
  assert.equal(totals["run-a"].hearts, 1);
  assert.equal(totals["run-b"].gold, 1);
  e.DB.run("UPDATE tallies SET hearts = 99, gold = 99"); // a drifted tally is repaired the same way
  e.DB.reapplySchema();
  assert.deepEqual((await (await call(e, "/votes?p=demo")).json()).totals["run-a"], { hearts: 1, gold: 0, silver: 0, bronze: 0 });
});

test("showing a page reads one tally per run plus the viewer's own votes, never the page's voters", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  await heart(e, alice, "run-a", true);
  for (const cookie of [undefined, alice]) {
    e.DB.seen.length = 0;
    assert.equal((await call(e, "/votes?p=demo", { cookie })).status, 200);
    const reads = e.DB.seen.filter((s) => /^\s*select/i.test(s.sql));
    assert.equal(reads.length, cookie ? 3 : 1);
    for (const { sql, args } of reads) {
      const plan = e.DB.plan(sql, ...args).join(" | ");
      // A SEARCH on `page` alone still walks every vote on the page, so it must be the tallies (one row per run) or
      // a lookup that is keyed by the user as well.
      if (/FROM tallies/i.test(sql)) assert.match(plan, /SEARCH tallies USING .*\(page=\?\)/, `${sql}: ${plan}`);
      else assert.match(plan, /SEARCH \w+ USING .*\(page=\? AND user_id=\?\)/, `${sql}: ${plan}`);
      assert.doesNotMatch(plan, /SCAN/, `${sql}: ${plan}`);
    }
  }
});

test("writes need a session, the site's own origin, JSON, and a real page and run", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  assert.equal((await heart(e, undefined, "run-a", true)).status, 401);
  assert.equal((await medal(e, undefined, "gold", "run-a")).status, 401);
  const put = (extra) => call(e, "/heart", { method: "PUT", cookie: alice, body: { p: "demo", run: "run-a", on: true }, ...extra });
  assert.equal((await put({ origin: "https://evil.example" })).status, 403);
  assert.equal((await put({ origin: "null" })).status, 403); // a sandboxed game frame
  assert.equal((await put({ origin: null })).status, 403);
  assert.equal((await put({ type: "text/plain" })).status, 415);
  assert.equal((await call(e, "/heart", { method: "PUT", cookie: alice, body: { p: "demo", run: "nope", on: true } })).status, 400);
  assert.equal((await call(e, "/heart", { method: "PUT", cookie: alice, body: { p: "demo", run: "run-a", on: "yes" } })).status, 400);
  assert.equal((await call(e, "/heart", { method: "PUT", cookie: alice, body: { p: "ghost", run: "run-a", on: true } })).status, 404);
  assert.equal((await call(e, "/medal", { method: "PUT", cookie: alice, body: { p: "demo", medal: "platinum", run: "run-a" } })).status, 400);
  assert.equal((await call(e, "/medal", { method: "PUT", cookie: alice, body: { p: "demo", medal: "gold" } })).status, 400); // undefined run isn't null
  assert.equal((await call(e, "/heart", { method: "PUT", cookie: alice, body: { p: "demo", run: "run-a", on: true, pad: "x".repeat(3000) } })).status, 413);
  assert.equal((await call(e, "/heart", { method: "POST", cookie: alice })).status, 405);
  assert.equal((await put({})).status, 200);
});

test("a malformed page, or a failing database, is a clean JSON error", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  const put = (body) => call(e, "/heart", { method: "PUT", cookie: alice, body });
  assert.equal((await put({ p: ["demo"], run: "run-a", on: true })).status, 400); // coerces to "demo" in a regex test
  assert.equal((await put({ p: { toString: "demo" }, run: "run-a", on: true })).status, 400);
  assert.equal((await put({ run: "run-a", on: true })).status, 400);
  const empty = await router.fetch(new Request(ORIGIN + "/art-crit/api/heart", { method: "PUT", headers: { Cookie: alice, Origin: ORIGIN, "Content-Type": "application/json" } }), e);
  assert.equal(empty.status, 400); // an empty body isn't JSON

  const broken = { ...e, DB: { prepare: e.DB.prepare, batch: async () => { throw new Error("D1 exploded: secret detail"); } } };
  const log = console.error;
  console.error = () => {};
  try {
    const res = await call(broken, "/votes?p=demo");
    assert.equal(res.status, 500);
    assert.deepEqual(await res.json(), { error: "internal error" });
  } finally {
    console.error = log;
  }
});

test("only an intact, unexpired session cookie counts, and a login-state cookie is not one", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  assert.equal((await (await call(e, "/votes?p=demo", { cookie: alice })).json()).user.login, "alice");
  const forged = alice.slice(0, -3) + "AAA";
  assert.equal((await heart(e, forged, "run-a", true)).status, 401);
  const start = await call(e, "/login");
  const wrongKind = pair(cookieFrom(start, "__Secure-ac_oauth")).replace("__Secure-ac_oauth", "__Secure-ac_session");
  assert.equal((await heart(e, wrongKind, "run-a", true)).status, 401);
  const realNow = Date.now;
  Date.now = () => realNow() + 31 * 24 * 3600 * 1000;
  try {
    assert.equal((await heart(e, alice, "run-a", true)).status, 401);
  } finally {
    Date.now = realNow;
  }
});

test("logout clears the session and needs the same origin", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  assert.equal((await call(e, "/logout", { method: "POST", cookie: alice, origin: "https://evil.example" })).status, 403);
  const res = await call(e, "/logout", { method: "POST", cookie: alice });
  assert.equal(res.status, 200);
  assert.match(cookieFrom(res, "__Secure-ac_session"), /Max-Age=0/);
});

test("voting is off until it is configured, and unknown routes are 404", async () => {
  assert.equal((await call({ ...VARS }, "/votes?p=demo")).status, 503); // the vars alone: no database or secrets yet
  assert.equal((await call(env(), "/constructor")).status, 404);
  assert.equal((await call(env(), "/rank", { method: "PUT", body: {} })).status, 404);
});

// ---- prompt requests (adr/0030)
const withBot = () => ({ ...env(), GITHUB_ISSUES_TOKEN: "bot-token" });
const request = (e, cookie, body, opts = {}) => call(e, "/request", { method: "POST", cookie, body, ...opts });
const PROMPT = "Draw a pelican riding a bicycle, as an SVG";

test("a signed-in visitor's prompt request becomes a labeled issue, opened with the bot token", async () => {
  const e = withBot();
  const alice = await signIn(e, "alice");
  const before = issues.length;
  const res = await request(e, alice, { prompt: `  ${PROMPT}\nwith a @someone mention and \`\`\` fences  `, kind: "media", note: "watch the wheels" });
  assert.equal(res.status, 201);
  const { number, url } = await res.json();
  assert.equal(url, `https://github.com/tokenosopher/greater-good-bench/issues/${number}`);
  assert.equal(issues.length, before + 1);
  const issue = issues.at(-1);
  assert.equal(issue.title, `Prompt request: ${PROMPT}`);
  assert.deepEqual(issue.labels, ["prompt request"]);
  assert.match(issue.body, /\*\*Kind:\*\* Vector \(`--kind media`\)/);
  assert.match(issue.body, /`alice`/);
  // the prompt and note are fenced (longer than any backtick run inside), so GitHub shows them verbatim
  assert.match(issue.body, /````text\nDraw a pelican[\s\S]*fences\n````/);
  assert.match(issue.body, /```text\nwatch the wheels\n```/);
  assert.deepEqual(e.DB.sql("SELECT user_id, issue FROM prompt_requests").map((r) => ({ ...r })), [{ user_id: 101, issue: number }]);
});

test("prompt requests need a session, the site's origin, a real kind and a sensible prompt", async () => {
  const e = withBot();
  const alice = await signIn(e, "alice");
  const before = issues.length;
  assert.equal((await request(e, null, { prompt: PROMPT, kind: "media" })).status, 401);
  assert.equal((await request(e, alice, { prompt: PROMPT, kind: "media" }, { origin: "https://evil.example" })).status, 403);
  assert.equal((await request(e, alice, { prompt: PROMPT, kind: "media" }, { origin: null })).status, 403);
  assert.equal((await request(e, alice, { prompt: PROMPT, kind: "pdf" })).status, 400);
  assert.equal((await request(e, alice, { prompt: PROMPT, kind: "constructor" })).status, 400);
  assert.equal((await request(e, alice, { prompt: "too short", kind: "media" })).status, 400);
  assert.equal((await request(e, alice, { prompt: "x".repeat(4001), kind: "media" })).status, 400);
  assert.equal((await request(e, alice, { prompt: PROMPT, kind: "media", note: "n".repeat(1001) })).status, 400);
  assert.equal((await call(e, "/request", { method: "GET", cookie: alice })).status, 405);
  assert.equal(issues.length, before);
});

test("prompt requests are capped per user and per day, and GitHub trouble is a clean error", async () => {
  const e = withBot();
  const alice = await signIn(e, "alice");
  for (let i = 0; i < 5; i++) assert.equal((await request(e, alice, { prompt: `${PROMPT} #${i}`, kind: "godot" })).status, 201);
  const sixth = await request(e, alice, { prompt: PROMPT, kind: "godot" });
  assert.equal(sixth.status, 429);
  const bob = await signIn(e, "bob");
  assert.equal((await request(e, bob, { prompt: PROMPT, kind: "text" })).status, 201); // the cap is per user (and text is a kind)
  e.DB.run("UPDATE prompt_requests SET at = at - 25 * 3600"); // a day later
  assert.equal((await request(e, alice, { prompt: PROMPT, kind: "blender" })).status, 201);
  // the site-wide cap
  for (let i = 0; i < 50; i++) e.DB.run(`INSERT INTO prompt_requests (user_id, at, issue) VALUES (${900 + i}, ${Math.floor(Date.now() / 1000)}, 0)`);
  assert.equal((await request(e, bob, { prompt: PROMPT, kind: "web" })).status, 429);

  const f = withBot();
  const carol = await signIn(f, "carol");
  const failed = await request(f, carol, { prompt: "please make github fail for this one", kind: "media" });
  assert.equal(failed.status, 502);
  assert.match((await failed.json()).error, /GitHub/);
  assert.deepEqual(f.DB.sql("SELECT * FROM prompt_requests"), []); // nothing counted when no issue was made
});

test("prompt requests are off until the bot token is configured", async () => {
  const e = env();
  const alice = await signIn(e, "alice");
  const res = await request(e, alice, { prompt: PROMPT, kind: "media" });
  assert.equal(res.status, 503);
});

test("prompt requests are off without GITHUB_REPO", async () => {
  const e = { ...withBot(), GITHUB_REPO: "" };
  const alice = await signIn(e, "alice");
  assert.equal((await request(e, alice, { prompt: PROMPT, kind: "media" })).status, 503);
});

// ---- a site on a host of its own: SITE_PREFIX "" serves the API at /api/ and the site at /
test("with an empty SITE_PREFIX the API, its cookies, the callback and the return path live at the host's root", async () => {
  const HOST = "https://bench.example.com";
  const e = { ...withBot(), SITE_PREFIX: "" };
  const at = (path, { method = "GET", cookie, body, origin = HOST } = {}) => router.fetch(new Request(HOST + path, {
    method,
    headers: { ...(cookie && { Cookie: cookie }), ...(origin && { Origin: origin }), ...(body && { "Content-Type": "application/json" }) },
    body: body && JSON.stringify(body),
  }), e);
  const start = await at("/api/login?return=/compare.html?p=demo");
  const to = new URL(start.headers.get("location"));
  assert.equal(to.searchParams.get("redirect_uri"), `${HOST}/api/callback`);
  const oauth = cookieFrom(start, "__Secure-ac_oauth");
  assert.match(oauth, /Path=\/api\/;/);
  const done = await at(`/api/callback?code=code-alice&state=${to.searchParams.get("state")}`, { cookie: pair(oauth) });
  assert.equal(done.headers.get("location"), "/compare.html?p=demo");
  const alice = pair(cookieFrom(done, "__Secure-ac_session"));
  for (const evil of ["https://evil.example/", "//evil.example/", "/api/votes"]) {
    const s = await at(`/api/login?return=${encodeURIComponent(evil)}`);
    const back = await at(`/api/callback?state=${new URL(s.headers.get("location")).searchParams.get("state")}`, { cookie: pair(cookieFrom(s, "__Secure-ac_oauth")) });
    assert.equal(back.headers.get("location"), "/", evil);
  }
  assert.equal((await at("/api/heart", { method: "PUT", cookie: alice, body: { p: "demo", run: "run-a", on: true } })).status, 200);
  assert.equal((await at("/api/heart", { method: "PUT", cookie: alice, body: { p: "demo", run: "run-a", on: true }, origin: "https://evil.example" })).status, 403);
  const votes = await (await at("/api/votes?p=demo", { cookie: alice })).json();
  assert.equal(votes.totals["run-a"].hearts, 1);
  assert.equal((await at("/api/request", { method: "POST", cookie: alice, body: { prompt: PROMPT, kind: "web" } })).status, 201);
});
