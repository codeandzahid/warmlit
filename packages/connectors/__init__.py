from .base import Connector
from .facebook import FacebookConnector
from .gmail import GmailConnector
from .tiktok import TikTokConnector
from .whatsapp import WhatsAppConnector
from .youtube import YouTubeConnector


def all_connectors(profiles, dry_run: bool = False) -> dict:
    return {
        "gmail": GmailConnector(profiles, dry_run=dry_run),
        "facebook": FacebookConnector(profiles, dry_run=dry_run),
        "tiktok": TikTokConnector(profiles, dry_run=dry_run),
        "youtube": YouTubeConnector(profiles, dry_run=dry_run),
        "whatsapp": WhatsAppConnector(profiles, dry_run=dry_run),
    }
