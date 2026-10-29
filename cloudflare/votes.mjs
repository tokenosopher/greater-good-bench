// /art-crit/api/*: GitHub sign-in plus hearts and gold/silver/bronze medals, stored in D1 (adr/0022), and prompt
// requests, which become GitHub issues opened by the site's bot token (adr/0030). The only part of the site that writes. Reads are public; writes need a session cookie *and* a same-origin
// request, so a page on another origin (or a sandboxed game frame, whose Origin is "null") can't vote.

const SITE = "/art-crit/";
const API = `${SITE}api/`;
const SESSION = "__Secure-ac_session";
const OAUTH = "__Secure-ac_oauth";
const SESSION_SECONDS = 30 * 24 * 3600;
const OAUTH_SECONDS = 600;
const SLUG = /^[a-z0-9][a-z0-9-]*$/;
const MEDALS = ["gold", "silver", "bronze"];
const MAX_BODY = 2048;

const encoder = new TextEncoder();
const now = () => Math.floor(Date.now() / 1000);

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

// ---- signed cookies (HMAC-SHA-256 over a JSON payload; `t` keeps a login-state cookie from being a session)
const b64 = (bytes) => btoa(String.fromCharCode(...new Uint8Array(bytes))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64 = (text) => Uint8Array.from(atob(text.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
const hmacKey = (secret, usage) => crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, [usage]);

async function seal(secret, type, payload, seconds) {
  const body = b64(encoder.encode(JSON.stringify({ ...payload, t: type, exp: now() + seconds })));
  return `${body}.${b64(await crypto.subtle.sign("HMAC", await hmacKey(secret, "sign"), encoder.encode(body)))}`;
}

async function unseal(secret, type, token) {
  const [body, signature] = String(token ?? "").split(".");
  if (!body || !signature) return null;
  try {
    if (!(await crypto.subtle.verify("HMAC", await hmacKey(secret, "verify"), unb64(signature), encoder.encode(body)))) return null;
    const payload = JSON.parse(new TextDecoder().decode(unb64(body)));
    return payload.t === type && payload.exp > now() ? payload : null;
  } catch {
    return null; // malformed base64/JSON
  }
}

function cookieValue(request, name) {
  for (const part of (request.headers.get("Cookie") ?? "").split(";")) {
    const [key, ...value] = part.trim().split("=");
    if (key === name) return value.join("=");
  }
  return null;
}

const setCookie = (name, value, seconds) => `${name}=${value}; Path=${API}; Max-Age=${seconds}; HttpOnly; Secure; SameSite=Lax`;

// ---- responses
const json = (body, status = 200, headers = []) =>
  new Response(JSON.stringify(body), { status, headers: [["Content-Type", "application/json"], ["Cache-Control", "no-store"], ...headers] });

const redirect = (location, cookies) =>
  new Response(null, { status: 302, headers: [["Location", location], ["Cache-Control", "no-store"], ...cookies.map((c) => ["Set-Cookie", c])] });

// Where to send the visitor after sign-in: a page of this site, never anywhere else.
function returnPath(origin, value) {
  try {
    const url = new URL(value ?? "", origin);
    if (url.origin === origin && url.pathname.startsWith(SITE) && !url.pathname.startsWith(API)) return url.pathname + url.search + url.hash;
  } catch {}
  return SITE;
}

// ---- sign in with GitHub (OAuth web flow, no scopes: only the public profile is readable)
// The random `state` travels to GitHub and back, and also sits in a signed cookie with the page to return to,
// so the callback only accepts a sign-in this browser started.
async function startLogin(url, env) {
  const state = b64(crypto.getRandomValues(new Uint8Array(16)));
  const ret = returnPath(url.origin, url.searchParams.get("return"));
  const cookie = setCookie(OAUTH, await seal(env.SESSION_SECRET, "oauth", { state, ret }, OAUTH_SECONDS), OAUTH_SECONDS);
  const authorize = new URL("https://github.com/login/oauth/authorize");
  authorize.search = new URLSearchParams({ client_id: env.GITHUB_CLIENT_ID, redirect_uri: `${url.origin}${API}callback`, state }).toString();
  return redirect(authorize.toString(), [cookie]);
}

async function finishLogin(request, url, env) {
  const saved = await unseal(env.SESSION_SECRET, "oauth", cookieValue(request, OAUTH));
  const clear = setCookie(OAUTH, "", 0);
  if (!saved || saved.state !== url.searchParams.get("state")) {
    return new Response("Sign-in expired. Go back and try again.", { status: 400, headers: [["Set-Cookie", clear]] });
  }
  const code = url.searchParams.get("code");
  if (!code) return redirect(saved.ret, [clear]); // the visitor declined on GitHub

  const token = await (await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ client_id: env.GITHUB_CLIENT_ID, client_secret: env.GITHUB_CLIENT_SECRET, code, redirect_uri: `${url.origin}${API}callback` }),
  })).json().catch(() => ({}));
  if (!token.access_token) return new Response("GitHub did not accept the sign-in. Go back and try again.", { status: 502, headers: [["Set-Cookie", clear]] });

  const profile = await (await fetch("https://api.github.com/user", {
    headers: { Authorization: `Bearer ${token.access_token}`, Accept: "application/vnd.github+json", "User-Agent": "art-crit" },
  })).json().catch(() => ({}));
  // The token is dropped here: only the id and login are kept, in the signed cookie.
  if (!Number.isSafeInteger(profile.id) || typeof profile.login !== "string") {
    return new Response("Could not read your GitHub profile. Go back and try again.", { status: 502, headers: [["Set-Cookie", clear]] });
  }
  const session = await seal(env.SESSION_SECRET, "session", { id: profile.id, login: profile.login }, SESSION_SECONDS);
  return redirect(saved.ret, [clear, setCookie(SESSION, session, SESSION_SECONDS)]);
}

