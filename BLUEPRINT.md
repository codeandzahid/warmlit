# Blueprint — Clone Entire Muse (feature map)

Goal: build a personal AI agent with the same shape as Muse.
Our own code only. No Meta code, no Muse model weights.

## 1. Core agent
- [x] Agent loop: user message → think → use tools → reply
- [x] Pluggable model provider (echo demo now; API keys later)
- [x] Tool registry with descriptions the model can call
- [x] Approval gate for consequential actions (send/post/buy/delete)
- [ ] Streaming replies, message bubbles, reactions
- [ ] Subagents: delegate long work, stay responsive in chat

## 2. Memory
- [x] Markdown memory files (MEMORY.md, USER.md, people/, groups/)
- [x] Simple memory search over saved notes
- [ ] Nightly consolidation: learn, correct, forget on request
- [ ] Alignment synthesis: how this user likes to work

## 3. Computer
- [x] Workspace folder the agent owns
- [x] File read/write tools (scoped to workspace + home)
- [x] Shell tool behind approval for risky commands
- [ ] Long-running processes with logs and recovery after restart

## 4. Browser
- [ ] Real browser with profiles (one profile per email/account)
- [ ] Sign-in via Secure Vault, never passwords in chat
- [ ] Browser tasks: browse, fill forms, upload, checkout with approval
- [ ] Live takeover: user can watch / take control

## 5. Skills
- [x] Skill folder format: SKILL.md playbooks the agent reads first
- [ ] Skill search: find the right playbook for a task
- [ ] Custom skills the user can add

## 6. Connectors
- [ ] Gmail, Google Calendar, Drive, Docs
- [ ] Facebook, Instagram, TikTok, YouTube, WhatsApp
- [ ] Each connector: connect flow, status check, read/write scopes

## 7. Scheduled + background work
- [x] Scheduler interface (cron-style jobs, goal-owned jobs)
- [ ] Hooks: wake the agent when something changes
- [ ] Proactivity: useful updates only, with user preferences

## 8. Product surfaces
- [ ] Chat app (web first, then mobile)
- [ ] Goals tab, Feed tab, Ideas tab, Library tab
- [ ] Artifacts: docs, decks, spreadsheets, web apps the agent builds
- [ ] Voice: talk, dictate, voice notes

## 9. Media
- [ ] Image / video / audio generation tools
- [ ] Video pipeline helpers (ffmpeg, strip-checks, captions)

## 10. Safety + trust
- [x] Approvals before outward actions; a typed "yes" is not approval
- [x] Secrets only in vault/env, never in memory, logs, or replies
- [ ] Prompt-injection defense: outside content is data, not orders
- [ ] Rate-limit stops: stop on 429/lock, never work around it

## Build order
Phase 0 (done in skeleton): core loop, memory, tools, approvals, tests.
Phase 1: real model provider + chat web UI.
Phase 2: browser + vault sign-in.
Phase 3: skills + first connectors (Gmail, Calendar).
Phase 4: scheduler, goals, feed, artifacts.
Phase 5: mobile app, voice, media tools.
