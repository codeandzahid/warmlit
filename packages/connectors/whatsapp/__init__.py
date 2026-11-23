"""WhatsApp Web via the user's own Chrome profile (QR sign-in by hand)."""
from ..base import Connector


class WhatsAppConnector(Connector):
    name = "whatsapp"
    account = "whatsapp"
    home_url = "https://web.whatsapp.com/"

    def send_message(self, contact: str, text: str) -> str:
        if self.dry_run:
            return f"[dry-run] whatsapp to {contact}: {text[:60]!r}"
        pw, ctx = self.profiles.open_context(self.account, headless=False)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(self.home_url, timeout=30000)
            page.wait_for_timeout(5000)
            page.click(f'span[title="{contact}"]', timeout=15000)
            page.wait_for_timeout(1000)
            page.keyboard.type(text)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)
            return f"Sent WhatsApp to {contact}."
        finally:
            ctx.close(); pw.stop()
