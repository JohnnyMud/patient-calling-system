.DEFAULT_GOAL := help

.PHONY: help install up down backend frontend tunnel db db-stop migrate seed seed-reset webhook health

help:
	@echo "Local development targets:"
	@echo "  make install      Install Python and frontend dependencies"
	@echo "  make up           Start Postgres, backend, frontend, and tunnel"
	@echo "  make down         Stop backend, frontend, and tunnel"
	@echo "  make db           Start Postgres (docker compose)"
	@echo "  make db-stop      Stop Postgres"
	@echo "  make migrate      Run Alembic migrations"
	@echo "  make seed         Seed demo data"
	@echo "  make seed-reset   Wipe demo rows and reseed"
	@echo "  make backend      Start FastAPI only (foreground)"
	@echo "  make frontend     Start Vite only (foreground)"
	@echo "  make tunnel       Start Cloudflare tunnel only (foreground)"
	@echo "  make webhook TUNNEL_URL=https://<id>.trycloudflare.com"
	@echo "  make health       Hit the backend health endpoint"

install:
	uv sync
	cd frontend && npm install

up:
	./scripts/dev_up.sh

down:
	./scripts/dev_down.sh

backend:
	./scripts/run_backend.sh

frontend:
	./scripts/run_frontend.sh

tunnel:
	./scripts/run_tunnel.sh

db:
	docker compose up -d db

db-stop:
	docker compose stop db

migrate:
	uv run alembic upgrade head

seed:
	uv run python scripts/seed_demo.py

seed-reset:
	uv run python scripts/seed_demo.py --reset

webhook:
	@if [ -z "$(TUNNEL_URL)" ]; then \
		echo "Usage: make webhook TUNNEL_URL=https://<id>.trycloudflare.com"; \
		exit 1; \
	fi
	uv run python scripts/update_retell_webhook.py --tunnel-url "$(TUNNEL_URL)" --apply

health:
	curl -fsS http://127.0.0.1:8000/