async function sessionUser(request, env) {
  const session = await unseal(env.SESSION_SECRET, "session", cookieValue(request, SESSION));
  return session && { id: session.id, login: session.login };
}

// ---- votes
// The runs of a page come from its published page.json, so votes can only land on results that exist.
async function pageRuns(pages, slug) {
  if (typeof slug !== "string" || !SLUG.test(slug)) throw new HttpError(400, "bad page slug"); // (an array would pass the regex)
  const res = await fetch(`${pages}/data/${slug}/page.json`, { cf: { cacheTtl: 60 } });
  // Pages answers a missing file with index.html (200) when docs/404.html is absent, so a page is only one if it's JSON.
  if (!res.ok || !(res.headers.get("Content-Type") ?? "").startsWith("application/json")) throw new HttpError(404, `no such page: ${slug}`);
  return new Set((await res.json()).runs.map((r) => r.id));
}

// Everything the viewer needs for one page: totals per run, and (signed in) the viewer's own hearts and medals.
// The cost of a view stays flat however many votes there are: the totals are one row per run (kept by the triggers
// in schema.sql), and a viewer's own votes are looked up by (page, user), never by scanning the page's voters.
async function readVotes(env, slug, runs, user) {
  const db = env.DB;
  const statements = [db.prepare("SELECT run, hearts, gold, silver, bronze FROM tallies WHERE page = ?").bind(slug)];
  if (user) {
    statements.push(
      db.prepare("SELECT run FROM hearts WHERE page = ? AND user_id = ?").bind(slug, user.id),
      db.prepare("SELECT medal, run FROM medals WHERE page = ? AND user_id = ?").bind(slug, user.id),
    );
  }
  const [tallies, myHearts, myMedals] = await db.batch(statements);
  const totals = Object.create(null);
  for (const id of runs) totals[id] = { hearts: 0, gold: 0, silver: 0, bronze: 0 };
  for (const { run, ...counts } of tallies.results) if (totals[run]) totals[run] = counts;
  let mine = null;
  if (user) {
    mine = { hearts: myHearts.results.map((r) => r.run).filter((id) => totals[id]), gold: null, silver: null, bronze: null };
    for (const { medal, run } of myMedals.results) if (totals[run]) mine[medal] = run;
  }
  return { user: user && { login: user.login }, totals, mine };
}

