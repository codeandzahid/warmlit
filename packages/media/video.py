"""Video making with local ffmpeg — no keys, no cloud."""
import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout)[-800:])
    return "ok"


def make_slideshow(images: list[str], out: str, seconds_each: float = 3.0, size: str = "720x1280") -> str:
    """Images -> vertical video (old-style image slides + crossfades via plain cuts)."""
    if not images:
        raise ValueError("no images")
    w, h = size.split("x")
    inputs, filters = [], []
    for i, img in enumerate(images):
        inputs += ["-loop", "1", "-t", str(seconds_each), "-i", img]
        filters.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}]")
    concat = "".join(f"[v{i}]" for i in range(len(images))) + f"concat=n={len(images)}:v=1:a=0[out]"
    _run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters + [concat]),
          "-map", "[out]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", out])
    return f"made {out}"


def make_text_video(text: str, out: str, seconds: float = 5.0, size: str = "720x1280") -> str:
    safe = text.replace("'", "").replace(":", " ")[:120]
    vf = f"drawtext=text='{safe}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2"
    _run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={size}:d={seconds}:r=30",
          "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", out])
    return f"made {out}"


def trim_video(src: str, out: str, start: float = 0, duration: float | None = None) -> str:
    cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", src]
    if duration:
        cmd += ["-t", str(duration)]
    cmd += ["-c:v", "libx264", "-c:a", "aac", "-preset", "veryfast", out]
    _run(cmd)
    return f"made {out}"


def join_videos(parts: list[str], out: str) -> str:
    list_file = Path(out).with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{Path(p).resolve()}'" for p in parts))
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", out])
    list_file.unlink(missing_ok=True)
    return f"made {out}"


def resize_video(src: str, out: str, size: str = "720x1280") -> str:
    w, h = size.split("x")
    _run(["ffmpeg", "-y", "-i", src, "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2",
          "-c:v", "libx264", "-c:a", "aac", "-preset", "veryfast", out])
    return f"made {out}"


def add_audio(video: str, audio: str, out: str) -> str:
    _run(["ffmpeg", "-y", "-i", video, "-i", audio, "-c:v", "copy", "-c:a", "aac",
          "-map", "0:v:0", "-map", "1:a:0", "-shortest", out])
    return f"made {out}"
