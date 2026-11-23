"""Scheduler that actually runs jobs in a background thread.

Schedules:
  every:60s / every:5m / every:1h
  daily@09:15
Jobs persist in jobs.json next to the data folder. Each run calls
agent.chat(task) and appends the result to jobs.log.
"""
import json
import threading
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class Job:
    name: str
    schedule: str
    task: str
    enabled: bool = True
    last_run: float = 0.0


def _interval_seconds(schedule: str) -> float | None:
    if schedule.startswith("every:"):
        v = schedule[6:]
        try:
            if v.endswith("s"):
                return float(v[:-1])
            if v.endswith("m"):
                return float(v[:-1]) * 60
            if v.endswith("h"):
                return float(v[:-1]) * 3600
        except ValueError:
            return None
    return None


def _daily_due(schedule: str, last_run: float) -> bool:
    if not schedule.startswith("daily@"):
        return False
    try:
        hh, mm = map(int, schedule[6:].split(":"))
    except ValueError:
        return False
    now = datetime.now()
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    return now >= target and last_run < target.timestamp()


@dataclass
class Scheduler:
    jobs: list[Job] = field(default_factory=list)
    store: Path | None = None
    _thread: threading.Thread | None = None
    _stop: threading.Event = field(default_factory=threading.Event)

    def __post_init__(self):
        if self.store and Path(self.store).exists():
            try:
                self.jobs = [Job(**j) for j in json.loads(Path(self.store).read_text())]
            except Exception:
                self.jobs = []

    def _save(self):
        if self.store:
            Path(self.store).parent.mkdir(parents=True, exist_ok=True)
            Path(self.store).write_text(json.dumps([asdict(j) for j in self.jobs], indent=2))

    def add(self, job: Job) -> Job:
        self.jobs.append(job)
        self._save()
        return job

    def list_jobs(self) -> list[Job]:
        return list(self.jobs)

    def due_jobs(self, now: float | None = None) -> list[Job]:
        now = now or time.time()
        due = []
        for j in self.jobs:
            if not j.enabled:
                continue
            iv = _interval_seconds(j.schedule)
            if iv is not None and now - j.last_run >= iv:
                due.append(j)
            elif _daily_due(j.schedule, j.last_run):
                due.append(j)
        return due

    def start(self, agent, log_path: str | Path, poll_seconds: float = 5.0):
        def loop():
            while not self._stop.wait(poll_seconds):
                for job in self.due_jobs():
                    job.last_run = time.time()
                    self._save()
                    try:
                        out = agent.chat(job.task)
                    except Exception as e:
                        out = f"[job error: {e}]"
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.now().isoformat()} {job.name}: {out}\n")

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
        return self._thread

    def stop(self):
        self._stop.set()
