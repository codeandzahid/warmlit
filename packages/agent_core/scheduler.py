"""Scheduler interface (cron-style jobs). Real runner comes in Phase 4."""
from dataclasses import dataclass, field


@dataclass
class Job:
    name: str
    schedule: str  # e.g. "daily@09:15" or a cron expression
    task: str
    enabled: bool = True


@dataclass
class Scheduler:
    jobs: list[Job] = field(default_factory=list)

    def add(self, job: Job) -> Job:
        self.jobs.append(job)
        return job

    def list_jobs(self) -> list[Job]:
        return list(self.jobs)
