import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.agent_core import Agent, ApprovalGate, EchoModel, MemoryStore, UsageCounter, check_license, default_tools, make_license  # noqa: E402


class TestPlans(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _agent(self, plan, usage=None):
        return Agent(
            model=EchoModel(),
            memory=MemoryStore(self.root / "memory"),
            tools=default_tools(self.root / "workspace"),
            approvals=ApprovalGate(approve=lambda a: True),
            plan=plan,
            usage=usage,
        )

    def test_free_blocks_local_system_tasks(self):
        free = self._agent("free")
        self.assertIn("Paid", free.chat("/run echo hi"))
        self.assertIn("Paid", free.chat("/write a.txt hi"))

    def test_paid_allows_local_system_tasks(self):
        paid = self._agent("paid")
        self.assertIn("hi", paid.chat("/run echo hi"))

    def test_license_round_trip(self):
        p = self.root / "license.json"
        p.write_text(json.dumps(make_license(days=30)))
        info = check_license(p)
        self.assertEqual(info["plan"], "paid")
        self.assertGreaterEqual(info["days_left"], 29)

    def test_bad_license_is_free(self):
        p = self.root / "license.json"
        p.write_text(json.dumps({"plan": "paid", "expires": "2999-01-01", "sig": "bad"}))
        self.assertEqual(check_license(p)["plan"], "free")

    def test_free_daily_limit(self):
        usage = UsageCounter(self.root / "usage.json", daily_limit=2)
        free = self._agent("free", usage=usage)
        free.chat("one")
        free.chat("two")
        self.assertIn("limit", free.chat("three"))


if __name__ == "__main__":
    unittest.main()
