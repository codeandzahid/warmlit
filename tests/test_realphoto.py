import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.media import realphoto  # noqa: E402


class TestRealPhoto(unittest.TestCase):
    def test_status_is_plain(self):
        s = realphoto.status()
        self.assertTrue(s.startswith("real-photo:"))

    def test_generate_without_deps_gives_clear_error(self):
        ok, _ = realphoto.available()
        if not ok:
            with self.assertRaises(RuntimeError):
                realphoto.generate("a boat on mud", "x.mp4")


if __name__ == "__main__":
    unittest.main()
