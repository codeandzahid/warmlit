"""Agent loop with a pluggable model provider."""
from .approvals import ApprovalGate
from .memory import MemoryStore
from .tools import ToolRegistry


class EchoModel:
    """Demo model: no API key needed. Real providers plug in the same way."""

    name = "echo-demo"

    def reply(self, system: str, history: list[dict], tools: list[dict]) -> str:
        last = history[-1]["content"] if history else ""
        return f"Echo: {last}"


class Agent:
    def __init__(self, model, memory: MemoryStore, tools: ToolRegistry, approvals: ApprovalGate | None = None):
        self.model = model
        self.memory = memory
        self.tools = tools
        self.approvals = approvals or ApprovalGate()
        self.history: list[dict] = []

    def system_prompt(self) -> str:
        notes = self.memory.all_notes()
        tool_lines = "\n".join(f"- {t['name']}: {t['description']}" for t in self.tools.list_tools())
        return (
            "You are a personal AI agent for one user. "
            "Use tools when needed. Ask approval before consequential actions.\n\n"
            f"Memory:\n{notes}\n\nTools:\n{tool_lines}"
        )

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        text = self.model.reply(self.system_prompt(), self.history, self.tools.list_tools())
        self.history.append({"role": "assistant", "content": text})
        return text

    def use_tool(self, name: str, **kwargs):
        if self.tools.is_consequential(name) and not self.approvals.check(name, consequential=True):
            raise PermissionError(f"approval needed for {name}")
        return self.tools.call(name, **kwargs)
