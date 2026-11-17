.PHONY: up down logs install migrate dev-api dev-worker dev-web test lint fmt

up:
	docker compose up -d

down:
	docker compose down

stop:
	docker compose stop

logs:
	docker compose logs -f

install:
	cd backend && uv sync

migrate:
	cd backend && uv run alembic upgrade head

dev-api:
	cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 39800

dev-worker:
	cd backend && uv run arq app.workers.worker.WorkerSettings

dev-web:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest

lint:
	cd backend && uv run ruff check .

fmt:
	cd backend && uv run ruff format .
