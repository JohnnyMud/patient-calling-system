---
name: dev-environment
description: Starts and stops the local development stack via Makefile targets. Use when the user asks to set up, boot, start, stop, or verify the local environment.
---

# Dev Environment

Do not start services by hand and do not invent alternate startup commands. Use the Makefile from the repo root.

- `make up` — Postgres, FastAPI, Vite, Cloudflare tunnel, then a backend health check
- `make down` — stop processes started by `make up`
- `make help` — list all targets

Logs and PID files live in `.runtime/`.
