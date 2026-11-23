"""3D VAE: compresses video [B,3,T,H,W] to latent [B,C,T/2,H/4,W/4] and back."""
import torch
import torch.nn as nn
import torch.nn.functional as F


def _conv3d(cin, cout, stride=(1, 1, 1)):
    return nn.Conv3d(cin, cout, kernel_size=3, stride=stride, padding=1)


class ResBlock3d(nn.Module):
    def __init__(self, ch):
        super().__init__()
        self.norm1 = nn.GroupNorm(4, ch)
        self.conv1 = _conv3d(ch, ch)
        self.norm2 = nn.GroupNorm(4, ch)
        self.conv2 = _conv3d(ch, ch)

    def forward(self, x):
        h = self.conv1(F.silu(self.norm1(x)))
        h = self.conv2(F.silu(self.norm2(h)))
        return x + h


class VideoVAE(nn.Module):
    def __init__(self, latent_channels=8, base=32):
        super().__init__()
        # Encoder: spatial /4 (two stride-2), temporal /2 (one stride-2)
        self.enc = nn.Sequential(
            _conv3d(3, base),
            ResBlock3d(base),
            _conv3d(base, base * 2, stride=(1, 2, 2)),
            ResBlock3d(base * 2),
            _conv3d(base * 2, base * 2, stride=(2, 2, 2)),
            ResBlock3d(base * 2),
            nn.GroupNorm(4, base * 2),
            nn.SiLU(),
            _conv3d(base * 2, latent_channels * 2),  # mean + logvar
        )
        # Decoder mirrors encoder
        self.dec_in = _conv3d(latent_channels, base * 2)
        self.dec = nn.Sequential(
            ResBlock3d(base * 2),
            nn.Upsample(scale_factor=(2, 2, 2), mode="nearest"),
            _conv3d(base * 2, base * 2),
            ResBlock3d(base * 2),
            nn.Upsample(scale_factor=(1, 2, 2), mode="nearest"),
            _conv3d(base * 2, base),
            ResBlock3d(base),
            nn.GroupNorm(4, base),
            nn.SiLU(),
            _conv3d(base, 3),
        )

    def encode(self, x):
        """x: [B,3,T,H,W] in [-1,1] -> (mu, logvar)"""
        h = self.enc(x)
        mu, logvar = h.chunk(2, dim=1)
        return mu, logvar.clamp(-10, 10)

    def decode(self, z):
        return torch.tanh(self.dec(self.dec_in(z)))

    def forward(self, x):
        mu, logvar = self.encode(x)
        std = torch.exp(0.5 * logvar)
        z = mu + std * torch.randn_like(std)
        recon = self.decode(z)
        kl = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
        return recon, kl

    @torch.no_grad()
    def encode_latent(self, x):
        mu, _ = self.encode(x)
        return mu
