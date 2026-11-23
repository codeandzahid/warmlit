#!/usr/bin/env bash
# Warmlit real-photo AI video (Linux/macOS).
# WARNING: needs NVIDIA GPU 8GB+ for usable speed. CPU = very slow.
# First run downloads model weights (several GB) from HuggingFace.
set -e
python3 -m pip install --upgrade pip
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python3 -m pip install diffusers transformers accelerate imageio imageio-ffmpeg
echo "Done. Set VIDEO_BACKEND=realphoto then ask Warmlit to make a video."
