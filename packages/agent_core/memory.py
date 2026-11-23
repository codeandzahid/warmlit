"""Markdown memory store, like Muse's MEMORY.md / USER.md files."""
from pathlib import Path


class MemoryStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.root / "MEMORY.md"
        if not self.memory_file.exists():
            self.memory_file.write_text("# Memory\n\n", encoding="utf-8")

    def remember(self, note: str) -> None:
        with self.memory_file.open("a", encoding="utf-8") as f:
            f.write(f"- {note}\n")

    def search(self, query: str) -> list[str]:
        q = query.lower()
        hits = []
        for line in self.memory_file.read_text(encoding="utf-8").splitlines():
            if q in line.lower():
                hits.append(line.strip())
        return hits

    def all_notes(self) -> str:
        return self.memory_file.read_text(encoding="utf-8")
