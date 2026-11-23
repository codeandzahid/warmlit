"""WarmlitVideoModel: text encoder + DiT + VAE, trained and run locally."""
import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import VideoModelConfig
from .dit import VideoDiT
from .scheduler import add_noise, euler_sample, sample_timesteps, velocity_target
from .text_encoder import TextEncoder
from .vae import VideoVAE


class WarmlitVideoModel(nn.Module):
    def __init__(self, cfg: VideoModelConfig | None = None):
        super().__init__()
        self.cfg = cfg or VideoModelConfig()
        self.vae = VideoVAE(self.cfg.latent_channels, self.cfg.vae_base_channels)
        self.text_encoder = TextEncoder(self.cfg.text_dim, self.cfg.text_layers,
                                        self.cfg.text_heads, self.cfg.text_max_len)
        self.dit = VideoDiT(self.cfg)

    def num_params(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def train_step(self, videos: torch.Tensor, captions: list[str],
                   vae_weight: float = 1.0, kl_weight: float = 1e-4) -> dict:
        """One joint training step. videos: [B,3,T,H,W] in [-1,1]."""
        # VAE loss
        recon, kl = self.vae(videos)
        vae_loss = F.mse_loss(recon, videos) + kl_weight * kl
        # Flow-matching loss in latent space (latent detached from VAE graph
        # is fine for the tiny joint setup; VAE still learns from recon loss)
        with torch.no_grad():
            latents = self.vae.encode_latent(videos)
        # caption dropout for CFG
        caps = ["" if torch.rand(()) < self.cfg.cfg_dropout else c for c in captions]
        text = self.text_encoder(caps)
        t = sample_timesteps(videos.shape[0], videos.device)
        noise = torch.randn_like(latents)
        noisy = add_noise(latents, noise, t)
        pred_v = self.dit(noisy, t, text)
        flow_loss = F.mse_loss(pred_v, velocity_target(latents, noise))
        loss = vae_weight * vae_loss + flow_loss
        return {"loss": loss, "vae": vae_loss.detach(), "flow": flow_loss.detach()}

    @torch.no_grad()
    def generate(self, prompt: str, steps: int = 20, cfg_scale: float = 3.0,
                 device: str = "cpu") -> torch.Tensor:
        """Prompt -> video frames [1,3,T,H,W] in [-1,1]."""
        self.eval()
        text_cond = self.text_encoder([prompt])
        text_uncond = self.text_encoder([""])
        shape = (1, self.cfg.latent_channels, self.cfg.latent_frames,
                 self.cfg.latent_h, self.cfg.latent_w)
        z = euler_sample(lambda zz, tt, tx: self.dit(zz, tt, tx), shape,
                         text_cond, text_uncond, steps=steps, cfg_scale=cfg_scale, device=device)
        return self.vae.decode(z)

    def save(self, path: str):
        torch.save({"cfg": self.cfg.__dict__, "state": self.state_dict()}, path)

    @classmethod
    def load(cls, path: str, device: str = "cpu"):
        ckpt = torch.load(path, map_location=device, weights_only=False)
        model = cls(VideoModelConfig(**ckpt["cfg"]))
        model.load_state_dict(ckpt["state"])
        return model.to(device)
