"""Browser profiles: one persistent Chrome profile per account.

The user signs in ONCE by hand in that profile. Warmlit never sees
or stores the password. After that, connectors reuse the profile.
No API keys anywhere.
"""
from pathlib import Path

CHROME_CANDIDATES = [
    Path.home() / "workspace/chrome-home/opt/google/chrome/chrome",
    Path("/usr/bin/google-chrome"),
    Path("/usr/bin/chromium"),
]


def chrome_path() -> str | None:
    for p in CHROME_CANDIDATES:
        if p.exists():
            return str(p)
    return None


class ProfileManager:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def profile_dir(self, account: str) -> Path:
        d = self.root / account
        d.mkdir(parents=True, exist_ok=True)
        return d

    def list_profiles(self) -> list[str]:
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())

    def open_context(self, account: str, headless: bool = True):
        """Return (playwright, context). Caller must close both."""
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        kwargs = {"headless": headless}
        exe = chrome_path()
        if exe:
            kwargs["executable_path"] = exe
        ctx = pw.chromium.launch_persistent_context(str(self.profile_dir(account)), **kwargs)
        return pw, ctx

    def open_for_signin(self, account: str, url: str) -> str:
        """Open a visible browser so the USER can sign in by hand.
        Warmlit does not type any password."""
        pw, ctx = self.open_context(account, headless=False)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(url, timeout=60000)
            return f"Browser opened for {account} at {url}. Sign in by hand, then close the window."
        finally:
            ctx.close()
            pw.stop()
