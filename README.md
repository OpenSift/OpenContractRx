# OpenContractRx

Open-source contract intelligence + renewal + drafting platform built for hospitals.

## What it does (v1 goals)
- Upload contracts (PDF/DOCX later)
- Extract key terms (term dates, auto-renew, notice windows, pricing escalators, SLA, indemnification, data-processing/BAA flags)
- Show renewals dashboard (120/90/60/30 day buckets)
- Human-in-the-loop review for extracted terms
- AI-assisted drafting (renewal addendum + clause suggestions) with auditable rationale

## Monorepo layout
- `apps/api` – FastAPI backend
- `apps/worker` – background processing (OCR, extraction, embeddings)
- `apps/web` – Next.js frontend
- `packages/core` – shared Python schemas (Pydantic)

## Quickstart (dev)
1) Copy env file:
```bash
cp .env.example .env
```

2) Run the stack:
```bash
docker compose up --build
```

3) Open:

Web UI: http://localhost:3000
API docs: http://localhost:8000/docs
MinIO console: http://localhost:9001 (login from .env)

## Run API tests
Use the dedicated API test service:
```bash
docker compose --profile test run --rm api-test
```

## Initial endpoints

GET /healthz
POST /contracts/upload (placeholder - stores metadata file upload wiring comes next)
GET /contracts
GET /integrations

## AI integrations (ChatGPT, Codex, Claude, Claude Code)
- API key connection:
  - `POST /integrations/{provider}/api-key`
- OAuth flow:
  - `GET /integrations/{provider}/oauth/start`
  - `GET /integrations/{provider}/oauth/callback`
- Connection test:
  - `POST /integrations/{provider}/test`

Set OAuth env vars per provider when you want OAuth enabled:
- `*_OAUTH_CLIENT_ID`
- `*_OAUTH_CLIENT_SECRET`
- `*_OAUTH_AUTH_URL`
- `*_OAUTH_TOKEN_URL`
- `*_OAUTH_REDIRECT_URI`

## Security posture (baseline)
RBAC scaffolding (role claims)
Audit logging hooks
LLM calls are intended to go through an internal gateway (future service) for policy + logging

## License
Apache-2.0
