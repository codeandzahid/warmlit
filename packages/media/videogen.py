"""Warmlit Video Generation — our OWN engine. No Meta, no keys, no cloud.

How it works (like a text-to-video generator, built from scratch):
  prompt -> scenes -> animated frames drawn locally -> ffmpeg MP4.

The built-in engine draws animated 2D scenes (sky, sun/moon, ground,
trees, houses, cars, boats, walking figures, captions) with camera
pan/zoom and moving objects. It runs on any computer, no GPU.

A real diffusion model (e.g. a local open model on the owner's PC)
can plug in later through VIDEO_MODEL_CMD — see docs/videogen.md.
Warmlit never calls Meta or any cloud video service.
"""
import math
import os
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def split_scenes(prompt: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\bthen\b|\.|;", prompt) if p.strip()]
    return parts or [prompt]


def _sky(d, W, H, t, night):
    top = (10, 10, 40) if night else (70, 150, 230)
    bot = (30, 30, 70) if night else (180, 225, 255)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)))
    # sun / moon moves across
    cx, cy = int(W * (0.1 + 0.8 * t)), int(H * 0.22)
    d.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], fill=(240, 240, 200) if night else (255, 220, 60))


def _ground(d, W, H, water=False):
    y0 = int(H * 0.72)
    d.rectangle([0, y0, W, H], fill=(40, 90, 180) if water else (60, 140, 60))
    return y0


def _tree(d, x, y, s=1.0):
    d.rectangle([x - 5 * s, y - 50 * s, x + 5 * s, y], fill=(110, 70, 30))
    d.ellipse([x - 35 * s, y - 120 * s, x + 35 * s, y - 40 * s], fill=(30, 120, 40))


def _house(d, x, y, s=1.0):
    d.rectangle([x, y - 80 * s, x + 110 * s, y], fill=(230, 220, 200))
    d.polygon([(x - 10 * s, y - 80 * s), (x + 55 * s, y - 130 * s), (x + 120 * s, y - 80 * s)], fill=(180, 60, 40))
    d.rectangle([x + 45 * s, y - 50 * s, x + 70 * s, y], fill=(120, 80, 40))


def _car(d, x, y, s=1.0, color=(220, 40, 40)):
    d.rectangle([x, y - 35 * s, x + 130 * s, y - 5 * s], fill=color)
    d.rectangle([x + 25 * s, y - 60 * s, x + 95 * s, y - 35 * s], fill=color)
    for wx in (x + 25 * s, x + 100 * s):
        d.ellipse([wx - 14 * s, y - 18 * s, wx + 14 * s, y + 10 * s], fill=(20, 20, 20))


def _boat(d, x, y, s=1.0):
    d.polygon([(x, y), (x + 140 * s, y), (x + 115 * s, y + 30 * s), (x + 25 * s, y + 30 * s)], fill=(150, 90, 40))
    d.rectangle([x + 65 * s, y - 70 * s, x + 70 * s, y], fill=(90, 60, 30))
    d.polygon([(x + 72 * s, y - 68 * s), (x + 72 * s, y - 5 * s), (x + 115 * s, y - 5 * s)], fill=(245, 245, 245))


def _figure(d, x, y, phase, s=1.0, color=(20, 20, 20)):
    """Walking stick figure. phase 0..1 loops the walk."""
    swing = math.sin(phase * 2 * math.pi) * 18 * s
    d.ellipse([x - 12 * s, y - 95 * s, x + 12 * s, y - 71 * s], outline=color, width=3)
    d.line([(x, y - 71 * s), (x, y - 35 * s)], fill=color, width=4)
    d.line([(x, y - 35 * s), (x + swing, y)], fill=color, width=4)
    d.line([(x, y - 35 * s), (x - swing, y)], fill=color, width=4)
    d.line([(x, y - 60 * s), (x + swing * 0.7, y - 35 * s)], fill=color, width=3)
    d.line([(x, y - 60 * s), (x - swing * 0.7, y - 35 * s)], fill=color, width=3)



def _cloud(d, x, y, s=1.0):
    d.ellipse([x, y, x + 90 * s, y + 36 * s], fill=(245, 245, 245))
    d.ellipse([x + 25 * s, y - 18 * s, x + 70 * s, y + 30 * s], fill=(245, 245, 245))


