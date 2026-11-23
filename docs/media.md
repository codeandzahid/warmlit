# Media making — local, no keys

## Video (ffmpeg on your computer)
- Slideshow video from images: `/call make_slideshow {"images":"a.png,b.png","out":"v.mp4"}`
- Text video: `make a text video that says Hello`
- Library code also: trim, join, resize to 9:16, add audio
  (`packages/media/video.py`).

## Images (PIL)
- Poster: `make a poster that says <text>`
- YouTube thumbnail: `make a thumbnail that says <text>`

## Voice (no key)
- Web UI: 🎤 Talk (mic), 🔊 Speak (reads reply), ⏺ Voice note
  (records and saves to data/workspace/voice-notes/).
- `say <text>` uses espeak-ng if installed, else tells you plainly.

## AI image/video generation
Not built in — it needs a big local model (your PC GPU) or an API
key. Warmlit never fakes it. If you add a local model later, plug
it in as a new tool in `packages/media/`.
