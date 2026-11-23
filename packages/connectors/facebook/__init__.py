"""Facebook posting via the user's own signed-in Chrome profile."""
from ..base import Connector


class FacebookConnector(Connector):
    name = "facebook"
    account = "facebook"
    home_url = "https://www.facebook.com/"

    def post_text(self, text: str) -> str:
        if self.dry_run:
            return f"[dry-run] facebook post: {text[:80]!r}"
        pw, ctx = self.profiles.open_context(self.account, headless=False)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(self.home_url, timeout=30000)
            page.wait_for_timeout(3000)
            page.click('text=What\'s on your mind', timeout=10000)
            page.wait_for_timeout(1000)
            page.keyboard.type(text)
            page.click('div[aria-label="Post"]', timeout=10000)
            page.wait_for_timeout(3000)
            return "Posted to Facebook."
        finally:
            ctx.close(); pw.stop()

    def post_video(self, video_path: str, caption: str = "") -> str:
        if self.dry_run:
            return f"[dry-run] facebook video {video_path} caption={caption[:60]!r}"
        return "Video upload: open Facebook in your profile and use Create Reel — Warmlit video upload automation is experimental; see docs/connectors.md."
