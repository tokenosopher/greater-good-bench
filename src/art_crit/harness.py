"""The agent-program interface (`art-crit run` drives one of these): Pi, ClaudeCode, Agy, GrokBuild, MuseCode, Codex
and Ori. Also the pure session parsers: metrics + state (see SPEC.md "Metrics" and "Harness interface").

Every harness hands the runner the same things: a command line, a session in pi's format
(`session_entries`, published as conversation.json, which the viewer renders) and metrics.
"""

import base64
import binascii
import json
import os
import re
import subprocess
import threading
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .kinds.media import thumbnail
from .util import LEVEL_INDEX, LEVEL_ORDER, CritError

# art-crit-shipped pi extension for OpenRouter runs (see pi_ext/openrouter_routing.ts): it records
# which upstream served each response and what OpenRouter charged, and pins the upstream for
# `MODEL@slug` runs. Passed with an explicit `-e` (which still loads under `-ne`).
ROUTING_EXTENSION = Path(__file__).parent / "pi_ext" / "openrouter_routing.ts"
# For unpinned OpenRouter Gemini runs (see pi_ext/openrouter_sticky_upstream.ts): keeps every request on
# the upstream that served the first one, since Gemini's thought signatures don't verify across upstreams.
STICKY_EXTENSION = Path(__file__).parent / "pi_ext" / "openrouter_sticky_upstream.ts"
MCP_TIMEOUT_S = 600  # per MCP tool call; a Blender render can take minutes (the clients default to ~60s)


def write_mcp_config(path, servers):
    """A run's MCP servers as the `mcpServers` JSON that pi and Claude Code read (`hidden` and `tools` are ours:
    each harness hides those tools its own way)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    servers = {name: {k: v for k, v in spec.items() if k not in ("hidden", "tools")} for name, spec in servers.items()}
    path.write_text(json.dumps({"mcpServers": servers}, indent=2) + "\n")
    return path


PROXY_SOURCE = Path(__file__).parent / "mcp_proxy.py"
SPEC_FILE = "art-crit-mcp.json"  # = mcp_proxy.SPEC_FILE (the proxy is copied out and runs on its own)
_global_config_lock = threading.Lock()


def proxy_path():
    """Where the MCP proxy is installed for global entries: a stable path outside the repo (it has moved before)."""
    cache = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return cache / "art-crit" / "mcp_proxy.py"


def install_proxy(mcp, session_dir):
    """Copy the proxy to proxy_path() (when it changed) and write the run's servers to <harness>/art-crit-mcp.json,
    where the proxy (started in <run>/work/) finds them. Not an env var: muse passes MCP servers only an allowlist of
    the environment. Returns the proxy's path."""
    proxy = proxy_path()
    with _global_config_lock:
        if not proxy.is_file() or proxy.read_text() != PROXY_SOURCE.read_text():
            proxy.parent.mkdir(parents=True, exist_ok=True)
            proxy.write_text(PROXY_SOURCE.read_text())
    (Path(session_dir) / SPEC_FILE).write_text(json.dumps(mcp, indent=2) + "\n")
    return proxy


def install_proxy_entries(config_path, mcp, session_dir, extra=lambda spec: {}):
    """For harnesses that only read a global MCP config (agy, muse): make sure it has one permanent `art-crit-<name>`
    entry per server, pointing at the proxy (mcp_proxy.py, copied to proxy_path()), plus `extra(spec)` (harness-specific
    fields), and write the run's servers for the proxy (`install_proxy`). Other entries and keys of the config are
    kept; it is only written when it changes."""
    proxy = install_proxy(mcp, session_dir)
    with _global_config_lock:
        config_path = Path(config_path)
        try:
            text = config_path.read_text() if config_path.is_file() else ""
            config = json.loads(text) if text.strip() else {}
        except ValueError:
            raise CritError(f"{config_path} isn't plain JSON (comments?); add the art-crit entries by hand or remove the comments")
        if "mcp_servers" in config:  # muse drops every server when both keys are present
            raise CritError(f"{config_path} uses the legacy mcp_servers key; rename it to mcpServers first")
        servers = config.setdefault("mcpServers", {})
        for name in mcp:
            servers[f"art-crit-{name}"] = {"command": "python3", "args": [str(proxy), name], **extra(mcp[name])}
        text = json.dumps(config, indent=2) + "\n"
        if not config_path.is_file() or config_path.read_text() != text:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = config_path.with_name(config_path.name + ".art-crit-tmp")
            tmp.write_text(text)
            tmp.replace(config_path)


def hidden_mcp_tools(mcp):
    """The hidden tools by their client-side names (`mcp__<server>__<tool>`, the same in pi and Claude Code)."""
    return [f"mcp__{name}__{tool}" for name, spec in (mcp or {}).items() for tool in spec.get("hidden", ())]


def grok_mcp_toml(mcp, proxy):
    """A run's MCP servers as Grok `[mcp_servers.<name>]` tables, each running the proxy (Grok has no setting that hides
    tools; `disabled_tools` is an unknown field there). JSON strings and lists are valid TOML."""
    lines = []
    for name in mcp:
        lines += [f"[mcp_servers.{name}]", 'command = "python3"', f"args = {json.dumps([str(proxy), name])}",
                  f"tool_timeout_sec = {MCP_TIMEOUT_S}", "startup_timeout_sec = 60", "enabled = true", ""]
    return "\n".join(lines)


def codex_mcp_args(mcp):
    """A run's MCP servers as Codex `-c mcp_servers.<name>...` overrides (TOML values; JSON strings are valid TOML)."""
    args = []
    for name, spec in (mcp or {}).items():
        env = ", ".join(f"{k} = {json.dumps(v)}" for k, v in spec.get("env", {}).items())
        args += ["-c", f"mcp_servers.{name}.command={json.dumps(spec['command'])}",
                 "-c", f"mcp_servers.{name}.args={json.dumps(spec.get('args', []))}",
                 "-c", f"mcp_servers.{name}.env={{{env}}}",
                 "-c", f"mcp_servers.{name}.disabled_tools={json.dumps(list(spec.get('hidden', ())))}",
                 "-c", f"mcp_servers.{name}.tool_timeout_sec={MCP_TIMEOUT_S}",
                 "-c", f"mcp_servers.{name}.startup_timeout_sec=60"]
    return args


SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")


def split_route(rest):
    """'openrouter/x/y@a,b:low' -> ('openrouter/x/y:low', ['a', 'b']); no '@' -> (rest, None).
    The part after '@' is SLUGS[:LEVELS], so the levels suffix stays attached to the spec."""
    base, sep, tail = rest.partition("@")
    if not sep:
        return rest, None
    upstreams, _, levels = tail.partition(":")
    slugs = [s.strip().lower() for s in upstreams.split(",") if s.strip()]
    if not slugs or any(not SLUG_RE.match(s) for s in slugs):
        raise CritError(f"bad @UPSTREAM in {rest!r}: expected @slug[,slug...] (each matching {SLUG_RE.pattern!r})")
    return base + (f":{levels}" if levels else ""), slugs


def split_model_route(model_arg):
    """'openrouter/x/y@a,b' -> ('openrouter/x/y', ['a', 'b']); no '@' -> (model_arg, None)."""
    base, sep, tail = model_arg.partition("@")
    if not sep:
        return model_arg, None
    slugs = [s.strip().lower() for s in tail.split(",") if s.strip()]
    return base, slugs


def upstream_key(name):
    """An OpenRouter upstream as a comparable key: slug "atlas-cloud/fp8" and the display name
    "AtlasCloud" (what responses report) both -> "atlascloud". The "/variant" can't be checked."""
    return re.sub(r"[^a-z0-9]", "", name.split("/", 1)[0].lower())