def _pyramid(d, x, y, s=1.0):
    d.polygon([(x, y), (x + 90 * s, y - 110 * s), (x + 180 * s, y)], fill=(210, 180, 110))
    d.polygon([(x + 90 * s, y - 110 * s), (x + 180 * s, y), (x + 90 * s, y)], fill=(180, 150, 85))


def _wall(d, x, y, s=1.0):
    d.rectangle([x, y - 45 * s, x + 260 * s, y], fill=(160, 140, 120))
    for i in range(5):
        d.rectangle([x + i * 52 * s, y - 65 * s, x + i * 52 * s + 26 * s, y - 45 * s], fill=(160, 140, 120))


def _mountain(d, x, y, s=1.0):
    d.polygon([(x, y), (x + 110 * s, y - 170 * s), (x + 220 * s, y)], fill=(110, 110, 130))
    d.polygon([(x + 85 * s, y - 128 * s), (x + 110 * s, y - 170 * s), (x + 135 * s, y - 128 * s)], fill=(255, 255, 255))


def _city(d, x, y, s=1.0):
    for i, h in enumerate([120, 180, 90, 150]):
        bx = x + i * 55 * s
        d.rectangle([bx, y - h * s, bx + 45 * s, y], fill=(90, 100, 130))
        for wy in range(3):
            d.rectangle([bx + 8 * s, y - h * s + 12 * s + wy * 30 * s, bx + 20 * s, y - h * s + 24 * s + wy * 30 * s], fill=(255, 230, 120))


def _train(d, x, y, s=1.0):
    d.rectangle([x, y - 45 * s, x + 200 * s, y - 10 * s], fill=(60, 60, 160))
    d.rectangle([x + 160 * s, y - 70 * s, x + 200 * s, y - 45 * s], fill=(60, 60, 160))
    for wx in (x + 30 * s, x + 90 * s, x + 160 * s):
        d.ellipse([wx - 12 * s, y - 16 * s, wx + 12 * s, y + 8 * s], fill=(20, 20, 20))


def _plane(d, x, y, s=1.0):
    d.ellipse([x, y - 12 * s, x + 130 * s, y + 12 * s], fill=(235, 235, 235))
    d.polygon([(x + 55 * s, y), (x + 85 * s, y - 40 * s), (x + 95 * s, y)], fill=(200, 60, 60))
    d.polygon([(x + 5 * s, y - 5 * s), (x - 15 * s, y - 30 * s), (x + 15 * s, y - 5 * s)], fill=(200, 60, 60))


def _weather(d, W, H, t, kind):
    import random as _r
    _r.seed(7)
    for i in range(60):
        x = _r.randint(0, W)
        y = int((_r.randint(0, H) + t * H * 1.5) % H)
        if kind == "rain":
            d.line([(x, y), (x - 4, y + 14)], fill=(150, 180, 255), width=2)
        else:
            d.ellipse([x, y, x + 5, y + 5], fill=(255, 255, 255))

