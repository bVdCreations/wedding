# Wedding E2E Tests

End-to-end tests for the wedding RSVP application using Playwright.

## Prerequisites

1. Install Node.js (v18 or later)
2. Install pnpm: `npm install -g pnpm`
3. Install Playwright browsers: `pnpm test:install`

## Installation

```bash
# Install dependencies from the workspace root
pnpm install
```

## Running Tests

### Prerequisites

Ensure the following services are running:
- Backend API on http://localhost:8000
- Frontend on http://localhost:4321
- PostgreSQL database on port 25432

You can start them with:
```bash
docker-compose up -d api frontend db
```

### Run tests

```bash
# Run tests in headless mode
pnpm test

# Run tests with UI mode
pnpm test:ui

# Run tests with visible browser
pnpm test:headed

# Generate and view HTML report
pnpm test:report
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_URL` | http://localhost:4321 | Frontend base URL |
| `API_URL` | http://localhost:8000 | Backend API base URL |

## Test Structure

```
src/
  fixtures.ts      - Custom Playwright fixtures
  api-client.ts    - API client for backend calls
  test-data.ts    - Test data factories

tests/
  rsvp.spec.ts    - RSVP page e2e tests
```

## Writing Tests

Import the custom test and expect from the fixtures:

```typescript
import { test, expect } from '../src/fixtures';

test('my test', async ({ page, apiRequest, frontendURL }) => {
  // Use page for browser interactions
  // Use apiRequest for direct API calls
  // Use frontendURL for the base URL
});
```

## CI/CD

In CI environments, set `CI=true` to enable retries and other CI-specific settings.
