# Warmlit — Personal AI Agent

A Muse-like personal AI agent, built from scratch in this repo.
One user, one agent, one computer that stays with the user.

**Important:** This is NOT Meta's Muse code and NOT the Muse model.
No Meta private code is copied here. This repo builds the same *idea*
with our own code. The brain (the AI model) is pluggable — bring your
own model API key, or run a free local model with Ollama.

## Run it locally (works now)

Linux / macOS:
```bash
cd warmlit
./run.sh
```
Windows: double-click `run.bat`

Then open http://localhost:8765

No keys needed to start: the demo echo model runs, and these
commands work right away in the chat box:

```
/remember I like tea
/search tea
/tools
/files
/read note.txt
/write note.txt hello      (approval card appears)
/run echo hi               (approval card appears)
/web https://example.com
/browser https://example.com
/skills example
/job every:60s /remember tick
/jobs
```

CLI version: `python3 apps/cli/main.py`
Tests: `python3 -m unittest discover tests`

## No keys needed — entire system works without keys

Default brain = built-in LocalBrain: tasks, memory, math, time,
files, shell, web — zero keys, zero installs, works offline.

For full free-form AI chat, still NO key: run `install-ollama.sh`
(or `install-ollama.bat` on Windows). It installs Ollama + a small
free model (~1 GB). Warmlit finds it alone and uses it.

An API key is optional only (OpenAI / Meta Model API / etc.):
copy `.env.example` to `.env` and set it there. Never put keys in
chat. `.env` is gitignored.

## Owner only — everything unlocked

Warmlit is personal, for the owner only. Not for sale, no price.
Everything is ON: unlimited chat, memory, files, shell, Chrome,
scheduled jobs — local system tasks included, still with approval
taps for risky actions. See `docs/plans.md`.

## What works today

- Web chat UI + CLI chat, with approval cards (Approve / Deny)
- Memory: save + search notes (markdown files)
- Tools: read/write/list files, run shell (approval), fetch web
  pages, open pages in local Chrome, search skills
- Scheduler: jobs that actually run (`every:60s`, `daily@09:15`)
- Model providers: built-in LocalBrain (no key), Ollama local
  (no key), OpenAI-compatible API (optional key)
- Goals, Feed, Ideas, Library panels + commands
- Artifacts: HTML docs, slide decks, CSV sheets
- Connectors (your own Chrome sign-in, no API keys): Gmail,
  Facebook, TikTok, YouTube, WhatsApp — see `docs/connectors.md`
- Voice in web UI: talk (mic), speak replies, voice notes
- Video making (ffmpeg): slideshow, text video, trim, join, resize
- Image making: posters, YouTube thumbnails
- Secure vault: encrypted local storage for keys you choose to keep
- Hooks (watch file/URL) and subagents (background tasks)
- Mobile app: installable PWA — open http://localhost:8765 on your
  phone (same Wi-Fi), then "Add to Home Screen"
- 23 tests, all passing

## Cannot be copied (Meta services)

- Muse's own model (Wonder) — use Ollama locally, or a Meta Model
  API key in `.env` if you get one
- Muse Mail (@muse.ai) — use your own Gmail connector instead
- Real payments/wallet — Warmlit opens the shop site; you pay yourself
- AI image/video generation — needs a big local model or a key;
  Warmlit makes videos from images/text with ffmpeg instead
- Browser note: on some cloud VMs headless Chrome cannot reach the
  internet (tunnel error). On a normal PC it works. `web_fetch`
  works everywhere.

See `BLUEPRINT.md` for the full Muse feature map and `PLAN.md`.

## Layout

```
apps/web/            local web UI (http://localhost:8765)
apps/cli/            chat command-line app
packages/agent_core/ agent loop, models, tools, memory, approvals, scheduler
packages/skills/     task playbooks (SKILL.md files)
packages/connectors/ service connectors (Gmail, Calendar, …)
packages/browser/    browser automation notes
docs/                architecture and feature checklist
data/                user data at runtime — gitignored
tests/               tests (8, all passing)
```

Nothing here posts, sends, or buys without an approval step.
