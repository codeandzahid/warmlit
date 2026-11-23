#!/usr/bin/env bash
# Install PyTorch for the Warmlit Video Model (Linux/macOS, CPU build).
set -e
python3 -m pip install --upgrade pip
python3 -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python3 -m pip install numpy pillow
echo "Done. Train: python3 -m packages.videomodel.train --synthetic --steps 500"
