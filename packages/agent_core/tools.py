"""Tool registry. Tools are plain functions with a name + description."""
import html
import re
import subprocess
import urllib.request
from pathlib import Path


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, description: str, fn, consequential: bool = False):
        self._tools[name] = {"description": description, "fn": fn, "consequential": consequential}

    def list_tools(self) -> list[dict]:
        return [
            {"name": n, "description": t["description"], "consequential": t["consequential"]}
            for n, t in sorted(self._tools.items())
        ]

    def is_consequential(self, name: str) -> bool:
        return bool(self._tools.get(name, {}).get("consequential"))

    def call(self, name: str, **kwargs):
        if name not in self._tools:
            raise KeyError(f"unknown tool: {name}")
        return self._tools[name]["fn"](**kwargs)


def _inside(ws: Path, path: str) -> Path:
    p = (ws / path).resolve()
    if ws.resolve() not in p.parents and p != ws.resolve():
        raise ValueError("path outside workspace")
    return p


def default_tools(workspace: str | Path, skills_root: str | Path | None = None, memory=None) -> ToolRegistry:
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)
    reg = ToolRegistry()

    def read_file(path: str) -> str:
        return _inside(ws, path).read_text(encoding="utf-8")

    def write_file(path: str, content: str) -> str:
        p = _inside(ws, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {path}"

    def list_files(path: str = ".") -> str:
        p = _inside(ws, path)
        return "\n".join(sorted(str(x.relative_to(ws)) for x in p.rglob("*") if x.is_file())) or "(empty)"

    def run_shell(command: str) -> str:
        r = subprocess.run(command, shell=True, cwd=ws, capture_output=True, text=True, timeout=60)
        out = (r.stdout or "") + (r.stderr or "")
        return f"exit {r.returncode}\n{out[:4000]}"

    def web_fetch(url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": "Warmlit/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "ignore")
        text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
        text = re.sub(r"(?s)<[^>]+>", " ", text)
        return html.unescape(re.sub(r"\s+", " ", text)).strip()[:6000]

    def browser_open(url: str) -> str:
        """Open a page in the local Chrome via Playwright, return title + text."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return "playwright not installed. Run: pip install playwright"
        chrome = Path.home() / "workspace/chrome-home/opt/google/chrome/chrome"
        kwargs = {"headless": True}
        if chrome.exists():
            kwargs["executable_path"] = str(chrome)
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**kwargs)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            title = page.title()
            text = page.inner_text("body")[:4000]
            browser.close()
        return f"Title: {title}\n{text}"

    def skills_search(query: str) -> str:
        root = Path(skills_root) if skills_root else Path(__file__).resolve().parents[1] / "skills"
        hits = []
        for f in sorted(root.rglob("SKILL.md")):
            txt = f.read_text(encoding="utf-8", errors="ignore")
            if query.lower() in txt.lower() or query.lower() in str(f).lower():
                hits.append(f"{f.parent.name}: {txt.splitlines()[0] if txt else ''}")
        return "\n".join(hits) or "no skill matched"

    if memory is not None:
        def memory_remember(note: str) -> str:
            memory.remember(note)
            return "Saved."

        def memory_search(query: str) -> str:
            hits = memory.search(query)
            return "\n".join(hits) or "No match."

        reg.register("memory_remember", "Save a note to long-term memory", memory_remember)
        reg.register("memory_search", "Search long-term memory notes", memory_search)

    reg.register("read_file", "Read a text file in the workspace", read_file)
    reg.register("write_file", "Write a text file in the workspace", write_file, consequential=True)
    reg.register("list_files", "List files in the workspace", list_files)
    reg.register("run_shell", "Run a shell command in the workspace", run_shell, consequential=True)
    reg.register("web_fetch", "Fetch a web page as text", web_fetch)
    reg.register("browser_open", "Open a page in local Chrome, return title and text", browser_open)
    reg.register("skills_search", "Search skill playbooks by keyword", skills_search)
    return reg
