"""Hooks + subagents (local versions).

Hook: watch a file or URL; when it changes, run an agent task.
Subagent: run a task in a background thread; result lands in a log
the main chat can read with /subagents.
"""
import hashlib
import threading
import time
import urllib.request
from pathlib import Path


class HookWatcher:
    def __init__(self):
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []

    def watch_file(self, path: str, agent, task: str, poll: float = 5.0):
        def loop():
            last = None
            while not self._stop.wait(poll):
                try:
                    cur = hashlib.sha256(Path(path).read_bytes()).hexdigest()
                except Exception:
                    cur = None
                if last is not None and cur != last:
                    agent.chat(task)
                last = cur
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        self._threads.append(t)
        return f"Watching file {path}"

    def watch_url(self, url: str, agent, task: str, poll: float = 60.0):
        def loop():
            last = None
            while not self._stop.wait(poll):
                try:
                    with urllib.request.urlopen(url, timeout=15) as r:
                        cur = hashlib.sha256(r.read()).hexdigest()
                except Exception:
                    cur = None
                if last is not None and cur != last:
                    agent.chat(task)
                last = cur
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        self._threads.append(t)
        return f"Watching URL {url}"

    def stop(self):
        self._stop.set()


class Subagents:
    def __init__(self, log_path: str | Path):
        self.log = Path(log_path)
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self._n = 0

    def spawn(self, agent, task: str) -> str:
        self._n += 1
        sid = self._n

        def run():
            try:
                out = agent.chat(task)
            except Exception as e:
                out = f"[subagent error: {e}]"
            with open(self.log, "a", encoding="utf-8") as f:
                f.write(f"#{sid} {task}\n-> {out}\n\n")

        threading.Thread(target=run, daemon=True).start()
        return f"Subagent #{sid} started: {task}"

    def results(self) -> str:
        return self.log.read_text(encoding="utf-8")[-4000:] if self.log.exists() else "No subagent results yet."
