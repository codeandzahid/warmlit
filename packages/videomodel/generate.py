"""Generate a video from a prompt with a trained Warmlit checkpoint.

  python -m packages.videomodel.generate --ckpt ckpt.pt --prompt "red circle moves right" --out out.mp4
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from .model import WarmlitVideoModel


def frames_to_mp4(frames: torch.Tensor, out: str, fps: int = 8):
    """frames: [1,3,T,H,W] in [-1,1]"""
    arr = ((frames[0].permute(1, 2, 3, 0).cpu().numpy() + 1) * 127.5).clip(0, 255).astype(np.uint8)
    with tempfile.TemporaryDirectory() as td:
        for i, fr in enumerate(arr):
            Image.fromarray(fr).save(Path(td) / f"f{i:04d}.png")
        subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-framerate", str(fps),
                        "-i", str(Path(td) / "f%04d.png"),
                        "-vf", "scale=720:720:flags=neighbor",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", out],
                       capture_output=True, timeout=120)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", default="generated.mp4")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--cfg", type=float, default=3.0)
    args = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = WarmlitVideoModel.load(args.ckpt, device)
    frames = model.generate(args.prompt, steps=args.steps, cfg_scale=args.cfg, device=device)
    frames_to_mp4(frames, args.out, fps=model.cfg.fps)
    print(f"made {args.out}")


if __name__ == "__main__":
    main()
