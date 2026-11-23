import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.agent_core import Agent, ApprovalGate, LocalBrain, MemoryStore, default_tools, pick_model  # noqa: E402


class TestNoKey(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        memory = MemoryStore(root / "memory")
        self.agent = Agent(
            model=LocalBrain(),
            memory=memory,
            tools=default_tools(root / "workspace", memory=memory),
            approvals=ApprovalGate(approve=lambda a: True),
            plan="paid",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_pick_model_needs_no_key(self):
        os.environ.pop("MODEL_PROVIDER", None)
        os.environ.pop("MODEL_API_KEY", None)
        model = pick_model()
        self.assertIn("local-brain", model.name)

    def test_plain_remember_and_search(self):
        self.assertEqual(self.agent.chat("remember that I like tea"), "Saved.")
        self.assertIn("tea", self.agent.chat("search memory for tea"))

    def test_math_and_help(self):
        self.assertIn("96", self.agent.chat("what is 12*8"))
        self.assertIn("no API key", self.agent.chat("help"))

    def test_plain_file_and_shell(self):
        self.agent.chat("write file note.txt hello warmlit")
        self.assertIn("hello warmlit", self.agent.chat("read file note.txt"))
        self.assertIn("ok", self.agent.chat("run echo ok"))


if __name__ == "__main__":
    unittest.main()
