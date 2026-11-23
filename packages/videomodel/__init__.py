"""Warmlit Video Model — from-scratch latent text-to-video diffusion.

Requires PyTorch (see requirements-videomodel.txt). The rest of
Warmlit stays stdlib-only; this package is imported lazily.
"""
from .config import VideoModelConfig
from .model import WarmlitVideoModel

__all__ = ["VideoModelConfig", "WarmlitVideoModel"]
