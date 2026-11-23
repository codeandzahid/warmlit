"""Training data: a folder of videos + captions, or synthetic clips.

Folder format:
  data/videos/clip1.mp4
  data/videos/clip1.txt   (caption, one line)

Synthetic mode makes moving-shape clips with captions using PIL —
zero external data needed to prove the model can learn.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw


def frames_from_video(path: str, frames: int, size: int) -> torch.Tensor:
    """Extract `frames` evenly spaced frames via ffmpeg -> [3,T,H,W] in [-1,1]."""
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", path,
                        "-vf", f"fps=8,scale={size}:{size}", str(Path(td) / "f%04d.png")],
                       capture_output=True, timeout=120)
        imgs = sorted(Path(td).glob("*.png"))
        if not imgs:
            raise ValueError(f"no frames from {path}")
        idx = np.linspace(0, len(imgs) - 1, frames).astype(int)
        arr = np.stack([np.asarray(Image.open(imgs[i]).convert("RGB")) for i in idx])  # [T,H,W,3]
    t = torch.from_numpy(arr).float() / 127.5 - 1.0
    return t.permute(3, 0, 1, 2)  # [3,T,H,W]


class VideoFolderDataset:
    def __init__(self, folder: str, frames: int, size: int):
        self.items = []
        for v in sorted(Path(folder).glob("*.mp4")):
            cap_file = v.with_suffix(".txt")
            caption = cap_file.read_text().strip() if cap_file.exists() else v.stem
            self.items.append((str(v), caption))
        self.frames, self.size = frames, size

    def __len__(self):
        return len(self.items)

    def get(self, i: int):
        path, caption = self.items[i % len(self.items)]
        return frames_from_video(path, self.frames, self.size), caption


# ---------------- synthetic data (learns with zero downloads) ----------------

SHAPES = ["red circle", "blue square", "green triangle", "yellow star"]
MOVES = ["moves right", "moves left", "moves down", "bounces"]


def synthetic_clip(caption: str, frames: int, size: int) -> torch.Tensor:
    color = {"red": (220, 40, 40), "blue": (40, 80, 220), "green": (40, 180, 60), "yellow": (230, 200, 40)}
    col = next((v for k, v in color.items() if k in caption), (200, 200, 200))
    out = []
    for i in range(frames):
        t = i / max(1, frames - 1)
        img = Image.new("RGB", (size, size), (15, 15, 25))
        d = ImageDraw.Draw(img)
        r = size // 6
        if "moves right" in caption:
            x, y = int(size * (0.15 + 0.7 * t)), size // 2
        elif "moves left" in caption:
            x, y = int(size * (0.85 - 0.7 * t)), size // 2
        elif "moves down" in caption:
            x, y = size // 2, int(size * (0.15 + 0.7 * t))
        else:  # bounces
            x, y = size // 2, int(size * (0.5 - 0.3 * abs(np.sin(t * 3.14 * 2))))
        if "circle" in caption:
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        elif "square" in caption:
            d.rectangle([x - r, y - r, x + r, y + r], fill=col)
        elif "triangle" in caption:
            d.polygon([(x, y - r), (x - r, y + r), (x + r, y + r)], fill=col)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        out.append(np.asarray(img))
    arr = np.stack(out)
    t = torch.from_numpy(arr).float() / 127.5 - 1.0
    return t.permute(3, 0, 1, 2)


def synthetic_batch(batch: int, frames: int, size: int):
    caps, vids = [], []
    for _ in range(batch):
        cap = f"{SHAPES[np.random.randint(len(SHAPES))]} {MOVES[np.random.randint(len(MOVES))]}"
        caps.append(cap)
        vids.append(synthetic_clip(cap, frames, size))
    return torch.stack(vids), caps
