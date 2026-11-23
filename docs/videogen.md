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

For real diffusion quality on YOUR PC: install a local open video
model yourself, then set in `.env`:
`VIDEO_MODEL_CMD=your-command --prompt "{prompt}" --out "{out}"`
Warmlit will call it instead. (Note: heavy models need a strong GPU;
this code does not download any model by itself.)
