"""Goals, Ideas, Feed, Library — local JSON/markdown stores."""
import json
from datetime import date
from pathlib import Path


class JsonStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def all(self) -> list:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def add(self, item: dict) -> dict:
        items = self.all()
        items.append(item)
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")
        return item

    def update(self, index: int, **fields) -> dict:
        items = self.all()
        items[index].update(fields)
        self.path.write_text(json.dumps(items, indent=2), encoding="utf-8")
        return items[index]


class Goals:
    def __init__(self, data: str | Path):
        self.store = JsonStore(Path(data) / "goals.json")

    def add(self, title: str) -> str:
        self.store.add({"title": title, "status": "active", "created": date.today().isoformat(), "log": []})
        return f"Goal added: {title}"

    def list(self) -> str:
        items = self.store.all()
        return "\n".join(f"{i+1}. [{g['status']}] {g['title']}" for i, g in enumerate(items)) or "No goals yet."

    def done(self, index: int) -> str:
        g = self.store.update(index - 1, status="done")
        return f"Goal done: {g['title']}"

    def log(self, index: int, note: str) -> str:
        items = self.store.all()
        items[index - 1]["log"].append({"date": date.today().isoformat(), "note": note})
        self.store.path.write_text(json.dumps(items, indent=2), encoding="utf-8")
        return "Logged."


class Ideas:
    def __init__(self, data: str | Path):
        self.store = JsonStore(Path(data) / "ideas.json")

    def add(self, text: str) -> str:
        self.store.add({"text": text, "status": "new", "created": date.today().isoformat()})
        return f"Idea saved: {text}"

    def list(self) -> str:
        items = self.store.all()
        return "\n".join(f"{i+1}. [{x['status']}] {x['text']}" for i, x in enumerate(items)) or "No ideas yet."


class Feed:
    """Local daily feed: short posts built from goals + memory (no key)."""

    def __init__(self, data: str | Path):
        self.store = JsonStore(Path(data) / "feed.json")

    def generate(self, goals: Goals, memory_notes: str) -> str:
        today = date.today().isoformat()
        posts = []
        for g in goals.store.all():
            if g["status"] == "active":
                posts.append({"date": today, "title": f"Goal check: {g['title']}",
                              "body": f"Still active since {g['created']}. One small step today beats zero."})
        if not posts:
            posts.append({"date": today, "title": "Warmlit daily",
                          "body": "No active goals. Add one with /goal add <title>."})
        for p in posts:
            self.store.add(p)
        return "\n\n".join(f"{p['title']}\n{p['body']}" for p in posts)

    def list(self) -> str:
        items = self.store.all()[-10:]
        return "\n\n".join(f"{p['date']} — {p['title']}\n{p['body']}" for p in items) or "Feed empty. Try /feed make"


def library_list(workspace: str | Path) -> str:
    ws = Path(workspace)
    files = sorted(str(p.relative_to(ws)) for p in ws.rglob("*") if p.is_file())
    return "\n".join(files) or "Library empty."
