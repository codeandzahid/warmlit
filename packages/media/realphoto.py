"""Real-photo AI video backend for Warmlit (local, no Meta, no API key).

Uses open pretrained text-to-video models via HuggingFace diffusers
(e.g. LTX-Video, Wan) running on YOUR computer. Warmlit ships the
code; the model weights download once on your PC when you install.

Hardware truth (from research, Nov 2026):
- No open real-photo model runs natively in 4GB VRAM.
  Floors: Wan 2.1-1.3B ~8.2GB, SVD <8GB with tricks, LTX ~12-16GB class.
- CPU offload works but is very slow (a 5s clip can take hours).
- AMD cards on Windows: PyTorch uses CPU (ROCm training/inference
  stack is Linux-only). NVIDIA 8GB+ is the practical minimum.

Enable with: VIDEO_BACKEND=realphoto  (and REALPHOTO_MODEL=<hf id>)
"""
import os
from pathlib import Path


def available() -> tuple[bool, str]:
    try:
        import diffusers  # noqa: F401
        import torch  # noqa: F401
    except ImportError:
        return False, "diffusers/torch not installed — run install-realphoto first"
    return True, "ready"


def generate(prompt: str, out: str, model_id: str | None = None,
             seconds: float = 5.0, fps: int = 24) -> str:
    ok, why = available()
    if not ok:
        raise RuntimeError(f"real-photo backend not ready: {why}")
    import torch
    from diffusers import LTXPipeline
    from diffusers.utils import export_to_video

    model_id = model_id or os.environ.get("REALPHOTO_MODEL", "Lightricks/LTX-Video")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.bfloat16 if device == "cuda" else torch.float32
    pipe = LTXPipeline.from_pretrained(model_id, torch_dtype=dtype)
    if device == "cuda":
        pipe.enable_model_cpu_offload()
    else:
        pipe.to("cpu")
    frames = pipe(prompt=prompt, num_frames=int(seconds * fps),
                  num_inference_steps=20, guidance_scale=3.0).frames[0]
    export_to_video(frames, out, fps=fps)
    return f"made {out} (real-photo AI, {model_id}, {device})"


def status() -> str:
    ok, why = available()
    if not ok:
        return f"real-photo: {why}"
    import torch
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none (CPU)"
    return f"real-photo: ready, GPU={gpu}"
