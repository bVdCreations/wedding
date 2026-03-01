# Astro Builder Agent Plan

## Overview

Build an agent that can create and update Astro.js apps for users based on natural language prompts.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Caddy (Port 80/443)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  /api/*         →  FastAPI (localhost:8000)              │  │
│  │  /preview/{id}/* →  Astro dev server (dynamic port)      │  │
│  │                   + JWT validation                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI (localhost:8000)                    │
│  ├── /api/agent/*      - LLM prompt processing                 │
│  ├── /api/project/*   - Astro project management               │
│  ├── /api/git/*       - GitHub private repos                   │
│  ├── /api/cloudflare* - Deploy to Cloudflare Pages             │
│  ├── /api/caddy/*     - Manage Caddy proxy routes              │
│  └── Dashboard (HTML) - User interface                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Astro Dev Servers (per user)                  │
│  ├── user_1: localhost:3001                                    │
│  ├── user_2: localhost:3002                                    │
│  └── user_n: localhost:3000+n                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Agent Service (app/agent/)

- **llm.py** - OpenRouter client (minimax model)
- **prompt.py** - Parse prompts → Generate Astro code

### 2. Project Manager (app/projects/)

- **manager.py** - Create/manage Astro projects
- **file_ops.py** - Read/write project files
- **dev_server.py** - Start/stop astro dev server

### 3. Caddy Proxy Manager (app/proxy/)

- **caddy.py** - Open/close routes via Caddy Admin API
- JWT validation on routes

### 4. Git Manager (app/git/)

- **client.py** - Create private repos, commit/push

### 5. Cloudflare Manager (app/cloudflare/)

- **deploy.py** - Deploy static files to Cloudflare Pages

### 6. API Routes (app/api/)

- All FastAPI endpoints
- Dashboard HTML template

## Environment Variables

```
OPENROUTER_API_KEY=...
GITHUB_TOKEN=...
CLOUDFLARE_API_TOKEN=...
CLOUDFLARE_ACCOUNT_ID=...
JWT_SECRET=...
CADDY_ADMIN_URL=http://localhost:2019
```

## User Flow

1. User visits dashboard (JWT in header)
2. Caddy validates JWT → proxies to FastAPI
3. FastAPI creates/fetches Astro project
4. FastAPI opens Caddy route → /preview/{user_id}/\* → localhost:{port}
5. Dashboard loads iframe with preview
6. User prompts "add a contact form"
7. LLM generates code → writes to project files
8. Astro dev auto-reloads → user sees changes
9. User clicks "Save" → commits to private GitHub repo
10. User clicks "Deploy" → builds + Cloudflare Pages

## Key Features

- Static Astro sites only (no server rendering)
- Per-user private GitHub repo
- Local dev server preview via Caddy proxy
- Cloudflare Pages for production deployment
- JWT authentication via Caddy

## Setup Requirements

1. OpenRouter API key
2. GitHub PAT with repo scope
3. Cloudflare API token + Account ID
4. Caddy server running
