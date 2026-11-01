import { handleApi } from "./votes.mjs";

// The Worker in front of the site: it serves every path under SITE_PREFIX (the whole host when the prefix is empty).
// The Pages project holds the static files; large Godot engines are stored there as .wasm.gz (Pages caps assets at
// 25 MiB). <prefix>/api/* is the votes API (votes.mjs), the only part of the site that isn't static.
// The site's address is set in cloudflare/wrangler.jsonc only: `routes` (the host) and `vars` SITE_PREFIX, PAGES_URL
// and GITHUB_REPO (DEPLOY.md).
const ENGINE = /^\/engines\/[a-f0-9]{12}\/godot\.wasm$/;
// Everything under data/ is model-made (games, packaged pages, SVGs). The viewer embeds it in a sandboxed iframe; this
// header gives a direct visit the same opaque origin, so the file can't act on the site's origin (its cookies, the
// votes API) if someone opens or shares its raw URL (ADR-0004). The flags match the iframe's, so embedding is unchanged.
const DATA = /^\/data\//;
const SANDBOX = "sandbox allow-scripts allow-pointer-lock";

// SITE_PREFIX is "" (the site is the whole host, e.g. bench.example.com/) or a path such as "/bench" (no trailing slash).
export function siteConfig(env) {
  const prefix = String(env?.SITE_PREFIX ?? "").replace(/\/+$/, "");
  if (prefix && !/^\/[A-Za-z0-9._~-]+(\/[A-Za-z0-9._~-]+)*$/.test(prefix)) throw new Error(`bad SITE_PREFIX ${JSON.stringify(prefix)}`);
  if (!env?.PAGES_URL) throw new Error("PAGES_URL is not set (cloudflare/wrangler.jsonc vars)");
  return { prefix, pages: String(env.PAGES_URL).replace(/\/+$/, "") };
}

export default {
  async fetch(request, env) {
    const { prefix, pages } = siteConfig(env);
    const url = new URL(request.url);
    if (prefix && url.pathname === prefix) {
      url.pathname += "/";
      return Response.redirect(url.toString(), 308);
    }
    if (!url.pathname.startsWith(`${prefix}/`)) return new Response("Not found", { status: 404 });
    if (url.pathname.startsWith(`${prefix}/api/`)) return handleApi(request, env, pages, prefix);
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response("Method not allowed", { status: 405 });
    }

    const path = url.pathname.slice(prefix.length);
    const upstream = new URL(pages);
    upstream.pathname = ENGINE.test(path) ? `${path}.gz` : path;
    upstream.search = url.search;
    // Keep Range for Safari video playback; never forward cookies or credentials.
    const headers = new Headers();
    if (!ENGINE.test(path)) {
      for (const name of ["Range", "If-Range"]) {
        if (request.headers.has(name)) headers.set(name, request.headers.get(name));
      }
    }
    const response = await fetch(upstream.toString(), { headers });
    if (!ENGINE.test(path)) {
      const served = await serveStatic(request, response, prefix);
      if (!DATA.test(path)) return served;
      const sandboxed = new Response(served.body, served);
      sandboxed.headers.set("Content-Security-Policy", SANDBOX);
      return sandboxed;
    }
    if (response.status !== 200) return response;
    const wasmHeaders = new Headers({
      "Content-Type": "application/wasm",
      "Access-Control-Allow-Origin": "*", // sandboxed game frames have opaque origins
      "Cache-Control": "public, max-age=31536000, immutable", // hashed engine directory
    });
    if (request.method === "HEAD") return new Response(null, { status: 200, headers: wasmHeaders });
    return new Response(response.body.pipeThrough(new DecompressionStream("gzip")), { status: 200, headers: wasmHeaders });
  },
};

// A static file from Pages as is, except that Range requests for small videos get a synthesized 206, and the 404 page
// (docs/404.html, served at any depth) gets its home link under the prefix.
async function serveStatic(request, response, prefix) {
  if (prefix && response.status === 404 && response.headers.get("Content-Type")?.startsWith("text/html")) {
    const html = (await response.text()).replaceAll('href="/"', `href="${prefix}/"`);
    const headers = new Headers(response.headers);
    headers.delete("Content-Length");
    return new Response(request.method === "HEAD" ? null : html, { status: 404, headers });
  }
  // Pages currently ignores Range on MP4s. Our normalized videos are ≤2 MiB;
  // synthesize a partial response for Safari without buffering larger assets.
  const range = request.headers.get("Range");
  if (request.method === "GET" && range && response.status === 200 &&
      response.headers.get("Content-Type")?.startsWith("video/")) {
    const length = Number(response.headers.get("Content-Length"));
    if (length > 0 && length <= 2 * 1024 * 1024 &&
        (!request.headers.has("If-Range") || request.headers.get("If-Range") === response.headers.get("ETag"))) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(range);
      if (match && (match[1] || match[2])) {
        const start = match[1] ? Number(match[1]) : Math.max(0, length - Number(match[2]));
        const end = match[1] ? (match[2] ? Math.min(Number(match[2]), length - 1) : length - 1) : length - 1;
        if (start >= length || end < start) {
          return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${length}` } });
        }
        const bytes = await response.arrayBuffer();
        const partialHeaders = new Headers(response.headers);
        partialHeaders.set("Content-Range", `bytes ${start}-${end}/${length}`);
        partialHeaders.set("Content-Length", String(end - start + 1));
        partialHeaders.set("Accept-Ranges", "bytes");
        return new Response(bytes.slice(start, end + 1), { status: 206, headers: partialHeaders });
      }
    }
  }
  return response;
}
