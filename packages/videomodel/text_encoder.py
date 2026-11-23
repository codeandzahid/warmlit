"""Small char-level transformer text encoder (no downloads, no vocab files).

Big models use frozen T5/CLIP. Ours is tiny and trained with the model,
which is the honest from-scratch choice for a personal PC build.
"""
import torch
import torch.nn as nn

VOCAB_SIZE = 128  # ASCII


def tokenize(text: str, max_len: int) -> list[int]:
    if not text:
        text = " "  # empty caption (CFG uncond) must keep one real token
    ids = [min(ord(c), VOCAB_SIZE - 1) for c in text.lower()[:max_len]]
    ids += [0] * (max_len - len(ids))
    return ids


class TextEncoder(nn.Module):
    def __init__(self, dim=256, layers=2, heads=4, max_len=64):
        super().__init__()
        self.max_len = max_len
        self.emb = nn.Embedding(VOCAB_SIZE, dim)
        self.pos = nn.Embedding(max_len, dim)
        layer = nn.TransformerEncoderLayer(dim, heads, dim * 4, batch_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(layer, layers)
        self.norm = nn.LayerNorm(dim)

    def forward(self, texts: list[str]) -> torch.Tensor:
        device = self.emb.weight.device
        ids = torch.tensor([tokenize(t, self.max_len) for t in texts], device=device)
        pos = torch.arange(self.max_len, device=device).unsqueeze(0)
        h = self.emb(ids) + self.pos(pos)
        mask = ids == 0
        h = self.encoder(h, src_key_padding_mask=mask)
        return self.norm(h)  # [B, L, D]
