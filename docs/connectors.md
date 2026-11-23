# Connectors — no API keys, your own sign-in

Warmlit connectors use Chrome profiles on YOUR computer.
No API keys. Warmlit never sees your password.

## Set up (once per account)
In chat: `/signin gmail` (or facebook / tiktok / youtube / whatsapp)
A Chrome window opens. YOU sign in by hand. Close it. Done.
Check later with `/connectors`.

## Use (approval first, always)
- Gmail: `/call gmail_search {"query":"invoice"}` ·
  `/call gmail_send {"to":"a@b.c","subject":"Hi","body":"..."}`
- Facebook: `post to facebook <text>`
- TikTok: `/call tiktok_upload {"video":"v.mp4","caption":"..."}`
- YouTube: `/call youtube_upload {"video":"v.mp4","title":"..."}`
- WhatsApp: `/call whatsapp_send {"contact":"Mom","text":"hi"}`

Site pages change often, so posting automation can break when a
site changes its buttons. If a post fails, Warmlit says so plainly —
it never claims a post went live without checking.
