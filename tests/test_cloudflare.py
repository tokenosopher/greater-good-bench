"""Pages staging and the router, on a path and on a host of its own (no live Cloudflare calls)."""

import gzip
import shutil
import subprocess
from pathlib import Path

import pytest

from cloudflare.prepare import LIMIT, prepare


def test_pages_build_compresses_large_engine_without_changing_source(tmp_path):
    source = tmp_path / "docs"
    engine = source / "engines" / "abcdef012345"
    engine.mkdir(parents=True)
    # A sparse, compressible file above the per-asset cap.
    original = b"\0" * (LIMIT + 1)
    (engine / "godot.wasm").write_bytes(original)
    (source / "index.html").write_text("<a href='page.html'>page</a>")
    destination = tmp_path / "dist"
    prepare(source, destination)
    assert gzip.decompress((destination / "engines/abcdef012345/godot.wasm.gz").read_bytes()) == original
    assert not (destination / "engines/abcdef012345/godot.wasm").exists()
    assert (engine / "godot.wasm").read_bytes() == original
    assert (destination / "index.html").read_text() == (source / "index.html").read_text()
    prepare(source, destination)  # can be rerun after imports change docs/


def test_pages_build_rejects_other_oversized_files(tmp_path):
    source = tmp_path / "docs"
    source.mkdir()
    (source / "too-big.bin").write_bytes(b"x" * (LIMIT + 1))
    with pytest.raises(ValueError, match="too-big.bin"):
        prepare(source, tmp_path / "dist")


