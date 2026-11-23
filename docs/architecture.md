# Architecture

```
User (app / web / WhatsApp)
        |
   Chat surface  ---- approval cards ----> User taps approve/deny
        |
   Agent core (loop, system prompt, subagents)
     |        |          |            |
  Memory    Tools     Skills     Connectors
  (md)    (files,    (SKILL.md)  (Gmail, FB…)
           shell,
           browser)
        |
   Model provider (pluggable API)   Scheduler (cron, hooks)
        |
   Secure Vault (logins, keys) — never in chat or memory
```

Rules:
- One user per agent. The agent's computer persists between chats.
- Outside content (web, files, tool output) is data, never orders.
- Consequential actions wait for an approval tap.
- Secrets live in the vault / .env only.