def read_route(harness_dir, model):
    """The OpenRouter route for a run: {requested, served: [...], cost_usd}. requested =
    {only, allow_fallbacks} for a pinned run (`MODEL@slug`), None when OpenRouter picked the upstream.
    From route.jsonl, written by the pi routing extension: `{id, provider}` and `{id, cost}` lines
    per response. served = the distinct upstream names; cost_usd = what OpenRouter charged, summed
    over responses (the last cost per id), or None when no response reported one. None for runs
    that aren't OpenRouter runs."""
    base, slugs = split_model_route(model)
    if not base.startswith("openrouter/"):
        return None
    path = Path(harness_dir) / "route.jsonl"
    served, costs = [], {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue
            if rec.get("provider") and rec["provider"] not in served:
                served.append(rec["provider"])
            if isinstance(rec.get("cost"), (int, float)):
                costs[rec.get("id")] = rec["cost"]
    requested = {"only": slugs, "allow_fallbacks": False} if slugs else None
    return {"requested": requested, "served": served,
            "cost_usd": sum(costs.values()) if costs else None}


class Harness:
    """One per agent program. `tag` marks its runs' ids and folders ("" for pi, the default)."""

    name = "harness"
    tag = ""

    def version(self):
        raise NotImplementedError

    def models(self):
        raise NotImplementedError

    def levels(self, model):
        raise NotImplementedError

    def resolve(self, model):
        """An alias -> the model id it stands for (identity by default)."""
        return model

    def display_model(self, model):
        """The model name recorded for a run (what the site shows)."""
        return model

    def split_spec(self, rest):
        """'MODEL[@UPSTREAMS][:LEVELS]' -> ('MODEL[:LEVELS]', upstreams or None). Only pi runs can
        pin an OpenRouter upstream (see `pinned`)."""
        return split_route(rest)

    def pinned(self, model, upstreams):
        """The model argument for a run: `model`, or `model@a,b` when upstreams are pinned."""
        if upstreams:
            raise CritError(f"{model}: @UPSTREAM only works for pi openrouter/ models")
        return model

    supports_mcp = False  # whether `command` can give the agent MCP servers (kinds like blender need it)
    BUILTIN_TOOLS = None  # the built-in tools `command` allows by name; None = the harness's own default set

    def tools(self, mcp=None):
        """What the agent is allowed, as run.json's `tools.allowed`: `builtin` (names, or None when art-crit doesn't
        restrict the harness's defaults) and `mcp` = {server: {allowed: [...], hidden: [...]}} for this run only."""
        return {"builtin": list(self.BUILTIN_TOOLS) if self.BUILTIN_TOOLS else None,
                "mcp": {name: {"allowed": list(spec.get("tools", ())), "hidden": list(spec.get("hidden", ()))}
                        for name, spec in (mcp or {}).items()}}

    def command(self, model, level, brief, session_dir, mcp=None):
        """The agent's argv. `mcp` = {name: {command, args, env, hidden, tools}}: stdio MCP servers for this run
        only, `hidden` = tool names the model must not get, `tools` = the ones it gets (optional; agy needs them).
        Only harnesses with `supports_mcp` take it. The agent's cwd is always the run's work/ (a sibling of session_dir).
        Harnesses with a per-run config use it; agy and muse only read a global one, which gets permanent proxy
        entries (`install_proxy_entries`)."""
        raise NotImplementedError

    def env(self, model=None, harness_dir=None):
        """The agent's environment (None = inherit art-crit's). Routed pi runs pass their
        model_arg + harness dir so per-run routing env can be set."""
        return None

    def session_file(self, session_dir):
        raise NotImplementedError

    def session_entries(self, session_dir, brief, level):
        """The session as pi-format entries (published as conversation.json), or None."""
        path = self.session_file(session_dir)
        if not path or not path.is_file():
            return None
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def metrics(self, session_dir, level=None):
        """parse_session()-shaped metrics, or None when there's no session yet. Tolerates a
        session that's still being written (live progress)."""
        path = self.session_file(session_dir)
        return parse_session(path) if path and path.is_file() else None

    def finish(self, harness_dir, model, metrics):
        """Final touches on a finished run's metrics (a dict, empty when the agent never wrote a
        session) from what the harness left in its scratch dir. `metrics["notes"]` are appended
        to the run's error and `metrics["extra"]` fields are added to the run. Identity by default."""
        return metrics


class Pi(Harness):
    """The `pi` CLI harness. See SPEC.md "Harness interface"."""

    name = "pi"
    supports_mcp = True

    def __init__(self, binary="pi"):
        self.binary = binary

    def version(self):
        try:
            r = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} --version: {e}")
        if r.returncode != 0:
            raise CritError(f"{self.binary} --version failed: {r.stderr.strip()}")
        return r.stdout.strip().splitlines()[0].strip()

    def models(self):
        r = subprocess.run([self.binary, "--list-models"], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise CritError(f"{self.binary} --list-models failed: {r.stderr.strip()}")
        lines = r.stdout.splitlines()
        models = []
        for line in lines[1:]:  # skip the header row
            parts = line.split()
            if len(parts) >= 2:
                models.append(f"{parts[0]}/{parts[1]}")
        return models

    def levels(self, model):
        """Ask pi over RPC which thinking levels `model` supports, in LEVEL_ORDER.

        `proc.stdout.readline()` blocks, so a 30s wall-clock deadline computed from
        `time.time()` never fires if pi hangs without answering; a `threading.Timer` that
        kills the process is used instead, so the blocking readline() always unblocks.
        """
        cmd = [self.binary, "--mode", "rpc", "--no-session", "--model", model, "-ne", "-ns", "-np", "-nc"]
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except OSError as e:
            raise CritError(f"cannot run {self.binary}: {e}")
        timer = threading.Timer(30, proc.kill)
        timer.start()
        try:
            proc.stdin.write('{"type":"get_available_thinking_levels"}\n')
            proc.stdin.flush()
            while True:
                line = proc.stdout.readline()
                if not line:
                    raise CritError(f"{model}: {self.binary} closed its output before answering get_available_thinking_levels (timed out?)")
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if data.get("type") == "response" and data.get("command") == "get_available_thinking_levels":
                    if not data.get("success"):
                        raise CritError(f"{model}: could not get thinking levels: {data}")
                    levels = data.get("data", {}).get("levels", [])
                    return [level for level in LEVEL_ORDER if level in levels]
        finally:
            timer.cancel()
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    def pinned(self, model, upstreams):
        if upstreams and not model.startswith("openrouter/"):
            raise CritError(f"{model}: @UPSTREAM only works for pi openrouter/ models")
        return f"{model}@{','.join(upstreams)}" if upstreams else model

    def finish(self, harness_dir, model, metrics):
        """An OpenRouter run: record the route (`metrics["extra"]["route"]`) and swap pi's catalog-price
        cost for what OpenRouter charged (pi's figure stays as `route.pi_cost_usd`; pi prices the
        calls at one rate whatever upstream served them). A pinned run served outside its `only`
        list gets a note."""
        route = read_route(harness_dir, model)
        if not route:
            return metrics
        only = {upstream_key(s) for s in route["requested"]["only"]} if route["requested"] else None
        # A response names the upstream by display name, which can be shorter than the slug ("Google" served
        # google-vertex/global), so a served key that starts a requested key counts as that upstream.
        outside = [s for s in route["served"] if not any(k.startswith(upstream_key(s)) for k in only)] if only else []
        notes = [f"served upstream outside requested only: {', '.join(outside)}"] if outside else []
        route["pi_cost_usd"] = metrics.get("cost_usd", 0.0)
        cost = route["cost_usd"] if route["cost_usd"] is not None else route["pi_cost_usd"]
        return {**metrics, "extra": {"route": route}, "cost_usd": cost, "notes": notes}

    def command(self, model, level, brief, session_dir, mcp=None):
        base, slugs = split_model_route(model)
        cmd = [
            self.binary,
            "-p",
            "--mode",
            "json",
            "--model",
            f"{base}:{level}",
            "--session-dir",
            str(session_dir),
            "-ne",
            "-ns",
            "-np",
            "-nc",
        ]
        if base.startswith("openrouter/"):
            cmd += ["-e", str(ROUTING_EXTENSION)]
            if base.startswith("openrouter/google/") and not slugs:
                cmd += ["-e", str(STICKY_EXTENSION)]
        if mcp:
            # pi's built-in MCP support (which -ne leaves out) has no per-run config flag: it reads ~/.pi/agent/mcp.json
            # and a trusted project's .pi/mcp.json, so the servers go in work/.pi/ (never published as source) and
            # --approve trusts that fresh work dir for this run only. `direct` declares the tools like a built-in's.
            servers = {name: {**spec, "exposure": "direct", "timeout": MCP_TIMEOUT_S} for name, spec in mcp.items()}
            write_mcp_config(Path(session_dir).parent / "work" / ".pi" / "mcp.json", servers)
            cmd += ["-e", "builtin:mcp", "--approve"]
            if hidden_mcp_tools(mcp):
                cmd += ["--exclude-tools", ",".join(hidden_mcp_tools(mcp))]
        return cmd + [brief]

    def env(self, model=None, harness_dir=None):
        """Every OpenRouter run logs its upstreams and real cost to ART_CRIT_ROUTE_LOG; a pinned one
        (`MODEL@slug`) also gets ART_CRIT_OPENROUTER_ROUTING. Other models inherit art-crit's env."""
        if model is None or harness_dir is None:
            return None
        base, slugs = split_model_route(model)
        if not base.startswith("openrouter/"):
            return None
        env = {**os.environ, "ART_CRIT_ROUTE_LOG": str(Path(harness_dir) / "route.jsonl")}
        env.pop("ART_CRIT_OPENROUTER_ROUTING", None)
        if slugs:
            env["ART_CRIT_OPENROUTER_ROUTING"] = json.dumps({"only": slugs, "allow_fallbacks": False})
        return env

    def session_file(self, session_dir):
        matches = sorted(p for p in Path(session_dir).glob("*.jsonl") if p.name != "events.jsonl")  # events.jsonl = pi's stdout
        return matches[0] if matches else None


def parse_session(path):
    """Read a pi session file and return metrics + thinkingLevel + whether it ended in error.

    Returns a dict: {thinking_level, turns, tool_calls, tokens: {...}, cost_usd, ended_in_error,
    error_message}. Pure and testable: no subprocess, no filesystem beyond reading `path`.

    Tolerates a partial last line: this is also called on a session file that a running agent
    is still appending to (for live progress), so a line caught mid-write is simply skipped
    rather than raising.
    """
    thinking_level = None
    turns = 0
    tool_calls = 0
    tokens = {"input": 0, "output": 0, "reasoning": 0, "cacheRead": 0, "cacheWrite": 0}
    cost_usd = 0.0
    ended_in_error = False
    error_message = None

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # a line the writer hasn't finished flushing yet
            if entry.get("type") == "thinking_level_change":
                thinking_level = entry.get("thinkingLevel")
                continue
            if entry.get("type") != "message":
                continue
            msg = entry.get("message") or {}
            if msg.get("role") != "assistant":
                continue
            turns += 1
            for block in msg.get("content") or []:
                if block.get("type") == "toolCall":
                    tool_calls += 1
            usage = msg.get("usage") or {}
            for key in tokens:
                tokens[key] += usage.get(key) or 0
            cost_usd += (usage.get("cost") or {}).get("total") or 0
            if msg.get("stopReason") == "error":
                ended_in_error = True
                error_message = msg.get("errorMessage") or error_message

    tokens["total"] = tokens["input"] + tokens["output"]
    return {
        "thinking_level": thinking_level,
        "turns": turns,
        "tool_calls": tool_calls,
        "tokens": tokens,
        "cost_usd": cost_usd,
        "ended_in_error": ended_in_error,
        "error_message": error_message,
    }


class ClaudeCode(Harness):
    """The `claude` CLI (Claude Code) harness. See SPEC.md "Harness interface".

    Each run is one direct agent: --safe-mode keeps the user's CLAUDE.md, memory, skills,
    plugins, hooks and MCP servers out of it (login still works), sub-agents are disallowed,
    and nothing is saved to the user's session history. The stdout stream-json is the session."""

    name = "claude-code"
    supports_mcp = True
    tag = "cc"
    # Models and effort levels (Claude Code has no command that lists them, so this mirrors the CLI's
    # own alias table + model catalog and has to be updated when they change). Aliases resolve to
    # these. A level the model doesn't take is silently clamped by the CLI (measured: `--effort xhigh`
    # on *-4-6 sends effort=high; on claude-haiku-4-5 --effort is ignored entirely, so it's not listed),
    # hence the trimmed lists. Levels from the catalog's capabilities, checked against the requests the
    # CLI actually sends.
    MODELS = {
        "claude-fable-5-1": ["low", "medium", "high", "xhigh", "max"],
        "claude-opus-5-5": ["low", "medium", "high", "xhigh", "max"],
        "claude-opus-5": ["low", "medium", "high", "xhigh", "max"],
        "claude-opus-4-8": ["low", "medium", "high", "xhigh", "max"],
        "claude-opus-4-7": ["low", "medium", "high", "xhigh", "max"],
        "claude-opus-4-6": ["low", "medium", "high", "max"],
        "claude-sonnet-5-5": ["low", "medium", "high", "xhigh", "max"],
        "claude-sonnet-5": ["low", "medium", "high", "xhigh", "max"],
        "claude-sonnet-4-6": ["low", "medium", "high", "max"],
        "claude-haiku-5-5": ["low", "medium", "high", "xhigh", "max"],
    }
    ALIASES = {"fable": "claude-fable-5-1", "opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5"}
    # Only the core file and shell tools, like pi: no web, scheduling, messaging or skills, and no
    # sub-agents (each model x effort is one direct run).
    TOOLS = "Bash,Read,Write,Edit,Glob,Grep"
    BUILTIN_TOOLS = TOOLS.split(",")
    NO_SUBAGENTS = "Agent,Task"

    def __init__(self, binary="claude"):
        self.binary = binary

    def version(self):
        try:
            r = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} --version: {e}")
        if r.returncode != 0:
            raise CritError(f"{self.binary} --version failed: {r.stderr.strip()}")
        return r.stdout.strip().split()[0]  # "2.1.283 (Claude Code)" -> "2.1.283"

    def models(self):
        return [*self.MODELS, *self.ALIASES]

    def resolve(self, model):
        return self.ALIASES.get(model, model)

    def levels(self, model):
        return self.MODELS[self.resolve(model)]

    def display_model(self, model):
        return f"anthropic/{self.resolve(model)}"

    def command(self, model, level, brief, session_dir, mcp=None):
        return [
            self.binary, "-p",
            "--model", self.resolve(model),
            "--effort", level,
            "--output-format", "stream-json", "--verbose",
            # --safe-mode also drops --mcp-config (measured, despite its help text), so a run with MCP servers
            # gets the same isolation from no settings sources (no user hooks/plugins), --strict-mcp-config and
            # CLAUDE_CODE_DISABLE_AUTO_MEMORY (env); the system prompt then differs only by the MCP server's tools.
            *(["--setting-sources="] if mcp else ["--safe-mode"]),
            "--permission-mode", "bypassPermissions",
            "--no-session-persistence",
            f"--tools={self.TOOLS}",
            f"--disallowed-tools={','.join([self.NO_SUBAGENTS, *hidden_mcp_tools(mcp)])}",
            "--disable-slash-commands",
            *([f"--mcp-config={write_mcp_config(Path(session_dir) / 'mcp.json', mcp)}", "--strict-mcp-config"] if mcp else []),
            "--", brief,
        ]

    def env(self, model=None, harness_dir=None):
        # art-crit itself may be running inside Claude Code; don't let the agent think it's nested.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE" and not k.startswith("CLAUDE_CODE_")}
        # A Blender render can take minutes; memory is off already under --safe-mode, and explicitly for MCP runs.
        return {**env, "MCP_TOOL_TIMEOUT": str(MCP_TIMEOUT_S * 1000), "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}

    def session_file(self, session_dir):
        path = Path(session_dir) / "events.jsonl"
        return path if path.is_file() else None

    def session_entries(self, session_dir, brief, level):
        path = self.session_file(session_dir)
        return convert_claude_stream(read_jsonl(path), brief, level) if path else None

    def metrics(self, session_dir, level=None):
        path = self.session_file(session_dir)
        return claude_metrics(read_jsonl(path), level) if path else None


def add_tool_durations(entries):
    """Set `durationMs` on each toolResult message that lacks one: its entry's timestamp minus the
    timestamp of the assistant entry that made the call (pi stamps entries when they're finished).
    Tools called together share a start, so parallel ones are exact and sequential ones cumulative.
    The Claude Code conversion sets exact ones itself. Entries without usable timestamps are left
    alone. Returns `entries`."""
    called = {}
    for entry in entries or []:
        msg = entry.get("message") or {}
        if msg.get("role") == "assistant":
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "toolCall":
                    called[block.get("id")] = entry.get("timestamp")
        elif msg.get("role") == "toolResult":
            if "durationMs" not in msg:
                _set_duration(msg, called.get(msg.get("toolCallId")), entry.get("timestamp"))
    return entries


def count_tools_used(entries):
    """{tool name: calls} over a pi-format session (MCP tools are `mcp__<server>__<tool>`), most-called first."""
    counts = {}
    for entry in entries or []:
        msg = entry.get("message") or {}
        if msg.get("role") == "assistant":
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "toolCall":
                    counts[block.get("name")] = counts.get(block.get("name"), 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _set_duration(result, start_iso, end_iso):
    start, end = _ms(start_iso), _ms(end_iso)
    if start is not None and end is not None:
        result["durationMs"] = max(0, round(end - start))


def _ms(iso):
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000
    except (AttributeError, ValueError):
        return None


def read_jsonl(path):
    """Parsed JSON lines, skipping blank and partial (still being written) ones."""
    out = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _claude_messages(events):
    """Assistant API messages from a stream-json event list, merged by message id (the stream
    can emit one event per content block, each repeating the message's usage)."""
    order, merged = [], {}
    for e in events:
        if e.get("type") != "assistant" or e.get("parent_tool_use_id"):
            continue
        msg = e.get("message") or {}
        mid = msg.get("id") or f"_{len(order)}"
        if mid not in merged:
            merged[mid] = {**msg, "content": []}
            order.append(mid)
        merged[mid]["content"] += msg.get("content") or []
        if msg.get("usage"):
            merged[mid]["usage"] = msg["usage"]
    return [merged[mid] for mid in order]


def _pi_usage(u):
    usage = {
        "input": u.get("input_tokens") or 0, "output": u.get("output_tokens") or 0,
        "cacheRead": u.get("cache_read_input_tokens") or 0, "cacheWrite": u.get("cache_creation_input_tokens") or 0,
    }
    usage["totalTokens"] = sum(usage.values())
    return usage


def _tool_content(content):
    """A tool_result's content -> pi content blocks: one text block, then one image block per image.
    An image (e.g. the agent reading a screenshot, often ~500 KB) is kept only as a small JPEG
    thumbnail, plus its original type and size; without ffmpeg it has no `data`."""
    blocks = content if isinstance(content, list) else [content]
    texts, images = [], []
    for c in blocks:
        if isinstance(c, dict) and c.get("type") == "image":
            images.append(_image_block(c.get("source") or {}))
        elif isinstance(c, dict) and c.get("type") == "text":
            texts.append(c.get("text", ""))
        elif isinstance(c, str):
            texts.append(c)
        elif c is not None:
            texts.append(json.dumps(c))
    return [{"type": "text", "text": "\n".join(texts)}, *images]


def _image_block(source):
    try:
        raw = base64.b64decode(source.get("data") or "", validate=True)
    except (binascii.Error, ValueError):
        raw = b""
    block = {"type": "image", "mimeType": "image/jpeg", "sourceMimeType": source.get("media_type"), "bytes": len(raw)}
    thumb = thumbnail(raw) if raw else None
    if thumb:
        block["data"] = base64.b64encode(thumb).decode()
    return block


def _tool_call(block, cwd):
    """A Claude Code tool_use block -> a pi toolCall. The tools the viewer knows (bash, write,
    edit, read) get pi's names and argument shapes, with paths made relative to the run dir."""
    name, args = block.get("name", ""), dict(block.get("input") or {})

    def rel(path):
        return path[len(cwd) + 1:] if cwd and isinstance(path, str) and path.startswith(cwd + "/") else path

    if name in ("Bash", "run_terminal_cmd"):
        name, args = "bash", {"command": args.get("command") or args.get("cmd") or ""}
    elif name in ("Write", "write_file"):
        name, args = "write", {"path": rel(args.get("file_path") or args.get("path")), "content": args.get("content", "")}
    elif name == "Edit":
        name, args = "edit", {"path": rel(args.get("file_path")), "edits": [{"oldText": args.get("old_string", ""), "newText": args.get("new_string", "")}]}
    elif name == "MultiEdit":
        edits = [{"oldText": e.get("old_string", ""), "newText": e.get("new_string", "")} for e in args.get("edits") or []]
        name, args = "edit", {"path": rel(args.get("file_path")), "edits": edits}
    elif name in ("Read", "read_file"):
        name, args = "read", {"path": rel(args.get("file_path") or args.get("path")), **{k: v for k, v in args.items() if k in ("offset", "limit")}}
    return {"type": "toolCall", "id": block.get("id"), "name": name, "arguments": args}


def convert_claude_stream(events, brief, level):
    """Claude Code stream-json events -> pi-format session entries (see SPEC.md "Harness
    interface"): session, model and effort entries, the brief as the user message, assistant
    messages (text / thinking / toolCall, with usage) and toolResult messages. Messages carry
    their stream event's `timestamp`; the session and the brief get the first one in the stream."""
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    cwd = init.get("cwd") or ""
    start = _stamp({}, next((e.get("timestamp") for e in events if e.get("timestamp")), None))
    entries = [
        {"type": "session", "cwd": cwd, **start},
        {"type": "model_change", "provider": "anthropic", "modelId": init.get("model")},
        {"type": "thinking_level_change", "thinkingLevel": level},
        {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": brief}]}, **start},
    ]
    pending = list(_claude_messages(events))  # merged, in stream order: emitted at their first event
    called = {}  # tool_use id -> the timestamp of the event that carried it
    for e in events:
        if e.get("parent_tool_use_id"):
            continue
        if e.get("type") == "assistant":
            for b in (e.get("message") or {}).get("content") or []:
                if b.get("type") == "tool_use":
                    called[b.get("id")] = e.get("timestamp")
            if not pending or (pending[0].get("id") and pending[0]["id"] != (e.get("message") or {}).get("id")):
                continue  # a later event of a message already emitted
            msg = pending.pop(0)
            content = []
            for b in msg["content"]:
                if b.get("type") == "text":
                    content.append({"type": "text", "text": b.get("text", "")})
                elif b.get("type") == "thinking" and b.get("thinking"):  # print mode often omits the text
                    content.append({"type": "thinking", "thinking": b["thinking"]})
                elif b.get("type") == "tool_use":
                    content.append(_tool_call(b, cwd))
            entries.append(_stamp({"type": "message", "message": {
                "role": "assistant", "content": content, "usage": _pi_usage(msg.get("usage") or {}),
                "stopReason": msg.get("stop_reason"),
            }}, e.get("timestamp")))
        elif e.get("type") == "user":
            for b in (e.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_result":
                    entries.append(_stamp({"type": "message", "message": {
                        "role": "toolResult", "toolCallId": b.get("tool_use_id"),
                        "content": _tool_content(b.get("content")), "isError": bool(b.get("is_error")),
                    }}, e.get("timestamp")))
                    _set_duration(entries[-1]["message"], called.get(b.get("tool_use_id")), e.get("timestamp"))
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if result and result.get("is_error"):
        entries.append({"type": "message", "message": {
            "role": "assistant", "content": [{"type": "text", "text": _result_error(result)}], "stopReason": "error",
        }})
    return entries


def _stamp(entry, timestamp):
    """Adds pi's `timestamp` field to a session entry when the stream event had one."""
    if timestamp:
        entry["timestamp"] = timestamp
    return entry


def _result_error(result):
    return str(result.get("result") or ", ".join(result.get("errors") or []) or result.get("subtype") or "error")


def claude_metrics(events, level=None):
    """Metrics from a Claude Code stream (parse_session()'s shape). Turns and tool calls are counted
    over the top-level assistant API messages. Tokens come from the final result's usage (the
    per-message usage in the stream is a snapshot taken before the output is written, so it
    undercounts output); until the run ends they're summed from those snapshots. Reasoning =
    usage.output_tokens_details.thinking_tokens. Cost = total_cost_usd (Claude Code's API-price
    estimate), 0 until the run ends."""
    msgs = _claude_messages(events)
    tool_calls = sum(1 for m in msgs for b in m["content"] if b.get("type") == "tool_use")
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if result and result.get("usage"):
        u = _pi_usage(result["usage"])
        reasoning = (result["usage"].get("output_tokens_details") or {}).get("thinking_tokens")
        if reasoning is None:
            reasoning = result["usage"].get("reasoning_tokens")
    else:
        u = {k: sum(_pi_usage(m.get("usage") or {})[k] for m in msgs) for k in ("input", "output", "cacheRead", "cacheWrite")}
        reasoning = None
    tokens = {"input": u["input"], "output": u["output"], "reasoning": reasoning, "cacheRead": u["cacheRead"], "cacheWrite": u["cacheWrite"]}
    tokens["total"] = tokens["input"] + tokens["output"]
    ended_in_error = bool(result and result.get("is_error"))
    return {
        "thinking_level": level,
        "turns": len(msgs),
        "tool_calls": tool_calls,
        "tokens": tokens,
        "cost_usd": (result or {}).get("total_cost_usd") or 0.0,
        "ended_in_error": ended_in_error,
        "error_message": _result_error(result)[:200] if ended_in_error else None,
    }


class Agy(Harness):
    """Antigravity's headless NDJSON stream. Model slugs include the effort tier.

    agy reads MCP servers only from the user's global config, so a run's servers go through the permanent
    `art-crit-<name>` proxy entries there (`install_proxy_entries`) and the run's harness/art-crit-mcp.json."""

    name = "agy"
    tag = "agy"
    supports_mcp = True
    MCP_CONFIG = Path.home() / ".gemini" / "config" / "mcp_config.json"

    def __init__(self, binary="agy"):
        self.binary = binary

    def version(self):
        try:
            r = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} --version: {e}")
        if r.returncode:
            raise CritError(f"{self.binary} --version failed: {r.stderr.strip()}")
        return r.stdout.strip().splitlines()[0]

    def _slugs(self):
        try:
            r = subprocess.run([self.binary, "models"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} models: {e}")
        if r.returncode:
            raise CritError(f"{self.binary} models failed: {r.stderr.strip()}")
        return [line.split()[0] for line in r.stdout.splitlines()
                if line.split() and re.search(r"-(?:low|medium|high|xhigh|max)$", line.split()[0])]

    def models(self):
        return list(dict.fromkeys(re.sub(r"-(?:low|medium|high|xhigh|max)$", "", s) for s in self._slugs()))

    def levels(self, model):
        slugs = set(self._slugs())
        return [level for level in LEVEL_ORDER if f"{model}-{level}" in slugs]

    def display_model(self, model):
        if "/" in model:
            return model
        vendor = next((v for prefix, v in (("gemini-", "google"), ("claude-", "anthropic"),
                                            ("gpt-oss-", "openai")) if model.startswith(prefix)), "antigravity")
        return f"{vendor}/{model}"

    def command(self, model, level, brief, session_dir, mcp=None):
        cmd = [self.binary, "-p", brief, "--model", f"{model}-{level}",
               "--output-format", "stream-json", "--dangerously-skip-permissions",
               "--disable-slash-commands"]
        if not mcp:
            return cmd
        # A tool is declared up front only when named in `tools` with eager (a "*" key doesn't work, measured): otherwise
        # the model gets a file to read for each tool's schema first.
        install_proxy_entries(self.MCP_CONFIG, mcp, session_dir, lambda spec: {
            "timeoutSeconds": MCP_TIMEOUT_S, "tools": {t: {"eager": True} for t in spec.get("tools", ())}})
        return cmd

    def session_file(self, session_dir):
        path = Path(session_dir) / "events.jsonl"
        return path if path.is_file() else None

    def session_entries(self, session_dir, brief, level):
        path = self.session_file(session_dir)
        return convert_agy_stream(read_jsonl(path), brief, level) if path else None

    def metrics(self, session_dir, level=None):
        path = self.session_file(session_dir)
        return agy_metrics(read_jsonl(path), level) if path else None


class GrokBuild(Harness):
    """Grok Build's Messages-compatible headless stream (not Grok's ACP delta stream). A run's MCP servers go in
    the project config work/.grok/config.toml (never published as source), through the proxy. Grok's models reach MCP
    tools only through its search_tool/use_tool meta-tools, never as declared tools."""

    name = "grok-build"
    tag = "gb"
    supports_mcp = True
    # Grok's `models` command lists ids but not supported effort levels. Mirrors its current
    # model menus; update when the CLI's catalog changes (an unsupported tier can be ignored).
    MODELS = {"grok-4.7": ["low", "medium", "high", "xhigh"],
              "grok-4.7-build-fast": ["low", "medium", "high", "xhigh"],
              "grok-4.6": ["low", "medium", "high", "xhigh"],
              "grok-4.5": ["low", "medium", "high"]}

    def __init__(self, binary="grok"):
        self.binary = binary

    def version(self):
        try:
            r = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} --version: {e}")
        if r.returncode:
            raise CritError(f"{self.binary} --version failed: {r.stderr.strip()}")
        return r.stdout.strip().split()[1]  # grok 1.0.50 (...) [stable]

    def models(self):
        try:
            r = subprocess.run([self.binary, "models"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} models: {e}")
        if r.returncode:
            raise CritError(f"{self.binary} models failed: {r.stderr.strip()}")
        return [m for m in self.MODELS if re.search(rf"(?m)^\s*[-*]\s+{re.escape(m)}(?:\s|$)", r.stdout)]

    def levels(self, model):
        return self.MODELS[model]

    def display_model(self, model):
        return f"xai/{model}"

    BUILTIN_TOOLS = ("run_terminal_cmd", "read_file", "write_file", "search_replace", "grep", "list_dir")

    def command(self, model, level, brief, session_dir, mcp=None):
        cmd = [self.binary, "-p", brief, "--model", model, "--reasoning-effort", level,
               "--output-format", "streaming-messages-json", "--always-approve", "--verbatim",
               "--tools", ",".join(self.BUILTIN_TOOLS),
               "--disallowed-tools", "Agent", "--disable-web-search", "--no-subagents"]
        if not mcp:
            return cmd
        # --tools above allows built-in tools only; MCP tools come from the project config, which grok starts only in
        # a trusted folder. GROK_FOLDER_TRUST=0 lifts that gate for this process (--trust would record every run dir
        # in ~/.grok/trusted_folders.toml); the work dir is fresh, so it holds nothing else to trust.
        config = Path(session_dir).parent / "work" / ".grok" / "config.toml"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(grok_mcp_toml(mcp, install_proxy(mcp, session_dir)))
        return ["env", "GROK_FOLDER_TRUST=0", *cmd]

    def session_file(self, session_dir):
        path = Path(session_dir) / "events.jsonl"
        return path if path.is_file() else None

    def session_entries(self, session_dir, brief, level):
        path = self.session_file(session_dir)
        return convert_claude_stream(read_jsonl(path), brief, level) if path else None

    def metrics(self, session_dir, level=None):
        path = self.session_file(session_dir)
        if not path:
            return None
        events = read_jsonl(path)
        metrics = claude_metrics(events, level)
        if not any(e.get("type") == "result" for e in events):
            metrics.update(ended_in_error=True, error_message="no final result from grok")
        return metrics


class MuseCode(Harness):
    """Meta's Muse Code (`muse exec`). Its `--json` stdout is a thin live event stream (no tool calls
    or usage), so each run exports its durable session log when the agent exits and that export is
    the session (`export.json`). Known models get an API-equivalent cost estimate at finish."""

    name = "muse-code"
    tag = "mc"
    supports_mcp = True  # through the permanent art-crit-<name> proxy entries in the user's settings (see Agy)
    MCP_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "muse" / "settings.json"
    # `muse` has no command that lists models, but it caches the provider's catalog (with each model's effort
    # tiers) in CATALOG_DIR whenever its TUI fetches it (opening /model), and that is the source. MODELS is the
    # fallback when there is no cache yet; update it when the CLI changes.
    CATALOG_DIR = Path.home() / ".local" / "share" / "muse" / "model-catalog"
    # USD per million tokens (uncached input, cached input, output). Meta Model API:
    # https://dev.meta.ai/docs/pricing-rate-limits (update when published prices change).
    # Full and Wonder Contributor have no API prices. Use Wonder Standard as a *labeled proxy*.
    API_PRICES = {"muse-wonder-1.0": (4.00, 0.20, 20.00),
                  "muse-spark-1.3": (1.25, 0.15, 4.25),
                  "muse-spark-1.2": (1.25, 0.15, 4.25),
                  "muse-spark-1.3-contributor": (0.10, 0.002, 0.20),
                  "muse-spark-1.2-contributor": (0.10, 0.002, 0.20)}
    PRICE_PROXIES = {"muse-wonder-full-1.0": "muse-wonder-1.0",
                     "muse-wonder-full-1.0-contributor": "muse-wonder-1.0",
                     "muse-wonder-1.0-contributor": "muse-wonder-1.0"}
    MODELS = {"muse-wonder-1.0": ["minimal", "low", "medium", "high", "xhigh", "max"],
              "muse-wonder-1.0-contributor": ["minimal", "low", "medium", "high", "xhigh", "max"],
              "muse-wonder-full-1.0": ["minimal", "low", "medium", "high", "xhigh", "max"],
              "muse-wonder-full-1.0-contributor": ["minimal", "low", "medium", "high", "xhigh", "max"],
              "muse-spark-1.3": ["minimal", "low", "medium", "high", "xhigh", "max"],
              "muse-spark-1.3-contributor": ["minimal", "low", "medium", "high", "xhigh", "max"],
              "muse-spark-1.2": ["minimal", "low", "medium", "high", "xhigh"]}
    # Export even when the agent failed. $1 = muse, $2 = session id, $3 = export path, then `exec` args.
    WRAPPER = '"$1" exec "${@:4}"; code=$?; "$1" export --session "$2" --out "$3" >/dev/null 2>&1; exit $code'

    def __init__(self, binary="muse"):
        self.binary = binary

    def version(self):
        try:
            r = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} --version: {e}")
        if r.returncode:
            raise CritError(f"{self.binary} --version failed: {r.stderr.strip()}")
        return r.stdout.split()[2]  # Muse Code 1.4.6 (1.4.6-R6000.1)

    def catalog(self):
        """{model id: effort levels in LEVEL_ORDER} from muse's cached catalog (text models only, hidden
        ones such as the -contributor builds included), or MODELS when there's no usable cache."""
        found = {}
        for path in sorted(Path(self.CATALOG_DIR).glob("*.json")):
            try:
                rows = json.loads(path.read_text(encoding="utf-8")).get("rows") or []
            except (OSError, ValueError, AttributeError):
                continue
            for row in rows:
                tiers = {v.get("tier") for v in row.get("reasoning_effort_variants") or []}
                if row.get("model_id") and tiers:
                    found[row["model_id"]] = [level for level in LEVEL_ORDER if level in tiers]
        return found or self.MODELS

    def models(self):
        return list(self.catalog())

    def levels(self, model):
        return self.catalog()[model]

    def display_model(self, model):
        return f"meta/{model}"

    def command(self, model, level, brief, session_dir, mcp=None):
        # No approval prompts or sandbox (like the other harnesses); the workspace stays untrusted, which
        # also leaves delegation off. No web, reminder agents or other tools' rules/skills.
        # MCP servers: muse reads them only from the user's settings (a project .muse/settings.json is ignored, and
        # --trust-workspace would also turn on sub-agents), so they go through the proxy entries there.
        session_id = str(uuid.uuid4())
        cmd = ["bash", "-c", self.WRAPPER, "muse-code", self.binary, session_id, str(Path(session_dir) / "export.json"),
               "--json", "--session-id", session_id, "--model", model, "--reasoning-effort", level, "--disable-approval", "--disable-sandbox",
               "--disable-web-tools", "--disable-reminders", "--no-foreign-personal-context", "--", brief]
        if mcp:
            install_proxy_entries(self.MCP_CONFIG, mcp, session_dir, lambda spec: {"type": "stdio", "mode": "optional"})
        return cmd

    def session_file(self, session_dir):
        path = Path(session_dir) / "export.json"
        return path if path.is_file() else None

    def session_entries(self, session_dir, brief, level):
        path = self.session_file(session_dir)
        return convert_muse_export(_read_muse_export(path), brief, level) if path else None

    def metrics(self, session_dir, level=None):
        path = self.session_file(session_dir)
        return muse_metrics(_read_muse_export(path), level) if path else None

    def finish(self, harness_dir, model, metrics):
        model_id = model.removeprefix("meta/")
        proxy = self.PRICE_PROXIES.get(model_id)
        prices = self.API_PRICES.get(proxy or model_id)
        if prices and metrics.get("turns"):
            tokens = metrics["tokens"]
            # Muse's input_tokens includes both cache reads and writes. Writes are billed as
            # uncached input; reasoning_tokens is already part of output_tokens.
            uncached = tokens["input"] + tokens["cacheWrite"]
            metrics["cost_usd"] = round((uncached * prices[0] + tokens["cacheRead"] * prices[1]
                                         + tokens["output"] * prices[2]) / 1_000_000, 9)
            metrics["cost_estimated"] = True
            if proxy:
                metrics["cost_estimate_proxy"] = f"meta/{proxy}"
        return metrics


def _read_muse_export(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _muse_events(doc):
    """(record, event) for the top-level run's events in a `muse export`, in order. Reminder and other
    background runs are left out: only runs marked `top_level_turn.run_origin` count, or all when none is."""
    records = [e["envelope"] for e in doc.get("events") or [] if e.get("kind") == "record" and e.get("envelope")]
    top = {r["payload"].get("run_id") for r in records if r.get("payload_type") == "runtime.retained_fact"
           and (r["payload"].get("record") or {}).get("payload_type") == "top_level_turn.run_origin"}
    return [(r, r["payload"]["event"]) for r in records if r.get("payload_type") == "runtime.session"
            and r["payload"].get("kind") == "run" and (not top or r["payload"].get("run_id") in top)]


def _muse_usage(u):
    """Muse's input_tokens includes cached ones; pi's `input` doesn't."""
    cache_read, cache_write = u.get("cache_read_tokens") or 0, u.get("cache_write_tokens") or 0
    usage = {"input": max(0, (u.get("input_tokens") or 0) - cache_read - cache_write), "output": u.get("output_tokens") or 0,
             "cacheRead": cache_read, "cacheWrite": cache_write}
    usage["totalTokens"] = sum(usage.values())
    return usage


def muse_metrics(doc, level=None):
    """Metrics from a `muse export` (parse_session()'s shape): turns = model calls, tokens summed over
    their usage, cost unreported (0). Failed = the run's terminal event is missing or not `completed`."""
    events = [ev for _, ev in _muse_events(doc)]
    calls = [ev for ev in events if ev.get("kind") == "model_completed"]
    usage = [_muse_usage(ev.get("usage") or {}) for ev in calls]
    tokens = {k: sum(u[k] for u in usage) for k in ("input", "output", "cacheRead", "cacheWrite")}
    tokens["reasoning"] = sum((ev.get("usage") or {}).get("reasoning_tokens") or 0 for ev in calls)
    tokens["total"] = tokens["input"] + tokens["output"]
    terminal = next((ev for ev in reversed(events) if ev.get("kind") == "terminal"), None)
    failed = terminal is None or terminal.get("terminal") != "completed"
    return {
        "thinking_level": level,
        "turns": len(calls),
        "tool_calls": sum(len(ev.get("tool_calls") or []) for ev in events if ev.get("kind") == "assistant_tool_calls_committed"),
        "tokens": tokens,
        "cost_usd": 0.0,
        "ended_in_error": failed,
        "error_message": (str((terminal or {}).get("reason") or (terminal or {}).get("terminal") or "no final result from muse"))[:200] if failed else None,
    }


def _muse_tool_call(call, cwd):
    """A muse tool call -> a pi toolCall (bash, write, edit, read get pi's names and argument shapes)."""
    try:
        args = json.loads(call.get("args") or "{}")
    except ValueError:
        args = {}
    name = call.get("name", "")

    def rel(path):
        return path[len(cwd) + 1:] if cwd and isinstance(path, str) and path.startswith(cwd + "/") else path

    if name == "bash":
        name, args = "bash", {"command": args.get("command", "")}
    elif name == "write_file":
        name, args = "write", {"path": rel(args.get("path")), "content": args.get("content", "")}
    elif name == "edit_file":
        name, args = "edit", {"path": rel(args.get("path")), "edits": [{"oldText": args.get("find", ""), "newText": args.get("replace", "")}]}
    elif name == "read_file":
        name, args = "read", {"path": rel(args.get("path")), **{k: v for k, v in args.items() if k in ("offset", "limit")}}
    elif name.startswith("mcp__art_crit_"):  # the proxy entry art-crit-<server> -> mcp__<server>__<tool>, like the others
        name = "mcp__" + name.removeprefix("mcp__art_crit_")
    return {"type": "toolCall", "id": call.get("call_id") or call.get("id"), "name": name, "arguments": args}


def _iso(microseconds):
    return datetime.fromtimestamp(microseconds / 1e6, timezone.utc).isoformat().replace("+00:00", "Z")


def convert_muse_export(doc, brief, level):
    """A `muse export` -> pi-format session entries (see SPEC.md "Harness interface"). One assistant message
    per model call (thinking, text and tool calls, with the call's usage), flushed when its tool results
    arrive or the run ends; tool durations are exact (the tool effect's start and end)."""
    records = [e["envelope"] for e in doc.get("events") or [] if e.get("kind") == "record" and e.get("envelope")]
    cwd = next(((r["payload"].get("record") or {}).get("workspace_root", "") for r in records if r.get("payload_type") == "runtime.session.metadata"), "")
    effects = {}  # call id -> [start, end] (microseconds)
    for r in records:
        rec = r.get("payload", {}).get("record") or {}
        if r.get("payload_type") in ("tool_batch.effect.started", "tool_batch.effect.terminal") and rec.get("call_id"):
            effects.setdefault(rec["call_id"], {})["start" if rec["kind"] == "started" else "end"] = r["recorded_at"]
    events = _muse_events(doc)
    model = next((ev.get("model") for _, ev in events if ev.get("kind") == "model_completed"), None)
    start = {"timestamp": _iso(events[0][0]["recorded_at"])} if events else {}
    entries = [{"type": "session", "cwd": cwd, **start}, {"type": "model_change", "provider": "meta", "modelId": model},
               {"type": "thinking_level_change", "thinkingLevel": level},
               {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": brief}]}, **start}]
    pending = {"content": [], "usage": None}
    stamp = [None]

    def flush():
        if pending["content"]:
            message = {"role": "assistant", "content": pending["content"], "usage": pending["usage"] or _muse_usage({}),
                       "stopReason": "toolUse" if any(b["type"] == "toolCall" for b in pending["content"]) else "stop"}
            entries.append(_stamp({"type": "message", "message": message}, stamp[0]))
        pending.update(content=[], usage=None)

    for record, ev in events:
        kind, when = ev.get("kind"), _iso(record["recorded_at"])
        if kind == "reasoning_committed" and ev.get("text"):
            pending["content"].append({"type": "thinking", "thinking": ev["text"]})
        elif kind == "assistant_message_committed":
            pending["content"].append({"type": "text", "text": ev.get("text", "")})
        elif kind == "assistant_tool_calls_committed":
            pending["content"] += [_muse_tool_call(c, cwd) for c in ev.get("tool_calls") or []]
        elif kind == "model_completed":
            pending["usage"] = _muse_usage(ev.get("usage") or {})
        elif kind == "tool_result_batch_committed":
            flush()
            for result in ev.get("results") or []:
                message = {"role": "toolResult", "toolCallId": result.get("tool_call_id"),
                           "content": [{"type": "text", "text": result.get("text", "")}], "isError": False}
                span = effects.get(result.get("tool_call_id")) or {}
                if "start" in span and "end" in span:
                    message["durationMs"] = max(0, round((span["end"] - span["start"]) / 1000))
                entries.append(_stamp({"type": "message", "message": message}, when))
        elif kind == "terminal":
            flush()
            if ev.get("terminal") != "completed":
                entries.append(_stamp({"type": "message", "message": {"role": "assistant", "content": [
                    {"type": "text", "text": str(ev.get("reason") or ev.get("terminal"))}], "stopReason": "error"}}, when))
        stamp[0] = when
    flush()
    return entries


def _agy_result(events):
    return next((e.get("result") or {} for e in reversed(events) if e.get("event") == "result"), {})


def agy_metrics(events, level=None):
    result = _agy_result(events)
    u = result.get("usage") or {}
    steps = {s.get("step_index") for e in events if e.get("event") == "step_update"
             for s in [e.get("step_update") or {}] if s.get("step_type") == "tool"}
    tokens = {"input": u.get("input_tokens") or 0, "output": u.get("output_tokens") or 0,
              "reasoning": u.get("thinking_tokens") or 0, "cacheRead": u.get("cache_read_tokens") or 0,
              "cacheWrite": 0}
    tokens["total"] = tokens["input"] + tokens["output"]
    status = result.get("status")
    return {"thinking_level": level, "turns": result.get("num_turns") or 0,
            "tool_calls": len(steps), "tokens": tokens, "cost_usd": 0.0,
            "ended_in_error": status != "SUCCESS",
            "error_message": str(result.get("error") or status or "no final result from agy")[:200] if status != "SUCCESS" else None}


def convert_agy_stream(events, brief, level):
    """Keep completed tool steps once, append streamed response deltas once (ACTIVE and DONE)."""
    init = next((e.get("init") or {} for e in events if e.get("event") == "init"), {})
    entries = [{"type": "session", "cwd": init.get("cwd", "")},
               {"type": "model_change", "provider": "antigravity", "modelId": init.get("model")},
               {"type": "thinking_level_change", "thinkingLevel": level},
               {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": brief}]}}]
    seen_tools = set()
    texts = {}  # agent_response step_index -> its one text block; the ACTIVE deltas and the DONE remainder join into it
    for e in events:
        if e.get("event") != "step_update":
            continue
        s = e.get("step_update") or {}
        if s.get("step_type") == "agent_response" and s.get("text_delta"):
            block = texts.get(s.get("step_index"))
            if block is None:  # one assistant message per response, not per streamed delta (each would be its own turn)
                block = texts[s.get("step_index")] = {"type": "text", "text": ""}
                entries.append({"type": "message", "message": {"role": "assistant", "content": [block]}})
            block["text"] += s["text_delta"]
        if s.get("step_type") != "tool" or s.get("state") != "DONE" or s.get("step_index") in seen_tools:
            continue
        seen_tools.add(s.get("step_index"))
        info = s.get("tool_info") or {}
        name = info.get("name") or s.get("tool_name") or "tool"
        args = info.get("parameters") or {}
        if name == "run_command":
            call = {"type": "toolCall", "id": f"agy-{s.get('step_index')}", "name": "bash",
                    "arguments": {"command": args.get("CommandLine", "")}}
        elif name == "call_mcp_tool":  # agy's generic MCP call -> the mcp__<server>__<tool> name the other harnesses use
            server = str(args.get("ServerName", "")).removeprefix("art-crit-")
            call = {"type": "toolCall", "id": f"agy-{s.get('step_index')}", "name": f"mcp__{server}__{args.get('ToolName', '')}",
                    "arguments": args.get("Arguments") or {}}
        elif m := re.fullmatch(r"mcp_art-crit-([A-Za-z0-9-]+)_(.+)", name):  # an eagerly declared MCP tool
            call = {"type": "toolCall", "id": f"agy-{s.get('step_index')}", "name": f"mcp__{m[1]}__{m[2]}", "arguments": args}
        else:
            call = {"type": "toolCall", "id": f"agy-{s.get('step_index')}", "name": name, "arguments": args}
        entries.append({"type": "message", "message": {"role": "assistant", "content": [call]}})
        output = info.get("output")
        result_msg = {"role": "toolResult", "toolCallId": call["id"],
                      "content": [{"type": "text", "text": output if isinstance(output, str) else
                                   json.dumps(output if output is not None else info.get("error") or "")}],
                      "isError": bool(info.get("error"))}
        if isinstance(s.get("duration_seconds"), (int, float)):
            result_msg["durationMs"] = round(s["duration_seconds"] * 1000)
        entries.append({"type": "message", "message": result_msg})
    result = _agy_result(events)
    if not any(e.get("message", {}).get("role") == "assistant" and
               any(b.get("type") == "text" for b in e["message"].get("content", [])) for e in entries) and result.get("response"):
        entries.append({"type": "message", "message": {"role": "assistant", "content":
                        [{"type": "text", "text": result["response"]}]}})
    if result.get("status") and result["status"] != "SUCCESS":
        entries.append({"type": "message", "message": {"role": "assistant", "content":
                        [{"type": "text", "text": str(result.get("error") or result["status"])}], "stopReason": "error"}})
    return entries


class Codex(Harness):
    """OpenAI's Codex CLI (`codex exec --json`). The stdout JSONL stream is the session; models and
    effort levels come from `codex debug models`. Cost is not reported (0 = unreported)."""

    name = "codex"
    supports_mcp = True
    tag = "cx"
    TOOL_ITEMS = ("command_execution", "file_change", "mcp_tool_call", "collab_tool_call", "web_search")

    def __init__(self, binary="codex"):
        self.binary = binary
        self._catalog = None

    def version(self):
        try:
            r = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} --version: {e}")
        if r.returncode:
            raise CritError(f"{self.binary} --version failed: {r.stderr.strip()}")
        parts = r.stdout.strip().split()
        return parts[1] if len(parts) > 1 else parts[0]  # codex-cli 0.162.1

    def catalog(self):
        """{model slug: effort levels in LEVEL_ORDER} from `codex debug models` (listed models only;
        `ultra` isn't in LEVEL_ORDER, so it's dropped). Cached per instance: planning asks often."""
        if self._catalog is None:
            try:
                r = subprocess.run([self.binary, "debug", "models"], capture_output=True, text=True, timeout=30)
            except (OSError, subprocess.TimeoutExpired) as e:
                raise CritError(f"cannot run {self.binary} debug models: {e}")
            if r.returncode:
                raise CritError(f"{self.binary} debug models failed: {r.stderr.strip()}")
            try:
                rows = json.loads(r.stdout).get("models") or []
            except (ValueError, AttributeError):
                rows = []
            found = {}
            for row in rows:
                tiers = {v.get("effort") for v in row.get("supported_reasoning_levels") or [] if isinstance(v, dict)}
                levels = [level for level in LEVEL_ORDER if level in tiers]
                if row.get("slug") and levels and row.get("visibility") in (None, "list"):
                    found[row["slug"]] = levels
            self._catalog = found
        return self._catalog

    def models(self):
        return list(self.catalog())

    def levels(self, model):
        return self.catalog()[model]

    def display_model(self, model):
        return f"openai/{model}"

    def command(self, model, level, brief, session_dir, mcp=None):
        # No approvals or sandbox (like the other harnesses); user config and execpolicy rules are
        # left out for reproducibility, the session isn't persisted (events.jsonl is the session).
        return [self.binary, "exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules",
                "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
                "-m", model, "-c", f'model_reasoning_effort="{level}"', *codex_mcp_args(mcp), brief]

    def session_file(self, session_dir):
        path = Path(session_dir) / "events.jsonl"
        return path if path.is_file() else None

    def session_entries(self, session_dir, brief, level):
        path = self.session_file(session_dir)
        return convert_codex_stream(read_jsonl(path), brief, level) if path else None

    def metrics(self, session_dir, level=None):
        path = self.session_file(session_dir)
        return codex_metrics(read_jsonl(path), level) if path else None


def _codex_usage(u):
    """Codex's input_tokens includes cached ones; pi's `input` doesn't."""
    cache_read = u.get("cached_input_tokens") or 0
    cache_write = u.get("cache_write_input_tokens") or 0
    usage = {"input": max(0, (u.get("input_tokens") or 0) - cache_read - cache_write),
             "output": u.get("output_tokens") or 0, "cacheRead": cache_read, "cacheWrite": cache_write}
    usage["totalTokens"] = sum(usage.values())
    return usage


def codex_metrics(events, level=None):
    """Metrics from a codex exec stream (parse_session()'s shape): tokens summed over each
    `turn.completed` usage, turns = turns started, cost unreported (0). Failed = a `turn.failed`/
    `error` event, or no completed turn at all."""
    done = [e for e in events if e.get("type") == "turn.completed"]
    failed = next((e for e in events if e.get("type") in ("turn.failed", "error")), None)
    usage = [_codex_usage(e.get("usage") or {}) for e in done]
    tokens = {k: sum(u[k] for u in usage) for k in ("input", "output", "cacheRead", "cacheWrite")}
    tokens["reasoning"] = sum((e.get("usage") or {}).get("reasoning_output_tokens") or 0 for e in done)
    tokens["total"] = tokens["input"] + tokens["output"]
    error = None
    if failed:
        error = str(((failed.get("error") or {}).get("message") or failed.get("message") or "codex error"))[:200]
    elif not done:
        error = "no final result from codex"
    return {
        "thinking_level": level,
        "turns": max(sum(1 for e in events if e.get("type") == "turn.started"), len(done)),
        "tool_calls": sum(1 for e in events if e.get("type") == "item.completed"
                          and (e.get("item") or {}).get("type") in Codex.TOOL_ITEMS),
        "tokens": tokens,
        "cost_usd": 0.0,
        "ended_in_error": bool(failed) or not done,
        "error_message": error,
    }


def _codex_tool(item):
    """A completed codex tool item -> (pi toolCall, toolResult text, isError)."""
    kind, item_id = item.get("type"), item.get("id")
    status = item.get("status")
    if kind == "command_execution":
        call = {"type": "toolCall", "id": item_id, "name": "bash", "arguments": {"command": item.get("command", "")}}
        return call, item.get("aggregated_output") or "", status != "completed" or (item.get("exit_code") or 0) != 0
    if kind == "file_change":
        call = {"type": "toolCall", "id": item_id, "name": "file_change", "arguments": {"changes": item.get("changes") or []}}
        return call, f"{status}: " + ", ".join(f"{c.get('kind')} {c.get('path')}" for c in item.get("changes") or []), status != "completed"
    if kind == "mcp_tool_call":
        call = {"type": "toolCall", "id": item_id, "name": f"mcp__{item['server']}__{item['tool']}" if item.get("server") and item.get("tool") else item.get("tool") or "mcp_tool",
                "arguments": item.get("arguments") if isinstance(item.get("arguments"), dict) else {"arguments": item.get("arguments")}}
        err = (item.get("error") or {}).get("message")
        result = item.get("result") or {}
        texts = [c.get("text", "") for c in result.get("content") or [] if isinstance(c, dict)]
        text = err or "\n".join(t for t in texts if t) or json.dumps(result.get("structured_content") or "")
        return call, text, status != "completed" or bool(err)
    args = {"query": item.get("query")} if kind == "web_search" else {
        k: item[k] for k in ("tool", "prompt", "receiver_thread_ids") if k in item}
    call = {"type": "toolCall", "id": item_id, "name": item.get("tool") or kind, "arguments": args}
    return call, json.dumps({k: v for k, v in item.items() if k not in ("id", "type")}), status == "failed"


def convert_codex_stream(events, brief, level):
    """A `codex exec --json` stream -> pi-format session entries (see SPEC.md "Harness interface").
    Only `item.completed` items count (started/updated are the same item in flight); a tool item
    becomes one assistant toolCall plus its toolResult. The stream carries no timestamps or model id."""
    entries = [{"type": "session", "cwd": ""}, {"type": "model_change", "provider": "openai", "modelId": None},
               {"type": "thinking_level_change", "thinkingLevel": level},
               {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": brief}]}}]
    pending = []

    def flush(usage=None):
        if pending:
            entries.append({"type": "message", "message": {
                "role": "assistant", "content": list(pending), "usage": usage or _codex_usage({}),
                "stopReason": "toolUse" if any(b["type"] == "toolCall" for b in pending) else "stop"}})
            pending.clear()

    for e in events:
        kind = e.get("type")
        if kind == "item.completed":
            item = e.get("item") or {}
            itype = item.get("type")
            if itype == "reasoning" and item.get("text"):
                pending.append({"type": "thinking", "thinking": item["text"]})
            elif itype == "agent_message" and item.get("text"):
                pending.append({"type": "text", "text": item["text"]})
            elif itype in Codex.TOOL_ITEMS:
                call, text, is_error = _codex_tool(item)
                pending.append(call)
                flush()
                entries.append({"type": "message", "message": {"role": "toolResult", "toolCallId": call["id"],
                                "content": [{"type": "text", "text": text}], "isError": is_error}})
            elif itype == "error":
                flush()
                entries.append({"type": "message", "message": {"role": "assistant", "content": [
                    {"type": "text", "text": str(item.get("message") or "error")}], "stopReason": "error"}})
        elif kind == "turn.completed":
            flush(_codex_usage(e.get("usage") or {}))
        elif kind in ("turn.failed", "error"):
            flush()
            message = (e.get("error") or {}).get("message") or e.get("message") or "codex error"
            entries.append({"type": "message", "message": {"role": "assistant", "content": [
                {"type": "text", "text": str(message)}], "stopReason": "error"}})
    flush()
    return entries


def fetch_json(url, timeout=30):
    """GET `url` and parse its JSON body: the one place art-crit reads the network, Ori's model catalog
    (tests replace it, so no test ever reaches out)."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


class Ori(Harness):
    """OpenRouter's Ori CLI (`ori code -p ... --output jsonl`): Ori's own runtime agent, one headless turn.
    The stdout JSONL stream is the session; the models are OpenRouter's (their public catalog, which is
    what Ori runs), and each turn reports OpenRouter's own usage, cost included."""

    name = "ori"
    supports_mcp = True  # work/.ori/mcp.json, which Ori merges for this run only (see write_ori_mcp_config)
    tag = "ori"
    # OpenRouter's public model list (no credential needed): the same catalog Ori resolves `--model` against.
    CATALOG_URL = "https://openrouter.ai/api/v1/models"
    # Ori takes these; a model advertising `reasoning_effort` takes all of them, and `off` is Ori's "none".
    MODEL_LEVELS = [level for level in LEVEL_ORDER if level != "off"]

    def __init__(self, binary="ori"):
        self.binary = binary
        self._catalog = None

    def version(self):
        try:
            r = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CritError(f"cannot run {self.binary} --version: {e}")
        if r.returncode != 0:
            raise CritError(f"{self.binary} --version failed: {r.stderr.strip()}")
        text = r.stdout.strip()
        try:  # piped, ori answers a JSON envelope; on a terminal it prints "ori 0.16.0-alpha+... Run ..."
            return str((json.loads(text).get("data") or {}).get("version") or text.split()[1])
        except (ValueError, IndexError, AttributeError):
            parts = text.split()
            return parts[1] if len(parts) > 1 and parts[0] == "ori" else text

    def openrouter_catalog(self):
        """OpenRouter's model rows, live (tests install their own: see `fetch_json`)."""
        try:
            return (fetch_json(self.CATALOG_URL) or {}).get("data") or []
        except (OSError, ValueError, AttributeError) as e:
            raise CritError(f"cannot read OpenRouter's model list ({self.CATALOG_URL}): {e}")

    def catalog(self):
        """{model id: effort levels in LEVEL_ORDER} over the text-output models of OpenRouter's catalog
        (image/video models can't drive an agent). A model that advertises `reasoning_effort` gets the
        whole ladder; one without it gets `off` only, like a non-reasoning model under pi. Cached per
        instance: planning asks often."""
        if self._catalog is None:
            found = {}
            for row in self.openrouter_catalog():
                params = set(row.get("supported_parameters") or [])
                outputs = (row.get("architecture") or {}).get("output_modalities") or []
                if row.get("id") and "text" in outputs:
                    found[row["id"]] = ["off", *self.MODEL_LEVELS] if "reasoning_effort" in params else ["off"]
            self._catalog = found
        return self._catalog

    def models(self):
        return list(self.catalog())

    def levels(self, model):
        return self.catalog()[model]

    def tools(self, mcp=None):
        """Ori takes MCP servers without a per-tool filter, so nothing is hidden: say so rather than
        recording the `hidden` names the harness can't enforce."""
        tools = super().tools(mcp)
        for server in tools["mcp"].values():
            server["hidden"] = []
        return tools

    def command(self, model, level, brief, session_dir, mcp=None):
        # --harness ori pins Ori's own runtime (the CLI's default harness is the user's to change), and
        # self-drive approves commands without asking, like the other harnesses run.
        if mcp:
            write_ori_mcp_config(Path(session_dir).parent / "work" / ".ori" / "mcp.json", mcp)  # Ori merges ./.ori/mcp.json
        return [self.binary, "code", "--harness", "ori", "--output", "jsonl", "--approvals", "self-drive",
                "--model", model, "--reasoning-effort", "none" if level == "off" else level, "-p", brief]

    def session_file(self, session_dir):
        path = Path(session_dir) / "events.jsonl"
        return path if path.is_file() else None

    def session_entries(self, session_dir, brief, level):
        path = self.session_file(session_dir)
        return convert_ori_stream(read_jsonl(path), brief, level) if path else None

    def metrics(self, session_dir, level=None):
        path = self.session_file(session_dir)
        return ori_metrics(read_jsonl(path), level) if path else None


def write_ori_mcp_config(path, mcp):
    """A run's MCP servers as the `mcpServers` JSON Ori reads from a workspace's .ori/mcp.json: unlike pi's
    and Claude Code's, each server needs `type: "stdio"`. Ori also holds no per-server tool filter."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    servers = {name: {"type": "stdio", "command": spec["command"], "args": list(spec.get("args", ())),
                      **({"env": dict(spec["env"])} if spec.get("env") else {})}
               for name, spec in (mcp or {}).items()}
    path.write_text(json.dumps({"mcpServers": servers}, indent=2) + "\n")
    return path


def ori_runtime_events(lines):
    """The agent events of an `ori code --output jsonl` stream. Each line is {kind, event}; a runtime event's
    `event` is a `runtime.event` wrapping the agent's own event, and audit events aren't part of the session.
    A line that already holds an agent event (`{type, payload}`) is accepted as it is."""
    events = []
    for line in lines:
        event = line.get("event") if isinstance(line, dict) else None
        if not isinstance(event, dict):
            continue
        if event.get("type") == "runtime.event":
            event = event.get("event")
        if isinstance(event, dict) and isinstance(event.get("type"), str):
            events.append(event)
    return events


def ori_result(lines):
    """The stream's closing `{kind: "result", ok, sessionId, error}` line, which Ori exits non-zero on."""
    return next((line for line in lines if isinstance(line, dict) and line.get("kind") == "result"), None)


def _ori_payload(event):
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def _ori_usage(u):
    """OpenRouter's usage (its input tokens include the cached ones; pi's `input` doesn't)."""
    cache_read = u.get("cacheReadTokens") or 0
    cache_write = u.get("cacheCreationTokens") or 0
    usage = {"input": max(0, (u.get("inputTokens") or 0) - cache_read - cache_write),
             "output": u.get("outputTokens") or 0, "cacheRead": cache_read, "cacheWrite": cache_write}
    usage["totalTokens"] = sum(usage.values())
    return usage


def ori_metrics(lines, level=None):
    """Metrics from an ori jsonl stream (parse_session()'s shape): tokens and cost come from the turn
    results, which carry OpenRouter's own numbers (cost is what it charged, like a pi OpenRouter run), and
    ori reports no reasoning tokens. Failed = a failed turn or session, a result line that says so, or no
    turn that ever settled."""
    events = ori_runtime_events(lines)
    result = ori_result(lines) or {}
    terminal = [event for event in events if event.get("type") in ("turn.succeeded", "turn.failed")]
    usage = [_ori_usage(p.get("usage") or {}) for p in map(_ori_payload, terminal) if p.get("usage")]
    tokens = {key: sum(u[key] for u in usage) for key in ("input", "output", "cacheRead", "cacheWrite")}
    tokens["reasoning"] = 0  # ori reports none
    tokens["total"] = tokens["input"] + tokens["output"]
    failed = [event for event in events if event.get("type") in ("turn.failed", "session.failed")]
    error = None
    if failed:
        error = (_ori_payload(failed[0]).get("failure") or {}).get("message") or "ori error"
    elif result.get("ok") is False:
        error = (result.get("error") or {}).get("message") or "ori error"
    elif not terminal:
        error = "no final result from ori"
    return {
        "thinking_level": level,
        "turns": sum(1 for event in terminal if event.get("type") == "turn.succeeded"),
        "tool_calls": sum(1 for event in events if event.get("type") == "tool.started"),
        "tokens": tokens,
        "cost_usd": sum(p.get("usage", {}).get("costUsd") or 0 for p in map(_ori_payload, terminal)),
        "ended_in_error": bool(error),
        "error_message": str(error)[:200] if error else None,
    }


def _ori_tool_text(value):
    """A tool result (or a failed call's result) as text for the transcript."""
    if isinstance(value, str):
        return value
    return "" if value is None else json.dumps(value, ensure_ascii=False)


def convert_ori_stream(lines, brief, level):
    """An `ori code --output jsonl` stream -> pi-format session entries (see SPEC.md "Harness interface").
    Ori streams prose and reasoning as deltas, so a turn's deltas join into one assistant message; each
    `tool.started` plus its `tool.succeeded`/`tool.failed` becomes a toolCall block and a toolResult message,
    and the event timestamps give the tool durations."""
    events = ori_runtime_events(lines)
    result = ori_result(lines) or {}
    entries = [{"type": "session", "cwd": ""}, {"type": "model_change", "provider": "openrouter", "modelId": None},
               {"type": "thinking_level_change", "thinkingLevel": level},
               {"type": "message", "message": {"role": "user", "content": [{"type": "text", "text": brief}]}}]
    blocks, calls, usage, text, thinking = [], [], None, [], []
    last_at = None

    def push_block():
        if thinking:
            blocks.append({"type": "thinking", "thinking": "".join(thinking)})
            thinking.clear()
        if text:
            blocks.append({"type": "text", "text": "".join(text)})
            text.clear()

    def flush(stop="stop"):
        nonlocal blocks, calls, usage
        push_block()
        if not blocks and not calls:
            return
        entries.append({"type": "message", "timestamp": last_at, "message": {
            "role": "assistant", "content": [*blocks, *calls], "usage": usage or _ori_usage({}),
            "stopReason": "toolUse" if any(block["type"] == "toolCall" for block in calls) else stop}})
        blocks, calls, usage = [], [], None

    for event in events:
        kind, payload, at = event.get("type"), _ori_payload(event), event.get("createdAt")
        if kind in ("reasoning.delta", "assistant.text.delta", "tool.started"):
            last_at = at or last_at  # when the assistant said what the next flush records
        if kind == "reasoning.delta":
            if text:  # prose before reasoning starts is its own block
                push_block()
            thinking.append(str(payload.get("delta") or ""))
        elif kind == "assistant.text.delta":
            text.append(str(payload.get("delta") or ""))
        elif kind == "tool.started":
            arguments = payload.get("input")
            calls.append({"type": "toolCall", "id": payload.get("toolCallId"), "name": payload.get("name") or "tool",
                          "arguments": arguments if isinstance(arguments, dict) else {"input": arguments}})
        elif kind in ("tool.succeeded", "tool.failed"):
            call_id = payload.get("toolCallId") or next((call["id"] for call in calls if call["id"]), None)
            flush()
            failed = kind == "tool.failed"
            entries.append({"type": "message", "timestamp": at, "message": {
                "role": "toolResult", "toolCallId": call_id, "isError": failed,
                **({"durationMs": payload["durationMs"]} if isinstance(payload.get("durationMs"), (int, float)) else {}),
                "content": [{"type": "text", "text": _ori_tool_text(payload.get("result")) or (payload.get("code") or "")}]}})
        elif kind in ("turn.failed", "session.failed"):
            flush()
            message = (payload.get("failure") or {}).get("message") or "ori error"
            entries.append({"type": "message", "timestamp": at, "message": {
                "role": "assistant", "content": [{"type": "text", "text": str(message)}], "stopReason": "error"}})
        elif kind == "turn.succeeded":
            if payload.get("usage"):
                usage = _ori_usage(payload["usage"])
            flush()
    flush()
    if result.get("ok") is False and not any(
            (entry.get("message") or {}).get("stopReason") == "error" for entry in entries):
        message = (result.get("error") or {}).get("message") or "ori error"  # e.g. it never started a turn
        entries.append({"type": "message", "message": {"role": "assistant", "content": [
            {"type": "text", "text": str(message)}], "stopReason": "error"}})
    return entries


HARNESSES = {"pi": Pi, "claude-code": ClaudeCode, "agy": Agy, "grok-build": GrokBuild, "muse-code": MuseCode,
             "codex": Codex, "ori": Ori}


def split_harness(spec):
    """'claude-code:claude-opus-5-5:high' -> ('claude-code', 'claude-opus-5-5:high'); no known
    harness prefix -> ('pi', spec)."""
    name, sep, rest = spec.partition(":")
    return (name, rest) if sep and name in HARNESSES else ("pi", spec)
