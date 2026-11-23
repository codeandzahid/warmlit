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


def default_tools(workspace: str | Path, skills_root: str | Path | None = None, memory=None, data_root: str | Path | None = None) -> ToolRegistry:
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

    # --- media (local, no keys) ---
    from packages.media import image as _img, video as _vid, voice as _voice

    def make_slideshow(images: str, out: str = "video.mp4") -> str:
        paths = [str(_inside(ws, p.strip())) for p in images.split(",") if p.strip()]
        return _vid.make_slideshow(paths, str(_inside(ws, out)))

    def make_text_video(text: str, out: str = "text-video.mp4") -> str:
        return _vid.make_text_video(text, str(_inside(ws, out)))

    def make_poster(text: str, out: str = "poster.png") -> str:
        return _img.make_poster(text, str(_inside(ws, out)))

    def make_thumbnail(text: str, out: str = "thumbnail.png") -> str:
        return _img.make_thumbnail(text, str(_inside(ws, out)))

    def say(text: str) -> str:
        return _voice.say(text)

    reg.register("make_slideshow", "Make a vertical video from images (comma list)", make_slideshow, consequential=True)
    reg.register("make_text_video", "Make a video with big text", make_text_video, consequential=True)
    reg.register("make_poster", "Make a poster image with text", make_poster, consequential=True)
    reg.register("make_thumbnail", "Make a YouTube thumbnail image", make_thumbnail, consequential=True)
    reg.register("say", "Speak text aloud (local voice)", say)

    # --- product: goals / ideas / feed / library / artifacts ---
    if data_root is not None:
        from packages.product import Feed as _Feed, Goals as _Goals, Ideas as _Ideas, artifacts as _art, library_list as _lib

        _goals, _ideas, _feed = _Goals(data_root), _Ideas(data_root), _Feed(data_root)

        reg.register("goal_add", "Add a goal", lambda title: _goals.add(title))
        reg.register("goal_list", "List goals", lambda: _goals.list())
        reg.register("goal_done", "Mark goal number done", lambda index: _goals.done(int(index)))
        reg.register("idea_add", "Save an idea", lambda text: _ideas.add(text))
        reg.register("idea_list", "List ideas", lambda: _ideas.list())
        reg.register("feed_make", "Make today's feed posts", lambda: _feed.generate(_goals, memory.all_notes() if memory else ""))
        reg.register("feed_list", "Show feed posts", lambda: _feed.list())
        reg.register("library", "List library files", lambda: _lib(ws))
        reg.register("make_doc", "Make an HTML document artifact", lambda title, body, out="doc.html": _art.make_doc(title, body, str(_inside(ws, out))), consequential=True)
        reg.register("make_deck", "Make a slide deck artifact (slides split by |)", lambda title, slides, out="deck.html": _art.make_deck(title, slides.split("|"), str(_inside(ws, out))), consequential=True)
        reg.register("make_sheet", "Make a CSV sheet artifact (rows split by ; cells by ,)", lambda rows, out="sheet.csv": _art.make_sheet([r.split(",") for r in rows.split(";")], str(_inside(ws, out))), consequential=True)

    # --- connectors (browser profiles, no API keys; posting needs approval) ---
    if data_root is not None:
        from packages.browser import ProfileManager as _PM
        from packages.connectors import all_connectors as _all_conn

        _profiles = _PM(Path(data_root) / "profiles")
        _conns = _all_conn(_profiles)

        def connector_status(connector: str = "") -> str:
            if connector in _conns:
                return _conns[connector].status()
            return "\n".join(f"{n}: profile {'exists' if (Path(data_root) / 'profiles' / n).exists() else 'not set up'}" for n in _conns)

        def connector_signin(connector: str) -> str:
            return _conns[connector].signin()

        def gmail_search(query: str) -> str:
            return _conns["gmail"].search(query)

        def gmail_send(to: str, subject: str, body: str) -> str:
            return _conns["gmail"].send(to, subject, body)

        def facebook_post(text: str) -> str:
            return _conns["facebook"].post_text(text)

        def tiktok_upload(video: str, caption: str = "") -> str:
            return _conns["tiktok"].upload_video(str(_inside(ws, video)), caption)

        def youtube_upload(video: str, title: str, description: str = "") -> str:
            return _conns["youtube"].upload_video(str(_inside(ws, video)), title, description)

        def whatsapp_send(contact: str, text: str) -> str:
            return _conns["whatsapp"].send_message(contact, text)

        reg.register("connector_status", "Check connector sign-in status", connector_status)
        reg.register("connector_signin", "Open browser for the user to sign in by hand", connector_signin, consequential=True)
        reg.register("gmail_search", "Search Gmail (signed-in profile)", gmail_search)
        reg.register("gmail_send", "Send an email via Gmail", gmail_send, consequential=True)
        reg.register("facebook_post", "Post text to Facebook", facebook_post, consequential=True)
        reg.register("tiktok_upload", "Upload a video to TikTok", tiktok_upload, consequential=True)
        reg.register("youtube_upload", "Upload a video to YouTube", youtube_upload, consequential=True)
        reg.register("whatsapp_send", "Send a WhatsApp message", whatsapp_send, consequential=True)

    reg.register("read_file", "Read a text file in the workspace", read_file)
    reg.register("write_file", "Write a text file in the workspace", write_file, consequential=True)
    reg.register("list_files", "List files in the workspace", list_files)
    reg.register("run_shell", "Run a shell command in the workspace", run_shell, consequential=True)
    reg.register("web_fetch", "Fetch a web page as text", web_fetch)
    reg.register("browser_open", "Open a page in local Chrome, return title and text", browser_open)
    reg.register("skills_search", "Search skill playbooks by keyword", skills_search)
    return reg
