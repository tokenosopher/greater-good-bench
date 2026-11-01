# Deploying Greater Good Bench

The checklist for putting the site on Cloudflare with community votes and prompt requests. The why and the details
are in README's [Cloudflare deployment](README.md#cloudflare-deployment) and ADRs 0021, 0022 and 0030; this file is
the order to do things in. Run the commands from the repo root. `bench.example.com` below stands for your address.

## Already live on GitHub Pages

The site is served now at https://tokenosopher.github.io/greater-good-bench/ (repo Settings → Pages, source
`main` branch, `/docs` folder). `art-crit publish` updates it in about a minute. Games boot there; votes and the
request form fall back to GitHub's new-issue page. Keep it as a fallback, or turn it off in Settings → Pages once
Cloudflare serves the site.

## The two decisions

1. **Address.** A subdomain of its own (`bench.yourdomain.com`, recommended) or a path on a domain that already serves
   something (`yourdomain.com/bench`). The Worker supports both.
2. **Pages project name.** Keep the suggested `greater-good-bench`; its address is `https://greater-good-bench.pages.dev`.

## 1. Cloudflare account and DNS

- Sign up at https://dash.cloudflare.com, then **Add a domain** and switch the domain's nameservers at your registrar
  to the two Cloudflare shows. Wait until the domain says **Active**.
- `pages.dev` alone is not enough: the Godot games need the Worker to stream their engine (Pages caps files at
  25 MiB, so the 38 MB `godot.wasm` is stored gzipped), and a Worker needs a domain on Cloudflare. Without a domain,
  stay on GitHub Pages.

Check: `dig +short NS yourdomain.com` lists `*.ns.cloudflare.com`.

## 2. The Pages project (static files, built from GitHub)

1. Workers & Pages → Create → **Pages** → Connect to Git. When asked, install/authorize the **Cloudflare Pages GitHub
   app** for `tokenosopher/greater-good-bench` (only that repo is enough).
2. Settings: project name `greater-good-bench`, production branch `main`, framework preset **None**,
   build command `python3 cloudflare/prepare.py`, build output directory `cloudflare-dist`, root directory `/` (empty).
3. Save and deploy. The first build is slow (a few minutes): `.python-version` makes Cloudflare compile Python 3.12.
   Later builds take about a minute. Don't add a custom domain to the Pages project; the Worker fronts it.

