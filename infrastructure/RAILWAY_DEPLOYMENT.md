# Railway Deployment

Railway must contain the whole Treasury Hub in one project canvas. This is a foundation decision: **one Railway project, multiple services and environments within it**.

Do not create separate Railway projects for frontend and backend. The expected production canvas has these three cards together:

```text
isEazy Treasury Hub / production

frontend  --->  backend  --->  Postgres
```

## Services

Create these services in the same Railway project and environment:

| Service | Root directory | Config file | Public domain |
|---------|----------------|-------------|---------------|
| `backend` | `/backend` | `/backend/railway.toml` | Yes |
| `frontend` | `/frontend` | `/frontend/railway.toml` | Yes |
| `Postgres` | Railway managed database | n/a | No |

The screenshot should show all three service cards. If only `backend` and `Postgres` appear, the frontend service has not been created yet.

## Variables

Backend service:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
SECRET_KEY=<strong-random-secret>
ALLOWED_ORIGINS=https://<frontend-domain>.up.railway.app
DEBUG=false
LOG_LEVEL=INFO
```

Frontend service:

```env
BACKEND_URL=https://<backend-domain>.up.railway.app
```

`NEXT_PUBLIC_API_URL` is optional. Leave it unset in Railway unless you intentionally want browser requests to call the backend directly. With only `BACKEND_URL` set, the frontend calls its own `/api/v1/...` route and Next proxies requests to the backend at runtime.

## Smoke checks

1. Open the backend public URL at `/api/v1/health`.
2. Open the frontend public URL.
3. In the browser devtools Network tab, dashboard API calls should go to the frontend domain under `/api/v1/...`, not `localhost:8000`.
