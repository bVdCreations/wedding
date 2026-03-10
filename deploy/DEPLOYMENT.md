# Production Deployment

## Prerequisites

- Docker & Docker Compose installed
- Access to GHCR (GitHub Container Registry) - you must be logged in:
  ```bash
  echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin
  ```

## Setup

### 1. Copy environment template

```bash
cp deploy/.env.prod.example .env.prod
```

### 2. Edit `.env.prod` with your production values

Key variables to configure:

- `POSTGRES_PASSWORD` - generate a secure password
- `SECRET_KEY` - generate a secure random key
- `DATABASE_URL` - update password if you changed it
- `FRONTEND_URL` - your production domain
- `SMTP_*` - your email provider settings
- `WEBHOOK_SECRET` - generate a secure token for deployments
- `CLOUDFLARE_API_TOKEN` - for DNS-01 challenge with Caddy

#### Generate Secure Secrets

Generate secure random values using:

```bash
openssl rand -base64 32
```

Use this for:
- `SECRET_KEY`
- `WEBHOOK_SECRET`
- `POSTGRES_PASSWORD`

Never commit these values to version control.

#### Get Cloudflare API Token

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Go to **Profile** → **API Tokens**
3. Click **Create Token**
4. Use the **Edit zone DNS** template (or create custom):
   - **Permissions**: `Zone - DNS - Edit`
   - **Zone Resources**: Include all zones
5. Copy the generated token

The token needs permission to create/remove DNS TXT records for the ACME challenge.

### 3. Start services

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Images

The following images are used (pulled from GHCR):

| Service | Default Image | Custom Tag |
|---------|---------------|------------|
| API | `ghcr.io/bvdcreations/wedding-api:latest` | `c-<commit-hash>` |
| Webhook | `ghcr.io/bvdcreations/wedding-webhook:latest` | `c-<commit-hash>` |

To use a specific version, update the image tag in `.env.prod`:

```bash
API_IMAGE=ghcr.io/bvdcreations/wedding-api:c-abcd123
WEBHOOK_IMAGE=ghcr.io/bvdcreations/wedding-webhook:c-abcd123
```

## CI/CD

### Automatic Builds

- Push to `main` branch → builds & pushes API image
- Changes in `deploy/**` → builds & pushes webhook image

### Manual Deployment via Webhook

You can deploy new API versions without rebuilding by calling the webhook endpoint:

```bash
curl -X POST http://your-server:8080/webhook \
  -H "Authorization: Bearer YOUR_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"tag": "c-<commit-hash>"}'
```

This will:
1. Update `.env.prod` with the new image tag
2. Pull the new image
3. Restart the API container

## Services

| Service | Port | Description |
|---------|------|-------------|
| caddy | 80, 443 | Reverse proxy with HTTPS |
| api | 8000 | FastAPI application |
| db | 5432 | PostgreSQL database |
| webhook | 8080 | Deployment webhook endpoint |

## Troubleshooting

### View logs

```bash
docker compose -f docker-compose.prod.yml logs -f
```

### View logs for specific service

```bash
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f webhook
```

### Restart a service

```bash
docker compose -f docker-compose.prod.yml restart api
```

### Stop all services

```bash
docker compose -f docker-compose.prod.yml down
```