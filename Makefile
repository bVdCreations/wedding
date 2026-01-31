.PHONY: start stop start-backend start-db start-frontend install test lint format

# Start all services with Docker Compose
start:
	docker compose up --build

# Start all services in detached mode
start-detached:
	docker compose up --build -d

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
	uv sync --extra dev

# Run tests
test:
	pytest

# Run linter
lint:
	ruff check src/
	mypy src/

# Format code
format:
	ruff format src/