async function readBody(request, max = MAX_BODY) {
  const type = (request.headers.get("Content-Type") ?? "").split(";")[0].trim();
  if (type !== "application/json") throw new HttpError(415, "expected application/json");
  if (Number(request.headers.get("Content-Length")) > max) throw new HttpError(413, "request too large");
  const text = await request.text();
  if (text.length > max) throw new HttpError(413, "request too large");
  try {
    const body = JSON.parse(text);
    if (body && typeof body === "object" && !Array.isArray(body)) return body;
  } catch {}
  throw new HttpError(400, "bad JSON");
}

// PUT api/heart {p, run, on}   PUT api/medal {p, medal, run|null}
async function vote(request, env, pages, user, kind) {
  const body = await readBody(request);
  const runs = await pageRuns(pages, body.p);
  const db = env.DB;
  const slug = body.p;
  const known = (run) => typeof run === "string" && runs.has(run);
  let statements;
  if (kind === "heart") {
    if (!known(body.run)) throw new HttpError(400, "no such run");
    if (typeof body.on !== "boolean") throw new HttpError(400, "on must be true or false");
    statements = [body.on
      ? db.prepare("INSERT OR IGNORE INTO hearts (page, run, user_id) VALUES (?, ?, ?)").bind(slug, body.run, user.id)
      : db.prepare("DELETE FROM hearts WHERE page = ? AND run = ? AND user_id = ?").bind(slug, body.run, user.id)];
  } else {
    if (!MEDALS.includes(body.medal)) throw new HttpError(400, "medal must be gold, silver or bronze");
    if (body.run !== null && !known(body.run)) throw new HttpError(400, "no such run");
    // Placing a medal frees that medal's old result and any other medal this user had put on the new one.
    statements = [db.prepare("DELETE FROM medals WHERE page = ? AND user_id = ? AND (medal = ? OR run = ?)").bind(slug, user.id, body.medal, body.run)];
    if (body.run !== null) statements.push(db.prepare("INSERT INTO medals (page, user_id, medal, run) VALUES (?, ?, ?, ?)").bind(slug, user.id, body.medal, body.run));
  }
  await db.batch(statements);
  return json(await readVotes(env, slug, runs, user));
}

// ---- prompt requests (adr/0030)
// POST api/request {prompt, kind, note?}: a signed-in visitor's prompt idea becomes an issue on the repo, labeled
// "prompt request". The issue is opened with GITHUB_ISSUES_TOKEN (a fine-grained token with Issues: write on this one
// repo), never the visitor's own GitHub token, which the site doesn't keep. Each user gets REQUESTS_PER_DAY a day and
// the whole site REQUESTS_PER_DAY_ALL, counted in D1, so the bot can't be used to flood the repo.
const REPO = "tokenosopher/mtwabp-bench";
const REQUEST_KINDS = { media: "Vector", godot: "Game", web: "Web", blender: "3D", text: "Text" };
const REQUESTS_PER_DAY = 5;
const REQUESTS_PER_DAY_ALL = 50;
const MAX_REQUEST_BODY = 8192;
const MAX_PROMPT = 4000;
const MAX_NOTE = 1000;

