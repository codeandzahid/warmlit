"""Free vs Paid plans + local license keys.

FREE: chat, memory, read files, web fetch, skills search. Daily limit.
PAID: everything, including local system tasks — write files, run
shell, open Chrome browser, scheduler jobs, connectors.

License: owner generates a key file with tools/make_key.py and gives
it to the buyer after payment (payment itself happens outside this
code, e.g. PayPal — no card data ever touches Warmlit).
Key file: data/license.json  {"plan":"paid","expires":"YYYY-MM-DD","sig":"..."}
Signature = HMAC-SHA256 with LICENSE_SECRET from .env (owner-only).
A bad or expired key means Free. No internet needed to check.
"""
import hashlib
import hmac
import json
import os
from datetime import date, timedelta
from pathlib import Path

FREE_TOOLS = {"read_file", "list_files", "web_fetch", "skills_search"}
PAID_ONLY_TOOLS = {"write_file", "run_shell", "browser_open"}


def _secret() -> str:
    return os.environ.get("LICENSE_SECRET", "warmlit-dev-secret-change-me")


def sign(plan: str, expires: str) -> str:
    msg = f"{plan}|{expires}".encode()
    return hmac.new(_secret().encode(), msg, hashlib.sha256).hexdigest()


def make_license(days: int = 30, plan: str = "paid") -> dict:
    expires = (date.today() + timedelta(days=days)).isoformat()
    return {"plan": plan, "expires": expires, "sig": sign(plan, expires)}


def check_license(path: str | Path) -> dict:
    """Return {'plan': 'free'|'paid', 'expires': str|None, 'days_left': int}"""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        plan, expires, sig = data["plan"], data["expires"], data["sig"]
        if not hmac.compare_digest(sig, sign(plan, expires)):
            return {"plan": "free", "expires": None, "days_left": 0}
        days_left = (date.fromisoformat(expires) - date.today()).days
        if plan == "paid" and days_left >= 0:
            return {"plan": "paid", "expires": expires, "days_left": days_left}
    except Exception:
        pass
    return {"plan": "free", "expires": None, "days_left": 0}


class UsageCounter:
    """Daily message counter for the Free plan."""

    def __init__(self, path: str | Path, daily_limit: int | None = None):
        self.path = Path(path)
        self.limit = daily_limit if daily_limit is not None else int(os.environ.get("FREE_DAILY_LIMIT", "50"))

    def _load(self) -> dict:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def count_today(self) -> int:
        return int(self._load().get(date.today().isoformat(), 0))

    def add(self) -> int:
        data = self._load()
        today = date.today().isoformat()
        data[today] = int(data.get(today, 0)) + 1
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return data[today]

    def over_limit(self) -> bool:
        return self.count_today() >= self.limit
