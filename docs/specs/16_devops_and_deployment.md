# Spec 16 — DevOps and Deployment

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Deployment Platform

**Railway** — managed cloud platform for all environments.

Rationale:
- Zero-ops managed infrastructure
- Managed PostgreSQL included
- Automatic deploys from Git
- Environment variable management built-in
- Affordable for Phase 1 (SME budget)

---

## 2. Environment Strategy

| Environment | Purpose | Database | Deploy Trigger |
|-------------|---------|----------|---------------|
| Development | Local developer machines | Local PostgreSQL | Manual |
| Staging | Integration testing, UAT | Railway PostgreSQL (staging) | PR merge to `main` |
| Production | Live system | Railway PostgreSQL (prod) | Manual deploy from `main` |

Phase 1: staging + production only (no dedicated CI runners). Development is local.

---

## 3. Monorepo Deployment Architecture

Railway supports deploying multiple services from a monorepo:

- **Service: backend** — FastAPI on Railway, `Dockerfile` in `/backend`
- **Service: frontend** — Next.js on Railway, `Dockerfile` in `/frontend`
- **Service: postgres** — Railway managed PostgreSQL

All three services must live in the same Railway project/environment canvas. Each service has its own Railway environment variables, but the deployed system is operated as one project.

---

## 4. Dockerfile Strategy

### Backend Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

CMD ["node", "server.js"]
```

---

## 5. Environment Variables

### Backend Required

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
SECRET_KEY=<random 256-bit key>
ALLOWED_ORIGINS=https://treasury.iseazy.com,http://localhost:3000
DEBUG=false
LOG_LEVEL=INFO
```

### Frontend Required

```
BACKEND_URL=https://<backend-domain>.up.railway.app
```

`NEXT_PUBLIC_API_URL` is optional and should normally be left unset on Railway. The frontend proxies same-origin `/api/v1/...` requests to `BACKEND_URL`, which avoids browser bundles being tied to a build-time backend URL.

### Template Files

- `/backend/.env.example` — committed, no secrets
- `/frontend/.env.example` — committed, no secrets
- `.gitignore` — all `.env` files (except `.env.example`) ignored

---

## 6. Database Migration Strategy

Alembic manages all schema changes.

```bash
# Generate migration
alembic revision --autogenerate -m "add movement deduplication index"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

**Production migration protocol:**
1. Test migration on staging first
2. Backup production database before running
3. Apply migration during low-traffic window
4. Verify with smoke test after migration

Migrations are run as part of the backend startup (Alembic `upgrade head` in entrypoint).

---

## 7. Secrets Management

Phase 1: Railway environment variable store (Railway Secrets).
- No secrets in code or Git
- `SECRET_KEY` rotated if compromised (requires session invalidation)
- Database credentials managed by Railway (auto-rotation not used in Phase 1)

---

## 8. Logging

**Backend:** structured JSON logs (structlog)
- Log level: INFO in production, DEBUG in development
- Fields: timestamp, level, service, request_id, duration, status_code
- Railway automatically captures stdout/stderr logs

**Frontend:** Next.js default logging + custom error boundary
- Client errors sent to console (no external error tracking in Phase 1)
- Server errors logged via Next.js

Phase 2: consider Sentry or similar for error tracking.

---

## 9. Health Checks

```
GET /api/v1/health
Response: { "status": "ok", "db": "ok", "version": "1.0.0" }
```

Railway uses this for deployment health checks.

---

## 10. Domain and SSL

- Domain: `treasury.iseazy.com` (TBD — requires DNS configuration)
- API: `api.treasury.iseazy.com`
- SSL: Railway auto-provisions Let's Encrypt certificates

---

## 11. Backup Strategy

Railway managed PostgreSQL includes:
- Daily automated backups (7-day retention)
- Point-in-time recovery (if Railway plan supports it)

For Phase 1: Railway built-in backups are sufficient.
For Phase 2: consider pg_dump-based additional backups.

---

## 12. Performance Monitoring

Phase 1: none (Railway basic metrics only).
Phase 2: consider:
- Prometheus + Grafana via Railway plugin
- Or Datadog lightweight integration

---

## 13. Deployment Runbook

### First Deployment

1. Create one Railway project/environment with three services visible together: frontend, backend, postgres
2. Set backend root directory `/backend` and config file `/backend/railway.toml`
3. Set frontend root directory `/frontend` and config file `/frontend/railway.toml`
4. Set environment variables for each service
5. Deploy backend first (runs Alembic migrations)
6. Seed initial data (companies, bank accounts, category taxonomy) via `/scripts/seed.py`
7. Deploy frontend
8. Verify health endpoint
9. Run smoke test checklist

### Routine Deployment (code changes)

1. Merge PR to `main`
2. Railway auto-deploys staging
3. QA smoke test on staging
4. Manual promote to production via Railway dashboard

### Rollback

1. Railway one-click rollback to previous deployment
2. If DB migration was involved: run `alembic downgrade -1` first
