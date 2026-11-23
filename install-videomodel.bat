@echo off
REM Install PyTorch for the Warmlit Video Model (Windows, CPU build).
REM AMD GPU on Windows: PyTorch training uses CPU (ROCm training is Linux-only).
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
python -m pip install numpy pillow
echo Done. Train: python -m packages.videomodel.train --synthetic --steps 500
pause
