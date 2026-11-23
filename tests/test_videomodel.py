"""Videomodel tests — skipped when PyTorch is not installed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@unittest.skipUnless(HAS_TORCH, "torch not installed")
class TestVideoModel(unittest.TestCase):
    def test_forward_train_generate(self):
        from packages.videomodel import VideoModelConfig, WarmlitVideoModel
        from packages.videomodel.data import synthetic_batch

        cfg = VideoModelConfig(frames=8, height=32, width=32, dit_depth=2, dit_hidden=64,
                               text_dim=64, vae_base_channels=16)
        model = WarmlitVideoModel(cfg)
        videos, caps = synthetic_batch(1, cfg.frames, cfg.height)
        out = model.train_step(videos, caps)
        out["loss"].backward()
        self.assertTrue(torch.isfinite(out["loss"]))
        frames = model.generate("red circle moves right", steps=3)
        self.assertEqual(frames.shape, (1, 3, cfg.frames, cfg.height, cfg.width))


if __name__ == "__main__":
    unittest.main()
