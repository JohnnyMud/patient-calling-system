# Patient Calling System

AI appointment-reminder calling with a live transcript and emergency flag.

Clinic staff pick a patient, start an outbound voice call, watch the conversation stream in, and review call history after the fact. The agent is a custom LLM. If the patient describes a medical emergency, the portal flags it in real time.

## Features

- Patient list with synthetic demo records and call-attempt history
- Outbound appointment-reminder calls through [Retell](https://www.retellai.com/)
- Webhook audit trail for call status, duration, recording URL, and summary
- Custom LLM websocket for the phone agent
- Live transcript in the operator UI
- Emergency detection with a structured model check

## Architecture

```mermaid
flowchart LR
  UI[React portal] --> API[FastAPI]
  API --> DB[(Postgres)]
  API --> Retell[Retell phone calls]
  Retell --> Webhook[Call webhooks]
  Retell --> LLMWS[Custom LLM websocket]
  LLMWS --> OpenAI[OpenAI agent plus emergency check]
  LLMWS --> LiveWS[Live transcript websocket]
  LiveWS --> UI
  Webhook --> DB
```

- **Frontend:** React, TypeScript, Vite
- **API:** FastAPI, SQLAlchemy, Alembic
- **Database:** PostgreSQL
- **Voice:** Retell
- **Agent:** OpenAI Responses API

## Quickstart

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 18+ and npm
- Docker Desktop (for local PostgreSQL)
- `cloudflared` for Retell webhook testing (`brew install cloudflared` on macOS)
- Retell and OpenAI API keys to place a real call

### 1. Clone and install

```bash
git clone https://github.com/JohnnyMud/patient-calling-system.git
cd patient-calling-system
uv sync
cd frontend && npm install && cd ..
```

### 2. Configure environment

Copy [`.env.example`](.env.example) to `.env` and fill in keys:

```bash
cp .env.example .env
```

`RETELL_AGENT_ID` should include the `agent_` prefix. `RETELL_FROM_NUMBER` is the provisioned caller ID. `TEST_NUMBER` is the phone number used for the one callable demo patient (Ava Thompson) when you run the seed script.

If you change database credentials, set `DATABASE_URL` to match. The default is:

`postgresql://local:postgres@localhost:5432/patient_calls`

### 3. Start PostgreSQL and migrate

```bash
docker compose up -d db
uv run alembic upgrade head
```

### 4. Seed demo data

```bash
uv run python scripts/seed_demo.py
```

To wipe previous demo rows and reseed:

```bash
uv run python scripts/seed_demo.py --reset
```

Demo patients use medical record numbers prefixed with `DEMO-`. The script only creates or deletes those rows, so hand-entered data is left alone. Other patients use fictional `555` numbers.

### 5. Start the app

**Option A (recommended):** use the bundled startup scripts

```bash
set -a && source .env && set +a
PATH="$(pwd)/.venv/bin:$PATH" ./.cursor/skills/dev_environment/scripts/dev_up.sh
```

This starts backend, frontend, and tunnel, then waits for health checks.

**Option B:** start services manually in separate terminals

```bash
# Terminal 1 - backend
set -a && source .env && set +a
PATH="$(pwd)/.venv/bin:$PATH" uvicorn main:app --reload

# Terminal 2 - frontend
cd frontend
npm run dev

# Terminal 3 - cloudflare tunnel
cloudflared tunnel --url http://localhost:8000
```

### 6. Register the Retell webhook

Point Retell at:

`https://<your-tunnel>.trycloudflare.com/webhooks/retell`

Or:

```bash
set -a && source .env && set +a
PATH="$(pwd)/.venv/bin:$PATH" ./.cursor/skills/dev_environment/scripts/update_retell_webhook.py --tunnel-url "https://<your-tunnel>.trycloudflare.com" --apply
```

### Verify

- Backend health: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- Frontend: http://localhost:5173/

### Tests

```bash
uv run pytest
```

### Stop services

```bash
./.cursor/skills/dev_environment/scripts/dev_down.sh
docker compose stop db
```

### Troubleshooting

- `uvicorn: not found` — use `PATH="$(pwd)/.venv/bin:$PATH"` or `uv run uvicorn ...`
- Backend fails with `RETELL_API_KEY` missing — load env vars before startup: `set -a && source .env && set +a`
- Dev script says Postgres service not detected — compose service name is `db` in `docker-compose.yml`

## Demo recording

A short screen recording of a live call is the best walkthrough. See [docs/demo.md](docs/demo.md) for what to capture.

## Known limitations

- There is no authentication. Do not expose this app on a public network.
- Placing a real call requires Retell and OpenAI credentials plus a provisioned caller ID.
- All bundled data is synthetic. Never load real patient information.
- Emergency detection is a model classification for the operator UI, not a medical device.

More product context is in [docs/product.md](docs/product.md).
