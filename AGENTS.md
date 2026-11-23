# AGENTS.md — working in this repo

- This repo is a from-scratch Muse-like personal agent. No Meta code.
- Core stays stdlib-only until a phase says otherwise.
- Secrets only in .env / vault. Never in code, memory, or logs.
- Consequential actions (send, post, buy, delete) need approval.
- Run tests before every commit: `python3 -m unittest discover tests`
- Keep user-facing words plain and simple.
