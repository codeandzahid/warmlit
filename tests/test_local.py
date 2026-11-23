import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.agent_core import Agent, ApprovalGate, EchoModel, Job, MemoryStore, Scheduler, default_tools  # noqa: E402


class TestLocal(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.scheduler = Scheduler(store=root / "jobs.json")
        self.agent = Agent(
            model=EchoModel(),
            memory=MemoryStore(root / "memory"),
            tools=default_tools(root / "workspace"),
            approvals=ApprovalGate(approve=lambda a: True),
            scheduler=self.scheduler,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_commands(self):
        self.assertEqual(self.agent.chat("/remember I like tea"), "Saved.")
        self.assertIn("tea", self.agent.chat("/search tea"))
        self.assertIn("read_file", self.agent.chat("/tools"))

    def test_shell_tool(self):
        out = self.agent.chat("/run echo warmlit-ok")
        self.assertIn("warmlit-ok", out)

    def test_scheduler_due(self):
        job = self.scheduler.add(Job(name="t", schedule="every:1s", task="/remember tick"))
        self.assertIn(job, self.scheduler.due_jobs(now=time.time() + 2))

    def test_scheduler_runs(self):
        log = Path(self.tmp.name) / "jobs.log"
        self.scheduler.add(Job(name="t", schedule="every:1s", task="/remember tick"))
        self.scheduler.start(self.agent, log, poll_seconds=0.2)
        time.sleep(2.5)
        self.scheduler.stop()
        self.assertTrue(log.exists() and "Saved." in log.read_text())


if __name__ == "__main__":
    unittest.main()
