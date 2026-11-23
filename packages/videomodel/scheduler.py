"""Rectified flow matching scheduler + Euler sampler with CFG.

Training path: x_t = t*x1 + (1-t)*x0, target velocity v = x1 - x0.
Sampling: Euler ODE steps from noise (t=0) to data (t=1), with
classifier-free guidance v = v_uncond + w*(v_cond - v_uncond).
"""
import torch


def sample_timesteps(batch, device):
    # logit-normal-ish: uniform is fine for the tiny model
    return torch.rand(batch, device=device)


def add_noise(x1, x0, t):
    tt = t.view(-1, 1, 1, 1, 1)
    return tt * x1 + (1 - tt) * x0


def velocity_target(x1, x0):
    return x1 - x0


@torch.no_grad()
def euler_sample(model_fn, shape, text_cond, text_uncond, steps=20, cfg_scale=3.0, device="cpu"):
    """model_fn(z, t, text) -> velocity. Returns clean latent."""
    z = torch.randn(shape, device=device)
    dt = 1.0 / steps
    for i in range(steps):
        t = torch.full((shape[0],), i * dt, device=device)
        v_cond = model_fn(z, t, text_cond)
        if cfg_scale != 1.0:
            v_uncond = model_fn(z, t, text_uncond)
            v = v_uncond + cfg_scale * (v_cond - v_uncond)
        else:
            v = v_cond
        z = z + dt * v
    return z
