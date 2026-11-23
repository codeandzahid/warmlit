"""Real-photo AI video backend for Warmlit (local, no Meta, no API key).

Uses open pretrained text-to-video models via HuggingFace diffusers
(LTX-Video by default) running on YOUR computer. Warmlit ships the
code; the model weights download once on your PC when you install.

480p LITE MODE (owner order Nov 23): output is locked to 480p
(832x480) to fit small hardware. Low-memory settings are always on:
model CPU offload, VAE tiling + slicing, attention slicing.

Hardware truth (from research, Nov 2026):
- Model weights alone are ~5GB+ (plus text encoder); 480p cuts the
  working memory, not the weight size. CPU offload keeps RAM use
  manageable on 16GB.
- CPU-only (e.g. Ryzen 5 3550H): works, but slow — estimate 1-3
  hours for a 3-second 480p clip. NVIDIA 8GB+: minutes.
- AMD on Windows: PyTorch runs on CPU (ROCm is Linux-only).

Enable with: VIDEO_BACKEND=realphoto  (REALPHOTO_MODEL=<hf id>)
"""
import os

WIDTH, HEIGHT = 832, 480  # 480p lite, locked


def available() -> tuple[bool, str]:
    try:
        import diffusers  # noqa: F401
        import torch  # noqa: F401
    except ImportError:
        return False, "diffusers/torch not installed — run install-realphoto first"
    return True, "ready"


def generate(prompt: str, out: str, model_id: str | None = None,
             seconds: float = 3.0, fps: int = 24) -> str:
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
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    pipe.vae.enable_slicing()
    pipe.enable_attention_slicing()
    frames = pipe(prompt=prompt, width=WIDTH, height=HEIGHT,
                  num_frames=int(seconds * fps),
                  num_inference_steps=20, guidance_scale=3.0).frames[0]
    export_to_video(frames, out, fps=fps)
    return f"made {out} (real-photo AI 480p lite, {model_id}, {device})"


def status() -> str:
    ok, why = available()
    if not ok:
        return f"real-photo: {why}"
    import torch
    gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none (CPU)"
    return f"real-photo: ready 480p lite, GPU={gpu}"