// Untrusted text inside a fence longer than any run of backticks in it: GitHub shows it verbatim (no Markdown, no
// @mentions, no links), so a request can't ping people or dress itself up.
function fenced(text) {
  const longest = Math.max(0, ...(text.match(/`+/g) ?? []).map((run) => run.length));
  const fence = "`".repeat(Math.max(3, longest + 1));
  return `${fence}text\n${text}\n${fence}`;
}

export function issueFor({ prompt, kind, note }, login) {
  const firstLine = prompt.split("\n")[0].replace(/\s+/g, " ").trim();
  const title = `Prompt request: ${firstLine.length > 80 ? `${firstLine.slice(0, 79)}…` : firstLine}`;
  const body = [
    `**Kind:** ${REQUEST_KINDS[kind]} (\`--kind ${kind}\`)`,
    "",
    "**Prompt**",
    "",
    fenced(prompt),
    ...(note ? ["", "**Note**", "", fenced(note)] : []),
    "",
    `Requested on the site by GitHub user \`${login}\`.`,
  ].join("\n");
  return { title, body, labels: ["prompt request"] };
}

async function requestPrompt(request, env, user) {
  if (!env.GITHUB_ISSUES_TOKEN) throw new HttpError(503, "prompt requests are not configured");
  const body = await readBody(request, MAX_REQUEST_BODY);
  const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
  const note = typeof body.note === "string" ? body.note.trim() : "";
  if (prompt.length < 10 || prompt.length > MAX_PROMPT) throw new HttpError(400, `the prompt must be 10 to ${MAX_PROMPT} characters`);
  if (typeof body.kind !== "string" || !Object.hasOwn(REQUEST_KINDS, body.kind)) throw new HttpError(400, "unknown kind");
  if (note.length > MAX_NOTE) throw new HttpError(400, `the note must be at most ${MAX_NOTE} characters`);

  const db = env.DB;
  const since = now() - 24 * 3600;
  const [mine, all] = await db.batch([
    db.prepare("SELECT COUNT(*) AS n FROM prompt_requests WHERE user_id = ? AND at > ?").bind(user.id, since),
    db.prepare("SELECT COUNT(*) AS n FROM prompt_requests WHERE at > ?").bind(since),
  ]);
  if (mine.results[0].n >= REQUESTS_PER_DAY) throw new HttpError(429, `you can send ${REQUESTS_PER_DAY} requests a day; try again tomorrow`);
  if (all.results[0].n >= REQUESTS_PER_DAY_ALL) throw new HttpError(429, "too many requests today; try again tomorrow");

  const res = await fetch(`https://api.github.com/repos/${REPO}/issues`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_ISSUES_TOKEN}`, Accept: "application/vnd.github+json",
      "Content-Type": "application/json", "User-Agent": "art-crit", "X-GitHub-Api-Version": "2022-11-28",
    },
    body: JSON.stringify(issueFor({ prompt, kind: body.kind, note }, user.login)),
  });
  if (!res.ok) {
    console.error("GitHub issue not created", res.status); // never log the token or the request
    throw new HttpError(502, "GitHub did not accept the request; try again later");
  }
  const issue = await res.json();
  await db.batch([db.prepare("INSERT INTO prompt_requests (user_id, at, issue) VALUES (?, ?, ?)").bind(user.id, now(), issue.number)]);
  return json({ number: issue.number, url: issue.html_url }, 201);
}

// ---- routing
const ROUTES = {
  login: { GET: (c) => startLogin(c.url, c.env) },
  callback: { GET: (c) => finishLogin(c.request, c.url, c.env) },
  logout: { POST: () => json({ ok: true }, 200, [["Set-Cookie", setCookie(SESSION, "", 0)]]) },
  votes: {
    GET: async (c) => {
      const slug = c.url.searchParams.get("p");
      return json(await readVotes(c.env, slug, await pageRuns(c.pages, slug), await sessionUser(c.request, c.env)));
    },
  },
  heart: { PUT: (c) => c.signedIn((user) => vote(c.request, c.env, c.pages, user, "heart")) },
  medal: { PUT: (c) => c.signedIn((user) => vote(c.request, c.env, c.pages, user, "medal")) },
  request: { POST: (c) => c.signedIn((user) => requestPrompt(c.request, c.env, user)) },
};

export async function handleApi(request, env, pages) {
  const url = new URL(request.url);
  const handlers = Object.hasOwn(ROUTES, url.pathname.slice(API.length)) ? ROUTES[url.pathname.slice(API.length)] : null;
  if (!handlers) return json({ error: "not found" }, 404);
  const handler = handlers[request.method];
  if (!handler) return json({ error: "method not allowed" }, 405, [["Allow", Object.keys(handlers).join(", ")]]);
  if (!env.DB || !env.GITHUB_CLIENT_ID || !env.GITHUB_CLIENT_SECRET || !env.SESSION_SECRET) return json({ error: "voting is not configured" }, 503);
  try {
    if (request.method !== "GET" && request.headers.get("Origin") !== url.origin) throw new HttpError(403, "cross-origin write refused");
    const signedIn = async (run) => {
      const user = await sessionUser(request, env);
      if (!user) throw new HttpError(401, "sign in with GitHub first");
      return run(user);
    };
    return await handler({ request, url, env, pages, signedIn });
  } catch (err) {
    if (err instanceof HttpError) return json({ error: err.message }, err.status);
    console.error(err); // D1 or GitHub trouble: say so plainly, without details
    return json({ error: "internal error" }, 500);
  }
}
