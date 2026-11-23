"""Warmlit Video Model config — tiny by default so it runs on a normal PC.

Architecture follows the public latent-video-diffusion design
(text encoder -> DiT denoiser in VAE latent space -> VAE decoder),
as used by Wan / LTX / CogVideoX / Open-Sora. Written from scratch.
"""
from dataclasses import dataclass


@dataclass
class VideoModelConfig:
    # video
    frames: int = 16
    height: int = 64
    width: int = 64
    fps: int = 8
    # VAE latent
    latent_channels: int = 8
    vae_downsample_spatial: int = 4   # 64 -> 16
    vae_downsample_temporal: int = 2  # 16 -> 8
    vae_base_channels: int = 32
    # text encoder (char-level, fully self-contained)
    text_max_len: int = 64
    text_dim: int = 256
    text_layers: int = 2
    text_heads: int = 4
    # DiT denoiser
    dit_hidden: int = 256
    dit_depth: int = 6
    dit_heads: int = 4
    patch_temporal: int = 1
    patch_spatial: int = 2
    # flow matching
    cfg_dropout: float = 0.1  # caption dropout for classifier-free guidance

    @property
    def latent_frames(self) -> int:
        return self.frames // self.vae_downsample_temporal

    @property
    def latent_h(self) -> int:
        return self.height // self.vae_downsample_spatial

    @property
    def latent_w(self) -> int:
        return self.width // self.vae_downsample_spatial

    @property
    def num_tokens(self) -> int:
        t = self.latent_frames // self.patch_temporal
        h = self.latent_h // self.patch_spatial
        w = self.latent_w // self.patch_spatial
        return t * h * w
