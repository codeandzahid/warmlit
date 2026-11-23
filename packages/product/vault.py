"""Secure Vault (local): passwords/keys encrypted at rest, stdlib only.

Key = PBKDF2(password). Encryption = HMAC-SHA256 keystream XOR +
encrypt-then-MAC. The vault password is typed by the user at unlock
time only — never stored, never in chat, never in memory files.
Note: browser sign-ins do NOT use this vault; the user signs in by
hand in Chrome profiles. The vault is for API keys the owner chooses
to keep (Warmlit needs none by default).
"""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path


def _key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)


def _keystream(key: bytes, nonce: bytes, n: int) -> bytes:
    out, counter = b"", 0
    while len(out) < n:
        out += hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        counter += 1
    return out[:n]


class Vault:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data: dict):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def set(self, password: str, name: str, value: str) -> str:
        data = self._load()
        salt = base64.b64decode(data["salt"]) if "salt" in data else os.urandom(16)
        key = _key(password, salt)
        nonce = os.urandom(16)
        plain = value.encode()
        cipher = bytes(a ^ b for a, b in zip(plain, _keystream(key, nonce, len(plain))))
        mac = hmac.new(key, nonce + cipher, hashlib.sha256).hexdigest()
        data["salt"] = base64.b64encode(salt).decode()
        data.setdefault("items", {})[name] = {
            "nonce": base64.b64encode(nonce).decode(),
            "cipher": base64.b64encode(cipher).decode(),
            "mac": mac,
        }
        self._save(data)
        return f"Saved '{name}' in vault."

    def get(self, password: str, name: str) -> str:
        data = self._load()
        item = data.get("items", {}).get(name)
        if not item:
            raise KeyError(f"no vault item: {name}")
        key = _key(password, base64.b64decode(data["salt"]))
        nonce = base64.b64decode(item["nonce"])
        cipher = base64.b64decode(item["cipher"])
        if not hmac.compare_digest(item["mac"], hmac.new(key, nonce + cipher, hashlib.sha256).hexdigest()):
            raise ValueError("wrong vault password")
        return bytes(a ^ b for a, b in zip(cipher, _keystream(key, nonce, len(cipher)))).decode()

    def names(self) -> list[str]:
        return sorted(self._load().get("items", {}))
