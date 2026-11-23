import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.media import videogen  # noqa: E402


class TestVideoGen(unittest.TestCase):
    def test_generate_from_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            out = str(Path(td) / "gen.mp4")
            result = videogen.generate_video(
                "a man walks to a house then a car drives on the road",
                out, seconds_per_scene=2, fps=8, size=(360, 640))
            self.assertIn("Warmlit engine", result)
            self.assertTrue(Path(out).stat().st_size > 5000)
            info = videogen.video_info(out)
            self.assertGreater(info["duration"], 3.0)

    def test_scenes_split(self):
        self.assertEqual(len(videogen.split_scenes("one. then two")), 2)


if __name__ == "__main__":
    unittest.main()
