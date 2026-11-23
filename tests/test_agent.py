import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.agent_core import Agent, ApprovalGate, EchoModel, MemoryStore, default_tools  # noqa: E402


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.agent = Agent(
            model=EchoModel(),
            memory=MemoryStore(root / "memory"),
            tools=default_tools(root / "workspace"),
            approvals=ApprovalGate(approve=lambda action: True),
            plan="paid",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_chat_echoes(self):
        self.assertEqual(self.agent.chat("hi"), "Echo: hi")

    def test_memory_round_trip(self):
        self.agent.memory.remember("user likes short replies")
        self.assertTrue(self.agent.memory.search("short replies"))

    def test_no_approval_system(self):
        # Approval system removed (owner order 2026-11-23): writes run directly.
        agent = Agent(
            model=EchoModel(),
            memory=self.agent.memory,
            tools=self.agent.tools,
            plan="paid",
        )
        agent.use_tool("write_file", path="a.txt", content="x")
        self.assertEqual(agent.use_tool("read_file", path="a.txt"), "x")

    def test_write_and_read_file(self):
        self.agent.use_tool("write_file", path="a.txt", content="hello")
        self.assertEqual(self.agent.use_tool("read_file", path="a.txt"), "hello")


if __name__ == "__main__":
    unittest.main()
