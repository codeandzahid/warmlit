"""LocalBrain — a no-key, no-internet brain built into Warmlit.

Works with zero API keys and zero installs. It understands plain
commands and turns them into tool calls, answers time/date/math,
and searches the memory notes it is given. For full free-form AI
chat, run Ollama locally (also no key) — Warmlit auto-detects it.
"""
import ast
import operator
import re
from datetime import datetime

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
       ast.USub: operator.neg}


def _safe_math(expr: str):
    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](ev(node.operand))
        raise ValueError("bad math")
    return ev(ast.parse(expr, mode="eval"))


def _tool(name: str, **args) -> str:
    import json
    return "```tool\n" + json.dumps({"name": name, "args": args}) + "\n```"


HELP = (
    "I am Warmlit, running 100% locally with no API key.\n"
    "Try: remember that I like tea · search memory for tea · list files · "
    "read file note.txt · write file note.txt hello · run echo hi · "
    "fetch https://example.com · open https://example.com · "
    "what time is it · what is 12*8 · /tools · /jobs"
)


class LocalBrain:
    name = "local-brain (no key)"

    def reply(self, system: str, history: list[dict], tools: list[dict]) -> str:
        text = (history[-1]["content"] if history else "").strip()
        low = text.lower()

        if low.startswith("tool result:"):
            return text.split(":", 1)[1].strip() or "Done."

        if low in {"hi", "hello", "hey", "salam", "assalamualaikum"}:
            return "Hello. " + HELP
        if low in {"help", "what can you do", "what can you do?"}:
            return HELP
        if "time" in low or "date" in low or "today" in low:
            now = datetime.now()
            return f"Now: {now.strftime('%A %Y-%m-%d %H:%M')} (local time)."

        m = re.search(r"(?:what is|calculate|calc)\s+([0-9+\-*/(). %]+)\??$", low)
        if m:
            try:
                return f"{m.group(1).strip()} = {_safe_math(m.group(1).strip())}"
            except Exception:
                return "I could not do that math."

        m = re.match(r"remember(?: that)?\s+(.+)", text, re.I)
        if m:
            return _tool("memory_remember", note=m.group(1))
        m = re.match(r"(?:search memory for|find in memory|recall)\s+(.+)", text, re.I)
        if m:
            return _tool("memory_search", query=m.group(1))
        if low in {"list files", "show files", "files"}:
            return _tool("list_files")
        m = re.match(r"read file\s+(\S+)", text, re.I)
        if m:
            return _tool("read_file", path=m.group(1))
        m = re.match(r"write file\s+(\S+)\s+(.+)", text, re.I | re.S)
        if m:
            return _tool("write_file", path=m.group(1), content=m.group(2))
        m = re.match(r"run\s+(.+)", text, re.I | re.S)
        if m:
            return _tool("run_shell", command=m.group(1))
        m = re.match(r"(?:fetch|get)\s+(https?://\S+)", text, re.I)
        if m:
            return _tool("web_fetch", url=m.group(1))
        m = re.match(r"open\s+(https?://\S+)", text, re.I)
        if m:
            return _tool("browser_open", url=m.group(1))
        m = re.match(r"(?:search skills for|find skill)\s+(.+)", text, re.I)
        if m:
            return _tool("skills_search", query=m.group(1))
        m = re.match(r"(?:add goal|new goal)\s+(.+)", text, re.I)
        if m:
            return _tool("goal_add", title=m.group(1))
        if low in {"list goals", "my goals", "goals"}:
            return _tool("goal_list")
        m = re.match(r"(?:add idea|new idea|idea)\s+(.+)", text, re.I)
        if m:
            return _tool("idea_add", text=m.group(1))
        if low in {"make feed", "today feed", "feed"}:
            return _tool("feed_make")
        if low in {"library", "my files", "show library"}:
            return _tool("library")
        m = re.match(r"make (?:a )?(?:poster|image) (?:that says|with text)\s+(.+)", text, re.I)
        if m:
            return _tool("make_poster", text=m.group(1))
        m = re.match(r"make (?:a )?thumbnail (?:that says|with text)\s+(.+)", text, re.I)
        if m:
            return _tool("make_thumbnail", text=m.group(1))
        m = re.match(r"make (?:a )?text video (?:that says|with text)\s+(.+)", text, re.I)
        if m:
            return _tool("make_text_video", text=m.group(1))
        m = re.match(r"say\s+(.+)", text, re.I)
        if m:
            return _tool("say", text=m.group(1))
        m = re.match(r"post to facebook\s+(.+)", text, re.I | re.S)
        if m:
            return _tool("facebook_post", text=m.group(1))
        m = re.match(r"search gmail for\s+(.+)", text, re.I)
        if m:
            return _tool("gmail_search", query=m.group(1))

        # Answer from memory notes in the system prompt if a word matches.
        notes = [ln.strip("- ").strip() for ln in system.splitlines() if ln.startswith("- ") and ":" not in ln[:12]]
        words = [w for w in re.findall(r"[a-z]{4,}", low)]
        hits = [n for n in notes if any(w in n.lower() for w in words)]
        if hits:
            return "From memory:\n" + "\n".join(f"- {h}" for h in hits[:5])

        return (
            "I run locally with no key, so I do tasks and simple answers. "
            "For full AI chat, install Ollama (free, no key) — Warmlit finds it alone. "
            "Type 'help' to see what I can do now."
        )
