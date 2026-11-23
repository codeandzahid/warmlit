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

## Use a real AI brain

Copy `.env.example` to `.env`, then pick one:

- **API key** (OpenAI, OpenRouter, Meta Model API, any
  OpenAI-compatible endpoint): set `MODEL_PROVIDER=openai`,
  `MODEL_API_KEY=...`, `MODEL_NAME=...`
- **Free local model** (your own PC): install Ollama from
  ollama.com, run `ollama pull llama3.2`, set `MODEL_PROVIDER=ollama`

Never put keys in chat. `.env` is gitignored.

## Free vs Paid

- **Free:** chat with daily limit, memory, read files, web fetch.
- **Paid:** unlimited + local system tasks — write files, run shell,
  open Chrome, scheduled jobs. All still need approval taps.

Owner makes a Paid key with `python3 tools/make_key.py --days 30`
(after the buyer pays outside Warmlit — no card data in this code).
Buyer puts `license.json` in `data/`. Price is NOT set yet — see
`docs/plans.md`. Check your plan in chat with `/plan`.

## What works today

- Web chat UI + CLI chat, with approval cards (Approve / Deny)
- Memory: save + search notes (markdown files)
- Tools: read/write/list files, run shell (approval), fetch web
  pages, open pages in local Chrome, search skills
- Scheduler: jobs that actually run (`every:60s`, `daily@09:15`)
- Model providers: echo demo, OpenAI-compatible API, Ollama local
- 8 tests, all passing

## Not connected yet (needs your accounts/keys)

- Gmail, Calendar, Facebook, TikTok, YouTube connectors — docs in
  `packages/connectors/`, code hooks ready, no login without you
- Mobile app, voice, image/video generation — later phases
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
