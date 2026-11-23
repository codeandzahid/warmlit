"""TikTok upload via the user's own signed-in Chrome profile."""
from ..base import Connector


class TikTokConnector(Connector):
    name = "tiktok"
    account = "tiktok"
    home_url = "https://www.tiktok.com/upload"

    def upload_video(self, video_path: str, caption: str = "") -> str:
        if self.dry_run:
            return f"[dry-run] tiktok upload {video_path} caption={caption[:60]!r}"
        pw, ctx = self.profiles.open_context(self.account, headless=False)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(self.home_url, timeout=30000)
            page.wait_for_timeout(3000)
            page.set_input_files('input[type="file"]', video_path)
            page.wait_for_timeout(5000)
            if caption:
                page.fill('div[contenteditable="true"]', caption)
            page.click('button:has-text("Post")', timeout=15000)
            page.wait_for_timeout(5000)
            return "Uploaded to TikTok."
        finally:
            ctx.close(); pw.stop()
