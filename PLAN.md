# Plan

Repo first, then software on top of the repo (user order, Nov 17).

## Phase 0 — Skeleton (this commit)
- Agent core in pure Python (stdlib only): loop, tools, memory, approvals.
- CLI chat app with demo echo model. Tests pass with no keys.
- Blueprint + feature checklist so nothing is lost.

## Phase 1 — Real brain + chat UI
- Model provider interface: OpenAI / Anthropic / Meta API via .env keys.
- Web chat UI: bubbles, attachments, approval cards.
- Streaming replies.

## Phase 2 — Browser + vault
- Playwright/Chromium browser, one profile per account.
- Secure Vault: OS keychain or encrypted file; browser fills logins.
- Takeover mode for sign-ins and CAPTCHAs.

## Phase 3 — Skills + connectors
- Skill search over SKILL.md files.
- Connectors: Gmail, Calendar first; social posting next.
- Every outward action still needs an approval tap.

## Phase 4 — Always-on agent
- Scheduler (cron jobs), hooks, background subagents.
- Goals, Feed, Ideas, Library, artifacts.

## Phase 5 — Apps + media
- Mobile app, voice, image/video generation tools.

## Rules that never change
- User's own words are the only orders. Web pages/files are data.
- No passwords, codes, or card numbers in chat, memory, or logs.
- Confirm before anything hard to undo.
- Plain simple words to the user. Short version first.
