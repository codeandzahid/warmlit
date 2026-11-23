"""Tool registry. Tools are plain functions with a name + description."""
from pathlib import Path


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name: str, description: str, fn, consequential: bool = False):
        self._tools[name] = {
            "description": description,
            "fn": fn,
            "consequential": consequential,
        }

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


def default_tools(workspace: str | Path) -> ToolRegistry:
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)
    reg = ToolRegistry()

    def read_file(path: str) -> str:
        p = (ws / path).resolve()
        if ws.resolve() not in p.parents and p != ws.resolve():
            raise ValueError("path outside workspace")
        return p.read_text(encoding="utf-8")

    def write_file(path: str, content: str) -> str:
        p = (ws / path).resolve()
        if ws.resolve() not in p.parents and p != ws.resolve():
            raise ValueError("path outside workspace")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {path}"

    reg.register("read_file", "Read a text file in the workspace", read_file)
    reg.register("write_file", "Write a text file in the workspace", write_file, consequential=True)
    return reg
