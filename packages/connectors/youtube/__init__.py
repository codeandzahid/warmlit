"""YouTube upload via Studio in the user's own Chrome profile."""
from ..base import Connector


class YouTubeConnector(Connector):
    name = "youtube"
    account = "youtube"
    home_url = "https://studio.youtube.com/"

    def upload_video(self, video_path: str, title: str, description: str = "") -> str:
        if self.dry_run:
            return f"[dry-run] youtube upload {video_path} title={title!r}"
        pw, ctx = self.profiles.open_context(self.account, headless=False)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(self.home_url, timeout=30000)
            page.wait_for_timeout(3000)
            page.click('#create-icon', timeout=10000)
            page.click('text=Upload videos', timeout=10000)
            page.set_input_files('input[type="file"]', video_path)
            page.wait_for_timeout(5000)
            page.fill('#textbox', title)
            page.click('#next-button', timeout=10000)
            page.wait_for_timeout(2000)
            page.click('#next-button', timeout=10000)
            page.wait_for_timeout(2000)
            page.click('#next-button', timeout=10000)
            page.wait_for_timeout(2000)
            page.click('tp-yt-paper-radio-button[name="PUBLIC"]', timeout=10000)
            page.click('#done-button', timeout=10000)
            page.wait_for_timeout(3000)
            return f"Uploaded to YouTube: {title}"
        finally:
            ctx.close(); pw.stop()
