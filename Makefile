.PHONY: start stop start-backend start-db start-frontend install pre-commit pre-commit-rm test test-e2e lint format fake-guest fake-plus-one preview

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

# Install pre-commit hooks
pre-commit:
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push

# Remove pre-commit hooks
pre-commit-rm:
	uv run pre-commit uninstall --hook-type pre-commit --hook-type pre-push

make frontend-run:
	pnpm --dir frontend run dev

# Run tests
test:
	pytest

# Run e2e tests with Playwright (builds frontend, starts preview, runs tests, stops preview)
E2E_PORT ?= 4400
test-e2e:
	@if lsof -i :$(E2E_PORT) -sTCP:LISTEN -t >/dev/null 2>&1; then \
		echo "Error: port $(E2E_PORT) is already in use"; exit 1; \
	fi
	pnpm --dir frontend run build
	pnpm --dir frontend exec astro preview --port $(E2E_PORT) & \
	E2E_PID=$$!; \
	npx --yes wait-on http://localhost:$(E2E_PORT) --timeout 15000 && \
	FRONTEND_URL=http://localhost:$(E2E_PORT) pnpm --dir packages/e2e test; \
	TEST_EXIT=$$?; \
	kill $$E2E_PID 2>/dev/null; \
	exit $$TEST_EXIT

# Run linter
lint:
	ruff check src/
	ty check src/

# Format code
format:
	ruff format src/

fake-guest:
	python cli.py create-guest

fake-plus-one:
	python cli.py create-plus-one

migrate-db:
	alembic upgrade head

clean-db:
	docker compose down
	docker container prune -f
	docker volume rm wedding_postgres_volume
	docker compose up -d
	alembic upgrade head

# Build frontend and start preview server
preview:
	pnpm --dir frontend run build
	pnpm --dir frontend exec astro preview

down:
	docker compose down

build:
	docker compose build
