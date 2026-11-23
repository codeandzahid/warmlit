"""Agent loop with a pluggable model provider + local slash commands.

Slash commands work with ANY model (even the echo demo), so Warmlit is
usable locally with no API key:
  /remember <note>      save a memory note
  /search <words>       search memory
  /read <path>          read a workspace file
  /write <path> <text>  write a workspace file (needs approval)
  /files                list workspace files
  /run <command>        run shell command (needs approval)
  /web <url>            fetch a web page as text
  /browser <url>        open page in local Chrome
  /skills <words>       search skill playbooks
  /tools                list tools
  /jobs                 list scheduled jobs
  /job <schedule> <task>  add a job, e.g. /job every:60s say hello
"""
import json
import re

from .approvals import ApprovalGate
from .memory import MemoryStore
from .models import EchoModel
from .tools import ToolRegistry

TOOL_BLOCK = re.compile(r"```tool\s*(\{.*?\})\s*```", re.S)


class Agent:
    def __init__(self, model, memory: MemoryStore, tools: ToolRegistry,
                 approvals: ApprovalGate | None = None, scheduler=None):
        self.model = model
        self.memory = memory
        self.tools = tools
        self.approvals = approvals or ApprovalGate()
        self.scheduler = scheduler
        self.history: list[dict] = []

    def system_prompt(self) -> str:
        notes = self.memory.all_notes()
        tool_lines = "\n".join(f"- {t['name']}: {t['description']}" for t in self.tools.list_tools())
        return (
            "You are Warmlit, a personal AI agent for one user. "
            "Use tools when needed. To call a tool, reply with a fenced block:\n"
            "```tool\n{\"name\": \"read_file\", \"args\": {\"path\": \"a.txt\"}}\n```\n"
            "Ask approval before consequential actions. Answer in plain simple words.\n\n"
            f"Memory:\n{notes}\n\nTools:\n{tool_lines}"
        )

    def use_tool(self, name: str, **kwargs):
        if self.tools.is_consequential(name) and not self.approvals.check(name, consequential=True):
            raise PermissionError(f"approval needed for {name}")
        return self.tools.call(name, **kwargs)

    def _command(self, text: str) -> str | None:
        if not text.startswith("/"):
            return None
        parts = text[1:].split(maxsplit=2)
        cmd = parts[0].lower() if parts else ""
        arg = parts[1] if len(parts) > 1 else ""
        rest = parts[2] if len(parts) > 2 else ""
        try:
            if cmd == "remember":
                note = text[len("/remember "):]
                self.memory.remember(note)
                return "Saved."
            if cmd == "search":
                hits = self.memory.search(arg)
                return "\n".join(hits) or "No match."
            if cmd == "read":
                return self.use_tool("read_file", path=arg)
            if cmd == "write":
                return self.use_tool("write_file", path=arg, content=rest)
            if cmd == "files":
                return self.use_tool("list_files")
            if cmd == "run":
                return self.use_tool("run_shell", command=text[len("/run "):])
            if cmd == "web":
                return self.use_tool("web_fetch", url=arg)
            if cmd == "browser":
                return self.use_tool("browser_open", url=arg)
            if cmd == "skills":
                return self.use_tool("skills_search", query=arg)
            if cmd == "tools":
                return "\n".join(f"{t['name']} — {t['description']}" for t in self.tools.list_tools())
            if cmd == "jobs":
                if not self.scheduler:
                    return "No scheduler."
                return "\n".join(f"{j.name} [{j.schedule}] {j.task}" for j in self.scheduler.list_jobs()) or "No jobs."
            if cmd == "job" and self.scheduler:
                from .scheduler import Job
                job = self.scheduler.add(Job(name=f"job-{len(self.scheduler.jobs)+1}", schedule=arg, task=rest))
                return f"Job added: {job.schedule} — {job.task}"
        except PermissionError as e:
            return f"[needs approval: {e}]"
        except Exception as e:
            return f"[error: {e}]"
        return "Unknown command. Try /tools"

    def chat(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        cmd_out = self._command(user_text.strip())
        if cmd_out is not None:
            self.history.append({"role": "assistant", "content": cmd_out})
            return cmd_out
        text = self.model.reply(self.system_prompt(), self.history, self.tools.list_tools())
        # Tool-calling loop for real models (max 5 steps).
        for _ in range(5):
            m = TOOL_BLOCK.search(text)
            if not m:
                break
            try:
                call = json.loads(m.group(1))
                result = self.use_tool(call["name"], **call.get("args", {}))
            except PermissionError as e:
                result = f"[needs approval: {e}]"
            except Exception as e:
                result = f"[tool error: {e}]"
            self.history.append({"role": "assistant", "content": text})
            self.history.append({"role": "user", "content": f"Tool result:\n{result}"})
            text = self.model.reply(self.system_prompt(), self.history, self.tools.list_tools())
        self.history.append({"role": "assistant", "content": text})
        return text
