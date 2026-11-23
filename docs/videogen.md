# Warmlit Video Generation — cloned, not Meta

Warmlit has its OWN video generation. It never calls Meta or any
cloud video service.

## Use
In chat: `make a video about a man walks to a house then a car drives`
or `/call generate_video {"prompt":"...","out":"v.mp4"}`

Prompt rules:
- Split scenes with `then` or `.` — each scene is ~4 seconds.
- Words it understands: house/village, car/drive/road, boat/sea/
  river/lake, night/moon, tree, walk (a figure walks by default).
- Output: vertical 720x1280 MP4 with captions.

## Honest limits
The built-in engine draws animated 2D scenes locally (no GPU, no
key). It is NOT photoreal AI diffusion like Meta's generator.

## Real-photo AI (added Nov 23 on owner order)
Backend: `packages/media/realphoto.py` — open pretrained
text-to-video model (LTX-Video by default) via diffusers, on your
PC, no Meta, no API key. Install: `install-realphoto.bat` /
`./install-realphoto.sh`, then set `VIDEO_BACKEND=realphoto`.
First run downloads weights (several GB).

480p LITE MODE (owner order Nov 23): output locked to 832x480,
low-memory settings always on (CPU offload, VAE tiling/slicing,
attention slicing). 480p cuts working memory, not weight size
(weights ~5GB+). CPU-only estimate: 1-3 hours per 3s clip.
NVIDIA 8GB+: minutes. AMD on Windows runs on CPU.

Also supported: `VIDEO_MODEL_CMD=your-command --prompt "{prompt}"
--out "{out}"` in `.env` for any other local model command.
