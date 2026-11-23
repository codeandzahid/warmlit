@echo off
REM Warmlit real-photo AI video (Windows).
REM WARNING: needs NVIDIA GPU 8GB+ for usable speed. AMD/CPU = very slow.
REM First run downloads model weights (several GB) from HuggingFace.
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cu121
python -m pip install diffusers transformers accelerate imageio imageio-ffmpeg
echo Done. Set VIDEO_BACKEND=realphoto then ask Warmlit to make a video.
pause