def render_frame(scene: str, t: float, W: int, H: int) -> Image.Image:
    """t = 0..1 progress inside the scene."""
    low = scene.lower()
    night = any(w in low for w in ["night", "dark", "moon", "star"])
    water = any(w in low for w in ["sea", "ocean", "river", "lake", "water", "boat"])
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    _sky(d, W, H, t, night)
    gy = _ground(d, W, H, water=water)
    # slow camera pan: shift world by t
    pan = int(W * 0.08 * t)
    _tree(d, W * 0.18 - pan, gy, 1.0)
    _tree(d, W * 0.85 - pan, gy, 0.8)
    _cloud(d, W * (0.05 + 0.5 * t), H * 0.08, 1.0)
    _cloud(d, W * (0.55 - 0.3 * t), H * 0.16, 0.7)
    if "pyramid" in low or "egypt" in low:
        _pyramid(d, W * 0.3 - pan, gy, 1.2)
    if "wall" in low:
        _wall(d, W * 0.1 - pan, gy, 1.2)
    if "mountain" in low:
        _mountain(d, W * 0.35 - pan, gy, 1.1)
    if "city" in low:
        _city(d, W * 0.15 - pan, gy, 1.0)
    if "train" in low:
        _train(d, W * (0.02 + 0.65 * t), gy + 45, 1.0)
    if "plane" in low or "fly" in low:
        _plane(d, W * (0.05 + 0.7 * t), H * 0.25, 1.0)
    if "house" in low or "home" in low or "village" in low:
        _house(d, W * 0.55 - pan, gy, 1.1)
    if "rain" in low:
        _weather(d, W, H, t, "rain")
    if "snow" in low:
        _weather(d, W, H, t, "snow")
    if "car" in low or "drive" in low or "road" in low:
        _car(d, W * (0.05 + 0.7 * t), gy + 40, 1.0)
    if water or "boat" in low:
        _boat(d, W * (0.1 + 0.6 * t), gy + 25 + int(4 * math.sin(t * 6)), 1.0)
    # main figure walks across unless scene is only objects
    if not any(w in low for w in ["car only", "no people", "empty"]):
        _figure(d, W * (0.1 + 0.75 * t), gy + 55, (t * 6) % 1.0, 1.1)
    # gentle zoom-in over the scene
    zoom = 1.0 + 0.12 * t
    if zoom > 1.01:
        zw, zh = int(W * zoom), int(H * zoom)
        img = img.resize((zw, zh), Image.LANCZOS).crop(((zw - W) // 2, (zh - H) // 2, (zw + W) // 2, (zh + H) // 2))
        d = ImageDraw.Draw(img)
    # caption (wrapped, up to 2 lines)
    font = _font(max(20, W // 24))
    text = scene.strip()
    words, lines, cur = text.split(), [], ""
    for w in words:
        if d.textlength(cur + " " + w, font=font) > W - 60 and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    lines = lines[:2]
    box_h = 34 * len(lines) + 16
    d.rectangle([0, H - box_h, W, H], fill=(0, 0, 0))
    y = H - box_h + 8
    for ln in lines:
        tw = d.textlength(ln, font=font)
        d.text(((W - tw) / 2, y), ln, fill="white", font=font)
        y += 34
    return img


def generate_video(prompt: str, out: str, seconds_per_scene: float = 4.0,
                   fps: int = 12, size: tuple = (720, 1280)) -> str:
    """Generate a video from a text prompt. Fully local, no Meta."""
    # Real-photo AI backend (open pretrained model on your PC, no Meta, no key):
    if os.environ.get("VIDEO_BACKEND") == "realphoto":
        from . import realphoto
        return realphoto.generate(prompt, out)

    # Warmlit Video Model (our own diffusion model, packages/videomodel):
    ckpt = os.environ.get("WARMLIT_VIDEO_CKPT")
    if ckpt and Path(ckpt).exists():
        import torch
        from packages.videomodel.generate import frames_to_mp4
        from packages.videomodel.model import WarmlitVideoModel
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = WarmlitVideoModel.load(ckpt, device)
        frames = model.generate(prompt, device=device)
        frames_to_mp4(frames, out, fps=model.cfg.fps)
        return f"made {out} (Warmlit Video Model)"

    # Optional external local diffusion model (owner's PC only, no Meta):
    cmd = os.environ.get("VIDEO_MODEL_CMD")
    if cmd:
        full = cmd.replace("{prompt}", prompt).replace("{out}", out)
        r = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=3600)
        if r.returncode == 0 and Path(out).exists():
            return f"made {out} (local model)"
        raise RuntimeError(f"local video model failed: {(r.stderr or r.stdout)[-500:]}")

    scenes = split_scenes(prompt)
    W, H = size
    with tempfile.TemporaryDirectory() as td:
        frames = []
        n = 0
        for scene in scenes:
            count = max(1, int(seconds_per_scene * fps))
            for i in range(count):
                frame = render_frame(scene, i / max(1, count - 1), W, H)
                p = Path(td) / f"f{n:05d}.png"
                frame.save(p)
                frames.append(p)
                n += 1
        r = subprocess.run(
            ["ffmpeg", "-y", "-framerate", str(fps), "-i", str(Path(td) / "f%05d.png"),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", out],
            capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout)[-800:])
    return f"made {out} ({len(scenes)} scene(s), {len(scenes) * seconds_per_scene:.0f}s, Warmlit engine)"


def video_info(path: str) -> dict:
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, timeout=60)
    try:
        return {"duration": float(r.stdout.strip())}
    except Exception:
        return {"duration": 0.0}
