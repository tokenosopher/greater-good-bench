"""The `text` kind: the agent writes one Markdown file in work/output/, published as is and rendered by the viewer
as a readable page (by its own markdown.js, never as HTML). See SPEC.md "Kinds" and ADR-0036."""

import json
import re
import shutil

from . import Kind, Staged
from .media import SOURCE_MAX_BYTES, _is_text

MAX_BYTES = 200 * 1024
FILE = "text.md"  # the output's name in out_dir and under the run's text/ dir
EXCERPT_CHARS = 300
H1 = re.compile(r"\s{0,3}#\s+(.+?)\s*#*\s*$")


def check(raw, name):
    """The Markdown bytes -> (text, error): UTF-8, at most MAX_BYTES, at least one non-blank line."""
    if len(raw) > MAX_BYTES:
        return None, f"{name}: {len(raw) // 1024} KB, larger than {MAX_BYTES // 1024} KB"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, f"{name}: not UTF-8 text"
    if not text.strip():
        return None, f"{name}: empty"
    return text, None


def _prose_lines(text):
    """The lines outside fenced code blocks."""
    fenced = False
    for line in text.splitlines():
        if re.match(r"\s{0,3}(```|~~~)", line):
            fenced = not fenced
        elif not fenced:
            yield line


def title_of(text):
    """The first `# ` heading's text (as plain text), or None."""
    heading = next((m.group(1) for line in _prose_lines(text) if (m := H1.match(line))), None)
    return (plain(heading).strip() or None) if heading else None


def stats(text):
    """{bytes, words, title} of the Markdown text (words = whitespace-separated)."""
    return {"bytes": len(text.encode("utf-8")), "words": len(text.split()), "title": title_of(text)}


def plain(line):
    """One Markdown line as plain text: no block markers, emphasis, code ticks, link or image syntax, HTML tags."""
    line = re.sub(r"^\s{0,3}(#{1,6}\s+|>\s?|[-*+]\s+(\[[ xX]\]\s+)?|\d+[.)]\s+)", "", line)
    line = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", line)  # [text](url), ![alt](src)
    line = re.sub(r"<[^>]*>", "", line)
    line = re.sub(r"\*{1,3}|_{2,3}|~~|`+", "", line)
    line = re.sub(r"(?<!\w)_(\S(?:.*?\S)?)_(?!\w)", r"\1", line)  # _em_, but not snake_case
    return "" if re.fullmatch(r"\s*([-*_=|:]\s*){3,}", line) else line  # rules, setext underlines, table borders


def excerpt_of(text, limit=EXCERPT_CHARS):
    """The first ~`limit` characters as plain prose, cut at a word boundary with "…". The first `# ` heading (the
    title, which cards show on its own) is left out."""
    lines = list(_prose_lines(text))
    first_h1 = next((i for i, line in enumerate(lines) if H1.match(line)), None)
    if first_h1 is not None:
        del lines[first_h1]
    flat = " ".join(" ".join(plain(line) for line in lines).split())
    if len(flat) <= limit:
        return flat
    head = flat[:limit + 1]
    cut = head.rsplit(" ", 1)[0] if " " in head else flat[:limit]
    return cut.rstrip(" ,;:.-") + "…"


def finalize_text(work_dir, out_dir):
    """Check the one .md file in work_dir/output/ and write out_dir/text.md + out_dir/manifest.json; returns the
    manifest {ok, bytes, words, title, errors}. Never raises for bad agent output: problems become `errors`."""
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    output = work_dir / "output"
    files = sorted(p for p in output.rglob("*") if p.is_file() and p.suffix.lower() == ".md"
                   and not p.name.startswith(".")) if output.is_dir() else []
    names = ["-".join(p.relative_to(output).parts) for p in files]  # flattened like the media kind's
    manifest = {"ok": False, "bytes": None, "words": None, "title": None, "errors": []}
    if not files:
        manifest["errors"].append("no Markdown file in ./output/")
    elif len(files) > 1:
        manifest["errors"].append(f"{len(files)} Markdown files in ./output/ ({', '.join(names)}); expected exactly one")
    else:
        text, error = check(files[0].read_bytes(), names[0])
        if error:
            manifest["errors"].append(error)
        else:
            (out_dir / FILE).write_text(text, encoding="utf-8")
            manifest.update(ok=True, **stats(text))
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


class Text(Kind):
    name = "text"
    tools = ()  # nothing has to be on PATH: the agent only writes a file
    activity = "checking"

    def finalize(self, work_dir, out_dir):
        manifest = finalize_text(work_dir, out_dir)
        return manifest["ok"], "; ".join(manifest["errors"])[:200] or None

    def verify(self, out_dir):
        """The file to publish still passes the checks (there is no browser step: the viewer renders it)."""
        path = out_dir / FILE
        if not path.is_file():
            return {"ok": False, "bytes": None, "words": None, "error": f"no {FILE}"}
        text, error = check(path.read_bytes(), FILE)
        if error:
            return {"ok": False, "bytes": path.stat().st_size, "words": None, "error": error}
        s = stats(text)
        return {"ok": True, "bytes": s["bytes"], "words": s["words"]}

    def stage(self, out_dir, run_dir, ctx):
        """The Markdown is model-written text, so it's cleaned and secret-scanned like source. The title and excerpt
        are read from that cleaned copy: they go into run.json, which isn't scanned itself. No thumbnail."""
        dest = run_dir / "text" / FILE
        ctx.write_text(out_dir / FILE, dest)
        text = dest.read_text(encoding="utf-8")
        return Staged({"text": f"text/{FILE}", **stats(text), "excerpt": excerpt_of(text)}, None)

    def keep_source(self, rel, path):
        """Text files of at most 512 KB (notes, drafts, scripts), but nothing under output/: the Markdown there is the
        output itself."""
        if rel.parts[0] == "output":
            return False
        return path.stat().st_size <= SOURCE_MAX_BYTES and _is_text(path)
