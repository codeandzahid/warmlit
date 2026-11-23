# Video Model Research — what we read, what we built

Built from public research on how text-to-video diffusion models
work (papers/model cards for Wan, LTX-Video, CogVideoX, HunyuanVideo,
Open-Sora, Stable Video Diffusion, DiT, Latte, Drishya/MiniDance).
No Meta code or weights are used anywhere.

## How these models work
1. **Text encoder** (frozen in big models: T5/CLIP/umT5) turns the
   prompt into token embeddings.
2. **3D VAE** compresses video to a small latent grid
   (e.g. 4x temporal, 8x spatial, 16 channels in Wan-VAE).
3. **DiT denoiser** (Diffusion Transformer) iteratively denoises
   Gaussian noise in latent space: patchify -> transformer blocks
   (adaLN-Zero timestep modulation, spatiotemporal self-attention,
   text cross-attention) -> unpatchify. It predicts noise (DDPM) or
   velocity (flow matching: x_t = t*x1 + (1-t)*x0, v = x1 - x0).
4. **Sampler**: Euler/DDIM steps from noise to clean latent, with
   classifier-free guidance (train with 10% caption dropout;
   sample v = v_uncond + w*(v_cond - v_uncond)).
5. **VAE decoder** turns latents back into frames.

## What Warmlit built (packages/videomodel/)
Same design, tiny scale, from scratch in PyTorch:
- `vae.py` — 3D VAE, 2x temporal + 4x spatial compression, 8ch latent
- `text_encoder.py` — small char-level transformer (no downloads)
- `dit.py` — DiT with adaLN-Zero, self-attention + text cross-attention
- `scheduler.py` — rectified flow matching + Euler sampler with CFG
- `model.py` — joint training step + generate()
- `data.py` — your video folder, or synthetic moving-shape clips
- `train.py` / `generate.py` — train and generate on your PC
- Default size: 64x64, 16 frames, ~10-15M params (CPU-trainable toy)

## Honest limits (from the research)
- Flagship models train on billions of clips with datacenter GPUs.
  A general photoreal text-to-video model CANNOT be trained from
  scratch on one home PC.
- Smallest documented from-scratch successes rented one GPU for
  11-15 hours (MiniDance ~120M params scenery-only; Drishya Tiny
  212M, 256px, still weak on faces/text/multi-object scenes).
- On a 16GB RAM / 4GB AMD PC: AMD ROCm training is Linux-only and
  most 4GB cards are unsupported — treat it as CPU training.
  Realistic: narrow-domain/simple motion at 64px, days of training
  for visible learning. The code is the real system; quality grows
  with your data + training time.
- No open model runs inference natively in 4GB VRAM (floors:
  Wan-1.3B ~8.2GB, SVD <8GB with tricks, Wan2.2-5B GGUF ~6GB).

## Use it
```
install-videomodel.bat        (Windows)  /  ./install-videomodel.sh
python -m packages.videomodel.train --synthetic --steps 500 --out ckpt.pt
python -m packages.videomodel.generate --ckpt ckpt.pt --prompt "red circle moves right" --out out.mp4
```
Your own data: folder of clip.mp4 + clip.txt (caption per clip),
then `--data that-folder`.
