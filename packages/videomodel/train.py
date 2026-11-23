"""Train Warmlit Video Model on your own computer.

Examples:
  # prove it learns, zero downloads (synthetic moving shapes):
  python -m packages.videomodel.train --synthetic --steps 500 --out ckpt.pt

  # your own videos (folder of .mp4 + .txt captions):
  python -m packages.videomodel.train --data data/videos --steps 5000 --out ckpt.pt

Honest scale (from research): on a normal PC this tiny model learns
simple/narrow-domain motion at 64px. General photoreal text-to-video
needs datacenter-scale training — no small PC can do that from scratch.
"""
import argparse
import time

import torch

from .config import VideoModelConfig
from .data import VideoFolderDataset, synthetic_batch
from .model import WarmlitVideoModel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="", help="folder of .mp4 + .txt captions")
    ap.add_argument("--synthetic", action="store_true", help="train on synthetic moving shapes")
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--out", default="warmlit-video-model.pt")
    ap.add_argument("--resume", default="")
    args = ap.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"device: {device}")
    model = WarmlitVideoModel.load(args.resume, device) if args.resume else WarmlitVideoModel().to(device)
    print(f"parameters: {model.num_params() / 1e6:.1f}M")
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    dataset = VideoFolderDataset(args.data, model.cfg.frames, model.cfg.height) if args.data else None
    if dataset is not None and len(dataset) == 0:
        raise SystemExit(f"no .mp4 files in {args.data}")

    model.train()
    start = time.time()
    for step in range(1, args.steps + 1):
        if dataset is not None:
            vids, caps = [], []
            for b in range(args.batch):
                v, c = dataset.get(step * args.batch + b)
                vids.append(v); caps.append(c)
            videos = torch.stack(vids).to(device)
        else:
            videos, caps = synthetic_batch(args.batch, model.cfg.frames, model.cfg.height)
            videos = videos.to(device)
        out = model.train_step(videos, caps)
        opt.zero_grad()
        out["loss"].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 25 == 0 or step == 1:
            print(f"step {step}/{args.steps} loss {out['loss'].item():.4f} "
                  f"(vae {out['vae'].item():.4f} flow {out['flow'].item():.4f}) "
                  f"{time.time() - start:.0f}s")
    model.save(args.out)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
