"""`run.summary`: what the agent says it made. Every brief asks it to end its final message with a `Blurb:` line (one
to three third-person sentences for the site's visitors); when that line is there the summary is the blurb alone, as
plain text, else it falls back to the whole closing message (Markdown, cut at MAX_CHARS). It is read from the
*published* transcript (session/conversation.json, already cleaned and secret-scanned): run.json itself isn't scanned
(see kinds/text.py)."""

import json
import re

MAX_CHARS = 4000
BLURB_MAX = 500
BLURB = re.compile(r"^[ \t>*_#-]*blurb[*_]*\s*:[*_]*[ \t]*(.*)", re.I | re.M)
EMPHASIS = re.compile(r"(?<![\w*`])(\*\*|__|\*|_|`)(?=\S)(.+?)(?<=\S)\1(?![\w*`])")
SENTENCE_END = re.compile(r"[.!?][\"')\]*_]*(?=\s)")


def last_assistant_text(entries):
    """The text parts (not thinking or tool calls) of the last assistant message that has any, or None."""
    for entry in reversed(entries if isinstance(entries, list) else []):
        msg = entry.get("message") if isinstance(entry, dict) else None
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        content = msg.get("content")
        if isinstance(content, list):
            content = "\n\n".join(p["text"] for p in content
                                  if isinstance(p, dict) and p.get("type") == "text" and isinstance(p.get("text"), str))
        if isinstance(content, str) and content.strip():
            return content.strip()
    return None


def cut(text, limit=MAX_CHARS):
    """`text` when it fits in `limit` characters, else its start cut at the last paragraph break (or, failing that,
    sentence end, then word) that keeps at least half, with "…". An unclosed code fence is closed."""
    if len(text) <= limit:
        return text
    head = text[:limit - 8]  # room for the "…" and a closing fence
    floor = limit // 2
    para = head.rfind("\n\n")
    sentences = [m.end() for m in SENTENCE_END.finditer(head)]
    if para >= floor:
        out = head[:para].rstrip() + "\n\n…"
    elif sentences and sentences[-1] >= floor:
        out = head[:sentences[-1]] + " …"
    else:
        out = (head.rsplit(None, 1)[0] if " " in head[floor:] else head).rstrip() + "…"
    if len(re.findall(r"^\s{0,3}(```|~~~)", out, re.M)) % 2:
        out += "\n```"
    return out


def blurb_of(text):
    """The text after the last `Blurb:` line, to the end of its paragraph (it may wrap over several lines), as one plain
    line: Markdown emphasis and code marks stripped, at most BLURB_MAX characters. None when there is no such line or
    it is empty."""
    found = list(BLURB.finditer(text))
    if not found:
        return None
    rest = re.split(r"\n\s*\n", text[found[-1].start(1):].lstrip(" \t"), maxsplit=1)[0]
    blurb = " ".join(rest.split())
    for _ in range(3):  # nested emphasis (***x***, **_x_**)
        blurb = EMPHASIS.sub(r"\2", blurb)
    blurb = blurb.strip().strip('"“”').strip()
    if not blurb:
        return None
    if len(blurb) > BLURB_MAX:
        head = blurb[:BLURB_MAX - 1]
        ends = [m.end() for m in SENTENCE_END.finditer(head + " ")]
        blurb = head[:ends[-1]] if ends and ends[-1] >= BLURB_MAX // 2 else head.rsplit(None, 1)[0].rstrip(",;:") + "…"
    return blurb


def summary_of(run_dir):
    """The run's summary from its published transcript (run_dir/session/conversation.json), or None."""
    path = run_dir / "session" / "conversation.json"
    if not path.is_file():
        return None
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    text = last_assistant_text(entries)
    if not text:
        return None
    return blurb_of(text) or cut(text)