@pytest.mark.skipif(not shutil.which("node"), reason="node unavailable")
def test_router_strips_prefix_and_decompresses_wasm():
    script = r"""
import { gzipSync } from 'node:zlib';
import assert from 'node:assert/strict';
import router from './cloudflare/router.mjs';
// wrangler.jsonc's vars for a site on a path; the second half runs the same Worker with SITE_PREFIX "".
const env = { SITE_PREFIX: '/art-crit', PAGES_URL: 'https://art-crit.pages.dev' };
let urls = [];
let forwarded = [];
globalThis.fetch = async (url, options) => {
  urls.push(url);
  forwarded.push(options.headers);
  return url.endsWith('.gz')
    ? new Response(gzipSync(Buffer.from('wasm bytes')))
    : url.endsWith('.mp4')
      ? new Response('0123456789', { headers: {
          'content-type': 'video/mp4', 'content-length': '10',
          'access-control-allow-origin': '*', etag: 'video-tag',
        } })
      : url.endsWith('/missing.html')
        ? new Response('<a href="/">Back</a>', { status: 404, headers: { 'content-type': 'text/html; charset=utf-8' } })
        : new Response('ok', { headers: { 'access-control-allow-origin': '*' } });
};
const request = (path, method = 'GET') => router.fetch(new Request('https://fenderog.com' + path, { method }), env);
let response = await request('/art-crit/engines/abcdef012345/godot.wasm');
assert.equal(await response.text(), 'wasm bytes');
assert.equal(response.headers.get('content-type'), 'application/wasm');
assert.equal(response.headers.get('access-control-allow-origin'), '*');
assert.equal(urls.pop(), 'https://art-crit.pages.dev/engines/abcdef012345/godot.wasm.gz');
assert.equal((await request('/art-crit/page.html?p=horse')).status, 200);
assert.equal(urls.pop(), 'https://art-crit.pages.dev/page.html?p=horse');
response = await request('/art-crit');
assert.equal(response.status, 308);
assert.equal(response.headers.get('location'), 'https://fenderog.com/art-crit/');
assert.equal((await request('/art-crit/page.html', 'PUT')).status, 405); // static files stay read-only
assert.equal((await request('/art-crit/api/rank', 'PUT')).status, 404); // the owner's ranking API is local-only
response = await router.fetch(new Request('https://fenderog.com/art-crit/video.mp4', {
  headers: { Range: 'bytes=2-4', Cookie: 'private=yes' },
}), env);
assert.equal(response.status, 206);
assert.equal(response.headers.get('content-range'), 'bytes 2-4/10');
assert.equal(response.headers.get('accept-ranges'), 'bytes');
assert.equal(await response.text(), '234');
assert.equal(forwarded.pop().get('Range'), 'bytes=2-4');
assert.equal(forwarded.at(-1).get('Cookie'), null);
response = await router.fetch(new Request('https://fenderog.com/art-crit/video.mp4', {
  headers: { Range: 'bytes=12-' },
}), env);
assert.equal(response.status, 416);
response = await router.fetch(new Request('https://fenderog.com/art-crit/video.mp4', {
  headers: { Range: 'bytes=2-4', 'If-Range': 'other-tag' },
}), env);
assert.equal(response.status, 200);
assert.equal((await request('/art-crit-other/')).status, 404);
// Model-made files under data/ get the viewer's sandbox as a header too, so a direct visit has an opaque origin.
response = await request('/art-crit/data/horse/runs/r1/game/index.html');
assert.equal(response.headers.get('content-security-policy'), 'sandbox allow-scripts allow-pointer-lock');
assert.equal(await response.text(), 'ok');
response = await router.fetch(new Request('https://fenderog.com/art-crit/data/horse/runs/r1/media/clip.mp4', { headers: { Range: 'bytes=0-1' } }), env);
assert.equal(response.status, 206);
assert.equal(response.headers.get('content-security-policy'), 'sandbox allow-scripts allow-pointer-lock');
assert.equal((await request('/art-crit/page.html')).headers.get('content-security-policy'), null);
// docs/404.html links home with href="/": under a prefix the Worker points it at the prefix.
response = await request('/art-crit/missing.html');
assert.equal(response.status, 404);
assert.equal(await response.text(), '<a href="/art-crit/">Back</a>');

// The same Worker on a host of its own (SITE_PREFIX ""): every path is the site, nothing is stripped.
const root = { SITE_PREFIX: '', PAGES_URL: 'https://greater-good-bench.pages.dev/' };
const at = (path, init = {}) => router.fetch(new Request('https://bench.example.com' + path, init), root);
response = await at('/engines/abcdef012345/godot.wasm');
assert.equal(await response.text(), 'wasm bytes');
assert.equal(response.headers.get('content-type'), 'application/wasm');
assert.equal(urls.pop(), 'https://greater-good-bench.pages.dev/engines/abcdef012345/godot.wasm.gz');
assert.equal((await at('/')).status, 200);
assert.equal(urls.pop(), 'https://greater-good-bench.pages.dev/');
assert.equal((await at('/page.html?p=horse')).status, 200);
assert.equal(urls.pop(), 'https://greater-good-bench.pages.dev/page.html?p=horse');
assert.equal((await at('/page.html', { method: 'PUT' })).status, 405);
assert.equal((await at('/api/rank', { method: 'PUT' })).status, 404);
assert.equal((await at('/api/votes?p=horse')).status, 503); // no database or secrets in this env
response = await at('/data/horse/runs/r1/media/clip.mp4', { headers: { Range: 'bytes=0-1' } });
assert.equal(response.status, 206);
assert.equal(response.headers.get('content-security-policy'), 'sandbox allow-scripts allow-pointer-lock');
assert.equal(await (await at('/missing.html')).text(), '<a href="/">Back</a>'); // already right at the root
await assert.rejects(() => router.fetch(new Request('https://bench.example.com/'), { SITE_PREFIX: '' }), /PAGES_URL/);
await assert.rejects(() => router.fetch(new Request('https://bench.example.com/'), { ...root, SITE_PREFIX: 'bench' }), /SITE_PREFIX/);
"""
    subprocess.run(["node", "--input-type=module", "-e", script], check=True, cwd=Path(__file__).resolve().parents[1])


def _has_node_sqlite():
    node = shutil.which("node")
    return bool(node) and subprocess.run([node, "-e", "require('node:sqlite')"], capture_output=True).returncode == 0


@pytest.mark.skipif(not _has_node_sqlite(), reason="needs node with node:sqlite (22.13+)")
def test_votes_api():
    """Sign-in, hearts and medals (cloudflare/votes.mjs) against a real SQLite with a faked GitHub and Pages."""
    result = subprocess.run(["node", "--test", "tests/js/votes.test.mjs"], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
