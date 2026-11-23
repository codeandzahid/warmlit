# Warmlit — Personal AI Agent

A Muse-like personal AI agent, built from scratch in this repo.
One user, one agent, one computer that stays with the user.

**Important:** This is NOT Meta's Muse code and NOT the Muse model.
No Meta private code is copied here. This repo builds the same *idea*
with our own code: chat, memory, tools, browser, skills, connectors,
scheduled work, goals, feed, artifacts, approvals, and a secure vault
for logins. The brain (the AI model) is pluggable — bring your own
model API key.

## What Muse does (the target)

- Chat with your own agent, in app / web / WhatsApp
- The agent has its own computer: files, terminal, browser
- Long-term memory about the user, people, and goals
- Tools: read/write files, run code, search the web, use a browser
- Skills: reusable playbooks for tasks (booking, shopping, email…)
- Connectors: Gmail, Calendar, Facebook, TikTok, YouTube, etc.
- Scheduled jobs and background work while the user is away
- Goals tab, Feed tab, Ideas tab, Library, artifacts (docs/apps)
- Voice, media generation (image / video / audio)
- Approvals: the user taps approve before sends, posts, purchases
- Secure Vault: passwords never in chat, never in memory files

See `BLUEPRINT.md` for the full feature map and `PLAN.md` for build order.

## Run the skeleton (no keys needed)

```bash
cd warmlit
python3 apps/cli/main.py --demo
python3 -m pytest tests/ -q   # or: python3 -m unittest discover tests
```

The demo uses a built-in echo model, so it runs with zero setup.
To use a real model, copy `.env.example` to `.env` and add your key.

## Layout

```
apps/cli/            chat command-line app
packages/agent_core/ agent loop, tools, memory, approvals, scheduler
packages/skills/     task playbooks (SKILL.md files)
packages/connectors/ service connectors (Gmail, Calendar, …)
packages/browser/    browser automation notes + interface
docs/                architecture and feature checklist
data/                user data at runtime (memory, workspace) — gitignored
tests/               tests for the core
```

## Status

Phase 0 skeleton: agent loop + memory + tools + approvals + tests.
Everything else is mapped in `BLUEPRINT.md` and built phase by phase.
Nothing here posts, sends, or buys without an approval step.