To try the build locally first: `python3 cloudflare/prepare.py` (writes the git-ignored `cloudflare-dist/`, about
150 MB in ~900 files, every file under 25 MiB; it fails loudly if one isn't).

Check (use the address the dashboard shows if Cloudflare added a suffix):

```sh
curl -sI https://greater-good-bench.pages.dev/ | head -1                        # HTTP/2 200
curl -s https://greater-good-bench.pages.dev/data/pages.json | head -c 200; echo # the page list
```

## 3. The Worker (your domain, engine streaming, the API)

1. Set the address in **`cloudflare/wrangler.jsonc`**, the one place for it (each value has a comment there):
   - `routes`: replace `bench.example.com` with your subdomain (a Custom Domain: Cloudflare creates its DNS record and
     certificate; the name must not have a DNS record already). For a path, use the commented zone-route variant.
   - `vars.SITE_PREFIX`: `""` for a subdomain, or `"/bench"` for a path (no trailing slash).
   - `vars.PAGES_URL`: the Pages address from step 2.
   - `vars.GITHUB_REPO` is already `tokenosopher/greater-good-bench`.
2. Set the same address in **`art-crit.toml`** under `[site] url` (e.g. `"https://bench.yourdomain.com/"`): the video
   tools print it on their vote cards. Commit both files.
3. Log in and deploy (Node 20+; `npx` fetches Wrangler):

```sh
npx wrangler login                                    # opens the browser once
npx wrangler deploy --config cloudflare/wrangler.jsonc
```

Check:

```sh
S=https://bench.yourdomain.com                        # or https://yourdomain.com/bench
curl -sI $S/ | head -1                                # 200
E=$(ls docs/engines | head -1)                        # the published Godot engine
curl -sI $S/engines/$E/godot.wasm | grep -i content-type    # application/wasm (streamed from the .gz)
curl -s "$S/api/votes?p=svg"; echo                    # {"error":"voting is not configured"} until step 4
```

Then open a game page in the browser: it should boot.

## 4. Community votes (GitHub sign-in + D1)

1. **GitHub OAuth App**: GitHub → Settings → Developer settings → OAuth Apps → New. Homepage `$S/`
   (e.g. `https://bench.yourdomain.com/`), callback URL `$S/api/callback`. Generate a client secret.
2. **Database**: `npx wrangler d1 create art-crit-votes`. Paste the printed `database_id` into
   `cloudflare/wrangler.jsonc` and uncomment its three `d1_databases` lines.
3. **Tables**: `npx wrangler d1 execute art-crit-votes --remote --config cloudflare/wrangler.jsonc --file cloudflare/schema.sql`
4. **Secrets** (each prompts for the value):

```sh
npx wrangler secret put GITHUB_CLIENT_ID --config cloudflare/wrangler.jsonc
npx wrangler secret put GITHUB_CLIENT_SECRET --config cloudflare/wrangler.jsonc
openssl rand -base64 48    # paste this as SESSION_SECRET (changing it later signs everyone out)
npx wrangler secret put SESSION_SECRET --config cloudflare/wrangler.jsonc
```

5. **Redeploy**: `npx wrangler deploy --config cloudflare/wrangler.jsonc`

Check: `curl -s "$S/api/votes?p=svg"` returns JSON totals (not 503); a write from elsewhere is refused:
`curl -s -X PUT $S/api/heart -H 'Origin: https://evil.example'` → `cross-origin write refused`. Then sign in on the
site and give a heart. Backups: README, [Community votes](README.md#community-votes-one-time-setup).

## 5. Prompt requests (issues opened by a bot token)

1. GitHub → Settings → Developer settings → Fine-grained tokens → Generate. Repository access: only
   `tokenosopher/greater-good-bench`; permissions: **Issues: Read and write**, nothing else.
2. Optional: `gh label create "prompt request" -R tokenosopher/greater-good-bench`
3. `npx wrangler secret put GITHUB_ISSUES_TOKEN --config cloudflare/wrangler.jsonc`
4. Re-apply the tables (step 4.3) and redeploy (step 4.5).

Check: `npx wrangler secret list --config cloudflare/wrangler.jsonc` shows four secrets; send a request from the site's
form while signed in and it appears under the repo's Issues with the `prompt request` label.

## 6. Rate limit (recommended)

Dashboard → your domain → Security → WAF → Rate limiting rules → Create rule (details and the CLI form in README's
[Rate limiting](README.md#rate-limiting-recommended)). Characteristics IP, 30 requests per 10 seconds, Block for 10
seconds, expression (for a path, put the prefix before `/api/`):

```
(http.host eq "bench.yourdomain.com" and starts_with(http.request.uri.path, "/api/") and not (http.request.method eq "GET" and http.request.uri.path eq "/api/votes"))
```

Check: `for i in $(seq 60); do curl -s -o /dev/null -w '%{http_code} ' -X POST $S/api/logout; done; echo`
shows `403`s and then `429`s.

## Publishing new runs

`uv run art-crit publish` (or a run's automatic publish) commits `docs/` and pushes `main`; the Pages project rebuilds
in about a minute (GitHub Pages too, while it's on). The Worker only needs a redeploy when `cloudflare/` changes; after
a change to `cloudflare/schema.sql`, re-apply the tables before redeploying.

## Vercel instead

Import the repo in Vercel with output directory `docs`, framework None and no build command; it serves the site as is.
There is no Worker there: no votes, no bot-opened prompt requests (the form falls back to GitHub's new-issue page).
