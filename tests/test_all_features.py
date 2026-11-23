import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.agent_core import Agent, ApprovalGate, LocalBrain, MemoryStore, default_tools  # noqa: E402
from packages.browser import ProfileManager  # noqa: E402
from packages.connectors import all_connectors  # noqa: E402
from packages.media import image as img, video as vid  # noqa: E402
from packages.product import Feed, Goals, Ideas, Vault, artifacts  # noqa: E402


class TestAllFeatures(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ws = self.root / "workspace"
        self.ws.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_video_and_image_making(self):
        poster = str(self.ws / "p.png")
        img.make_poster("Hello Warmlit", poster)
        self.assertTrue(Path(poster).exists())
        out = str(self.ws / "v.mp4")
        vid.make_text_video("Hello", out, seconds=2)
        self.assertTrue(Path(out).stat().st_size > 1000)
        slide = str(self.ws / "s.mp4")
        vid.make_slideshow([poster], slide, seconds_each=1)
        self.assertTrue(Path(slide).exists())

    def test_goals_ideas_feed(self):
        g = Goals(self.root)
        g.add("Make 10 videos")
        self.assertIn("Make 10 videos", g.list())
        i = Ideas(self.root)
        i.add("New series idea")
        self.assertIn("New series", i.list())
        f = Feed(self.root)
        self.assertIn("Goal check", f.generate(g, ""))

    def test_artifacts(self):
        doc = str(self.ws / "d.html")
        artifacts.make_doc("Title", "Body", doc)
        self.assertIn("Title", Path(doc).read_text())
        sheet = str(self.ws / "s.csv")
        artifacts.make_sheet([["a", "b"], ["1", "2"]], sheet)
        self.assertIn("a,b", Path(sheet).read_text())

    def test_vault_round_trip(self):
        v = Vault(self.root / "vault.json")
        v.set("my-password", "api-key", "secret-value")
        self.assertEqual(v.get("my-password", "api-key"), "secret-value")
        with self.assertRaises(ValueError):
            v.get("wrong", "api-key")

    def test_connectors_dry_run(self):
        conns = all_connectors(ProfileManager(self.root / "profiles"), dry_run=True)
        self.assertIn("dry-run", conns["gmail"].send("a@b.c", "hi", "body"))
        self.assertIn("dry-run", conns["facebook"].post_text("hello"))
        self.assertIn("dry-run", conns["tiktok"].upload_video("v.mp4", "cap"))
        self.assertIn("dry-run", conns["youtube"].upload_video("v.mp4", "title"))
        self.assertIn("dry-run", conns["whatsapp"].send_message("Mom", "hi"))

    def test_agent_all_tools_wired(self):
        memory = MemoryStore(self.root / "memory")
        agent = Agent(model=LocalBrain(), memory=memory,
                      tools=default_tools(self.ws, memory=memory, data_root=self.root),
                      approvals=ApprovalGate(approve=lambda a: True), plan="paid")
        self.assertIn("Goal added", agent.chat("/goal add Test goal"))
        self.assertIn("Test goal", agent.chat("/goal"))
        self.assertIn("made", agent.chat("make a poster that says Hi Warmlit"))
        self.assertIn("gmail", agent.chat("/connectors"))


if __name__ == "__main__":
    unittest.main()
