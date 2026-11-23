"""DiT denoiser: patchify latent -> transformer blocks -> predict velocity.

Block design (public DiT pattern): adaLN-Zero timestep modulation,
spatiotemporal self-attention, cross-attention to text tokens, MLP.
"""
import math

import torch
import torch.nn as nn
import torch.nn.functional as F


def timestep_embedding(t: torch.Tensor, dim: int) -> torch.Tensor:
    half = dim // 2
    freqs = torch.exp(-math.log(10000) * torch.arange(half, device=t.device) / half)
    args = t[:, None].float() * freqs[None]
    return torch.cat([args.sin(), args.cos()], dim=-1)


class DiTBlock(nn.Module):
    def __init__(self, hidden, heads, text_dim):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden, elementwise_affine=False)
        self.attn = nn.MultiheadAttention(hidden, heads, batch_first=True)
        self.norm2 = nn.LayerNorm(hidden, elementwise_affine=False)
        self.cross = nn.MultiheadAttention(hidden, heads, kdim=text_dim, vdim=text_dim, batch_first=True)
        self.norm3 = nn.LayerNorm(hidden, elementwise_affine=False)
        self.mlp = nn.Sequential(nn.Linear(hidden, hidden * 4), nn.GELU(), nn.Linear(hidden * 4, hidden))
        # adaLN-Zero: 9 params (shift/scale/gate x3), zero-init so blocks start as identity
        self.ada = nn.Sequential(nn.SiLU(), nn.Linear(hidden, hidden * 9))
        nn.init.zeros_(self.ada[1].weight)
        nn.init.zeros_(self.ada[1].bias)

    def forward(self, x, c, text):
        p = self.ada(c).unsqueeze(1)
        s1, sc1, g1, s2, sc2, g2, s3, sc3, g3 = p.chunk(9, dim=-1)
        h = self.norm1(x) * (1 + sc1) + s1
        h, _ = self.attn(h, h, h, need_weights=False)
        x = x + g1 * h
        h = self.norm2(x) * (1 + sc2) + s2
        h, _ = self.cross(h, text, text, need_weights=False)
        x = x + g2 * h
        h = self.norm3(x) * (1 + sc3) + s3
        x = x + g3 * self.mlp(h)
        return x


class VideoDiT(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        patch_dim = cfg.latent_channels * cfg.patch_temporal * cfg.patch_spatial * cfg.patch_spatial
        self.patchify = nn.Conv3d(cfg.latent_channels, cfg.dit_hidden,
                                  kernel_size=(cfg.patch_temporal, cfg.patch_spatial, cfg.patch_spatial),
                                  stride=(cfg.patch_temporal, cfg.patch_spatial, cfg.patch_spatial))
        self.pos = nn.Embedding(cfg.num_tokens, cfg.dit_hidden)
        self.time_mlp = nn.Sequential(nn.Linear(cfg.dit_hidden, cfg.dit_hidden), nn.SiLU(),
                                      nn.Linear(cfg.dit_hidden, cfg.dit_hidden))
        self.blocks = nn.ModuleList(
            DiTBlock(cfg.dit_hidden, cfg.dit_heads, cfg.text_dim) for _ in range(cfg.dit_depth))
        self.final_norm = nn.LayerNorm(cfg.dit_hidden, elementwise_affine=False)
        self.final_ada = nn.Sequential(nn.SiLU(), nn.Linear(cfg.dit_hidden, cfg.dit_hidden * 2))
        self.unpatchify = nn.Linear(cfg.dit_hidden, patch_dim)
        nn.init.zeros_(self.unpatchify.weight)
        nn.init.zeros_(self.unpatchify.bias)

    def forward(self, z, t, text):
        """z: [B,C,T,H,W] noisy latent, t: [B] in [0,1], text: [B,L,D] -> velocity [B,C,T,H,W]"""
        B, C, T, H, W = z.shape
        cfg = self.cfg
        x = self.patchify(z)  # [B,D,T',H',W']
        Tp, Hp, Wp = x.shape[2], x.shape[3], x.shape[4]
        x = x.flatten(2).transpose(1, 2)  # [B, L, D]
        x = x + self.pos(torch.arange(x.shape[1], device=z.device)).unsqueeze(0)
        c = self.time_mlp(timestep_embedding(t, cfg.dit_hidden))
        for block in self.blocks:
            x = block(x, c, text)
        shift, scale = self.final_ada(c).chunk(2, dim=-1)
        x = self.final_norm(x) * (1 + scale.unsqueeze(1)) + shift.unsqueeze(1)
        x = self.unpatchify(x)  # [B, L, patch_dim]
        pt, ps = cfg.patch_temporal, cfg.patch_spatial
        x = x.view(B, Tp, Hp, Wp, C, pt, ps, ps)
        x = x.permute(0, 4, 1, 5, 2, 6, 3, 7).reshape(B, C, Tp * pt, Hp * ps, Wp * ps)
        return x
