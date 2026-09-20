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
make install
```

`make help` lists all targets. Scripts load `.env` and the project virtualenv automatically.

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
make db
make migrate
```

### 4. Seed demo data

```bash
make seed
```

To wipe previous demo rows and reseed:

```bash
make seed-reset
```

Demo patients use medical record numbers prefixed with `DEMO-`. The script only creates or deletes those rows, so hand-entered data is left alone. Other patients use fictional `555` numbers.

### 5. Start the app

```bash
make up
```

This starts Postgres (if needed), backend, frontend, and the Cloudflare tunnel, then waits for the backend health check. Logs and PID files go in `.runtime/`.

To run a single service in the foreground instead:

```bash
make backend
make frontend
make tunnel
```

### 6. Register the Retell webhook

`make up` prints the tunnel URL. Point Retell at:

`https://<your-tunnel>.trycloudflare.com/webhooks/retell`

Or apply it with:

```bash
make webhook TUNNEL_URL=https://<your-tunnel>.trycloudflare.com
```

Set `AUTO_UPDATE_RETELL_WEBHOOK=1` in `.env` if you want `make up` to do this automatically.

### Verify

- Backend health: http://127.0.0.1:8000/ (`make health`)
- API docs: http://127.0.0.1:8000/docs
- Frontend: http://localhost:5173/

### Tests

```bash
uv run pytest
```

### Stop services

```bash
make down
make db-stop
```

### Troubleshooting

- `uvicorn: not found` — run `make install`, or use `uv run uvicorn ...`
- Backend fails with `RETELL_API_KEY` missing — put the key in `.env` at the project root (`make up` loads it)
- Dev script says Postgres service not detected — compose service name is `db` in `docker-compose.yml`

## Demo recording

A short screen recording of a live call is the best walkthrough. See [docs/demo.md](docs/demo.md) for what to capture.

## Known limitations

- There is no authentication. Do not expose this app on a public network.
- Placing a real call requires Retell and OpenAI credentials plus a provisioned caller ID.
- All bundled data is synthetic. Never load real patient information.
- Emergency detection is a model classification for the operator UI, not a medical device.

More product context is in [docs/product.md](docs/product.md).
