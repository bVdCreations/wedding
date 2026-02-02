.PHONY: start stop start-backend start-db start-frontend install test lint format

# Start all services with Docker Compose
start:
	docker compose up

# Start all services in detached mode
start-detached:
	docker compose up -d

# Stop all services
stop:
	docker compose down

# Start only the backend API (requires running database)
start-backend:
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Start database only
start-db:
	docker compose up db -d

# Install dependencies
install:
	uv sync

# Run tests
test:
	pytest

# Run linter
lint:
	ruff check src/
	ty check src/

# Format code
format:
	ruff format src/

fake-guest:
	python cli.py create_guest

migrate-db:
	alembic upgrade head

clean-db:
	docker compose down
	docker container prune -f
	docker volume rm wedding_postgres_volume
	docker compose up -d
	alembic upgrade head

down:
	docker compose down

build:
	docker compose build
