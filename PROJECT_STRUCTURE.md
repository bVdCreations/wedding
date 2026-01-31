# Project Structure

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: Astro.js
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy with async support
- **Authentication**: JWT-based authentication
- **Migrations**: Alembic
- **Testing**: pytest, Playwright (E2E)
- **Package Management**: pnpm workspaces
- **Containerization**: Docker & Docker Compose

## Directory Structure

```
weblibros/
├── .dockerignore          # Docker ignore rules
├── .editorconfig          # Editor configuration
├── .envrc                 # direnv environment variables
├── .git-blame-ignore-revs # Git blame ignore file
├── .gitignore             # Git ignore rules
├── .gitlab-ci.yml         # GitLab CI/CD configuration
├── .prettierignore        # Prettier ignore rules
├── .prettierrc            # Prettier configuration
├── .python-version        # Python version specification
├── alembic.ini            # Alembic configuration
├── Dockerfile             # Docker image definition
├── eslint.config.mjs      # ESLint configuration
├── LICENSE                # License file
├── Makefile               # Makefile for common tasks
├── package.json           # Root package.json
├── pnpm-lock.yaml         # pnpm lock file
├── pnpm-workspace.yaml    # pnpm workspace configuration
├── pyproject.toml         # Python project configuration
├── pyrightconfig.json     # Pyright configuration
├── README.md              # Existing README
├── renovate.json          # Renovate configuration
├── commands/              # Shell scripts for Docker commands
│   ├── entrypoint.sh      # Container entrypoint
│   ├── openapi.sh         # OpenAPI generation script
│   ├── start_command.sh   # Start script
│   ├── start-e2e-ci.sh    # E2E CI start script
│   ├── test-ci.sh         # CI test script
│   └── test.sh            # Test script
│
├── docker-compose/        # Docker Compose configurations
│
├── migrations/            # Database migrations (Alembic)

├── packages/              # npm workspace packages
│   ├── e2e/               # End-to-end tests (Playwright)
│   │
│   └── site/              # frontend site Astro.js
│
└── src/                   # Python backend source code
    ├── __init__.py
    ├── conftest.py        # pytest configuration
    ├── events.py          # Event definitions
    ├── main.py            # FastAPI application entry point
    │
    ├── accounts/          # User accounts module
    │
    ├── config/            # Configuration module
    │   ├── __init__.py
    │   ├── database.py
    │   ├── logging.py
    │   ├── settings.py
    │   ├── table_names.py
    │
    ├── healthz/           # Health check endpoints
    │   ├── __init__.py
    │   ├── router.py
    │   ├── schema.py
    │   └── tests/
    │       └── test_endpoint.py
```

## Architecture

### Domain-Driven Design (DDD)

The project follows Domain-Driven Design principles with clear separation of concerns:

- **Domain Layer**: Contains business logic, entities, aggregates, and domain events
- **Application Layer**: Features and use cases
- **Infrastructure Layer**: Repositories, external services, Read models, Write models
- **Presentation Layer**: API endpoints

### Running Tests

- Python tests: `pytest` or `make test`
- E2E tests: `pnpm --filter e2e test`

### Database Migrations

- Create migration: `alembic revision -m "description"`
- Apply migrations: `alembic upgrade head`
