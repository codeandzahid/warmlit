"""Connector base: browser-based, no API keys.

Every connector uses the user's own signed-in Chrome profile.
Posting/sending is consequential: the Agent's approval gate runs
first. dry_run=True (default in tests) never touches the network.
"""
from pathlib import Path


class Connector:
    name = "base"
    account = "default"
    home_url = "about:blank"

    def __init__(self, profiles, dry_run: bool = False):
        self.profiles = profiles
        self.dry_run = dry_run

    def status(self) -> str:
        if self.dry_run:
            return f"{self.name}: dry-run (not connected)"
        try:
            pw, ctx = self.profiles.open_context(self.account, headless=True)
            try:
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
                page.goto(self.home_url, timeout=30000)
                text = page.inner_text("body")[:500].lower()
                signed_out = any(w in text for w in ["log in", "sign in", "login"])
                return f"{self.name}: {'signed out — sign in once by hand' if signed_out else 'looks signed in'}"
            finally:
                ctx.close(); pw.stop()
        except Exception as e:
            return f"{self.name}: cannot check ({e})"

    def signin(self) -> str:
        return self.profiles.open_for_signin(self.account, self.home_url)
