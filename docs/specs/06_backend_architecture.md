# Spec 06 — Backend Architecture

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Technology Stack

| Concern | Technology | Version |
|---------|-----------|---------|
| Framework | FastAPI | 0.115+ |
| Language | Python | 3.12 |
| ORM | SQLAlchemy | 2.0 (typed, async-capable) |
| Validation | Pydantic | v2 |
| Migrations | Alembic | Latest |
| Database | PostgreSQL | 16 |
| Excel parsing | openpyxl | Latest |
| CSV parsing | stdlib csv + pandas (optional) | |
| Testing | pytest + pytest-asyncio | |
| HTTP client | httpx (for testing) | |

---

## 2. Application Structure

```
/backend
├── app/
│   ├── main.py                 — FastAPI app factory, router mounting
│   ├── config.py               — Settings via pydantic-settings
│   ├── database.py             — SQLAlchemy engine and session factory
│   │
│   ├── models/                 — SQLAlchemy ORM models (one per bounded context)
│   │   ├── company.py
│   │   ├── bank_account.py
│   │   ├── import_batch.py
│   │   ├── movement.py
│   │   ├── classification.py
│   │   ├── intercompany.py
│   │   ├── forecast.py
│   │   └── debt.py
│   │
│   ├── schemas/                — Pydantic v2 request/response schemas
│   │   ├── company.py
│   │   ├── bank_account.py
│   │   ├── import_batch.py
│   │   ├── movement.py
│   │   ├── classification.py
│   │   ├── intercompany.py
│   │   ├── forecast.py
│   │   ├── debt.py
│   │   └── common.py           — PaginatedResponse, ErrorResponse, etc.
│   │
│   ├── routers/                — FastAPI routers (one per domain)
│   │   ├── companies.py
│   │   ├── bank_accounts.py
│   │   ├── imports.py
│   │   ├── movements.py
│   │   ├── classifications.py
│   │   ├── intercompany.py
│   │   ├── forecast.py
│   │   ├── debt.py
│   │   └── analytics.py
│   │
│   ├── services/               — Business logic (one per bounded context)
│   │   ├── import_engine/
│   │   │   ├── __init__.py
│   │   │   ├── detector.py     — format detection
│   │   │   ├── parsers/        — one parser per bank format
│   │   │   │   ├── base.py
│   │   │   │   ├── santander.py
│   │   │   │   ├── bbva.py
│   │   │   │   └── generic_csv.py
│   │   │   ├── normalizer.py
│   │   │   └── deduplicator.py
│   │   ├── classification/
│   │   │   ├── __init__.py
│   │   │   ├── rules_engine.py
│   │   │   └── taxonomy.py
│   │   ├── intercompany/
│   │   │   ├── __init__.py
│   │   │   └── matcher.py
│   │   ├── forecast/
│   │   │   ├── __init__.py
│   │   │   └── engine.py
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── cash_flow.py
│   │   │   ├── variance.py
│   │   │   └── liquidity.py
│   │   └── excel/
│   │       ├── __init__.py
│   │       ├── importer.py
│   │       └── exporter.py
│   │
│   └── dependencies/           — FastAPI dependency injection
│       ├── database.py         — get_db session dependency
│       └── auth.py             — auth dependency (minimal in Phase 1)
│
├── migrations/                 — Alembic migration files
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── tests/
│   ├── conftest.py             — test database, fixtures
│   ├── test_import_engine/
│   ├── test_classification/
│   ├── test_intercompany/
│   └── test_api/
│
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

---

## 3. FastAPI App Configuration

```python
# app/main.py
app = FastAPI(
    title="isEazy Treasury Hub API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# All routers mounted under /api/v1/
app.include_router(movements.router, prefix="/api/v1/movements")
app.include_router(imports.router, prefix="/api/v1/imports")
# ...etc
```

CORS configured for frontend origin only.

---

## 4. Database Session Management

```python
# app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.DATABASE_URL, echo=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
```

All DB operations async. Session injected via FastAPI dependency.

---

## 5. API Endpoint Conventions

### URL Structure

```
GET    /api/v1/movements                    — list with filters
GET    /api/v1/movements/{id}               — single resource
POST   /api/v1/movements/{id}/classify      — action on resource
POST   /api/v1/imports                      — create (file upload)
GET    /api/v1/imports/{id}/status          — import status polling
DELETE /api/v1/imports/{id}                 — cancel (if PENDING)
```

### Pagination (all list endpoints)

```json
{
  "items": [...],
  "total": 1523,
  "page": 1,
  "page_size": 50,
  "pages": 31
}
```

### Filtering (query params)

```
GET /api/v1/movements?
  company_id=uuid&
  bank_account_id=uuid&
  date_from=2026-01-01&
  date_to=2026-03-31&
  category=OCF_REVENUE&
  amount_min=-1000&
  amount_max=0&
  search=PROVEEDOR&
  page=1&
  page_size=50&
  sort=value_date&
  order=desc
```

### Error Response Schema

```python
class ErrorResponse(BaseModel):
    error: str           # Machine-readable error code
    message: str         # Human-readable description
    details: dict = {}   # Optional field-level errors
```

---

## 6. Service Layer Pattern

Routers delegate all business logic to service classes. Routers handle:
- Input validation (Pydantic)
- Auth check
- Calling service
- Returning response schema

Services handle:
- Business logic
- DB queries (via SQLAlchemy)
- Cross-service calls

```python
# routers/movements.py
@router.get("/", response_model=PaginatedResponse[MovementResponse])
async def list_movements(
    params: MovementQueryParams = Depends(),
    db: AsyncSession = Depends(get_db),
):
    return await movement_service.list_movements(db, params)
```

---

## 7. Settings Management

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 8. File Upload Handling

Import files received as `multipart/form-data`. Files processed in-memory for Phase 1 (no disk storage of raw files required beyond error logging). File hash computed before processing.

If file storage becomes needed: abstract behind a `FileStore` interface, implement with local filesystem first, later swap for S3.

---

## 9. Background Processing

Phase 1: import processing is synchronous in the request. If a file has >5000 rows, consider background processing.

Architecture note: import pipeline designed as a pipeline of stateless functions so it can be moved to a background worker without refactoring:

```
receive_file → detect_format → parse → normalize → deduplicate → persist
```

---

## 10. Logging

Structured JSON logging via Python `logging` + `structlog`:
- Every request: method, path, duration, status code
- Every import: batch_id, file, row counts, errors
- Every classification: movement_id, rule_id, result
- Errors: full exception with context

---

## 11. Testing Strategy

See `/docs/specs/17_testing_strategy.md` for full detail.

Backend testing priorities:
1. Parser unit tests (each bank format)
2. Rules engine unit tests
3. Intercompany matcher unit tests
4. API integration tests (test database)
5. Import pipeline end-to-end tests

```bash
# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```
