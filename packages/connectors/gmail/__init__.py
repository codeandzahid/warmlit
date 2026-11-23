"""Gmail via the user's own signed-in Chrome profile (no API key)."""
from ..base import Connector


class GmailConnector(Connector):
    name = "gmail"
    account = "gmail"
    home_url = "https://mail.google.com/mail/u/0/#inbox"

    def search(self, query: str) -> str:
        if self.dry_run:
            return f"[dry-run] gmail search: {query}"
        pw, ctx = self.profiles.open_context(self.account, headless=True)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto(f"https://mail.google.com/mail/u/0/#search/{query}", timeout=30000)
            page.wait_for_timeout(3000)
            return page.inner_text("body")[:4000]
        finally:
            ctx.close(); pw.stop()

    def send(self, to: str, subject: str, body: str) -> str:
        if self.dry_run:
            return f"[dry-run] gmail send to={to} subject={subject!r}"
        pw, ctx = self.profiles.open_context(self.account, headless=False)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://mail.google.com/mail/u/0/#inbox?compose=new", timeout=30000)
            page.wait_for_timeout(3000)
            page.fill('input[name="to"]', to)
            page.fill('input[name="subjectbox"]', subject)
            page.fill('div[aria-label="Message Body"]', body)
            page.click('div[aria-label="Send"]')
            page.wait_for_timeout(2000)
            return f"Sent to {to}"
        finally:
            ctx.close(); pw.stop()
