# Spec 00 — System Architecture

**Version:** 1.0  
**Status:** Draft — Pending User Review  
**Date:** 2026-05-11  
**Author:** Architectural Foundation Session

---

## 1. System Overview

isEazy Treasury Hub is an internal Treasury Intelligence Platform for a Spanish SME e-learning group. It provides centralized treasury visibility, direct cash flow generation, rolling forecasting, and treasury governance across multiple operational companies and a holding entity.

The system is **not** an ERP, accounting system, banking integration, or reconciliation engine. It is a treasury operations intelligence layer that sits alongside existing finance tooling.

---

## 2. Architectural Style

**Modular Monolith** (Phase 1) with explicit bounded context boundaries that allow future microservice extraction without breaking changes.

Rationale:
- Phase 1 scope and team size do not justify distributed system complexity
- Clear bounded context design enables future decomposition if needed
- Simpler deployment on Railway
- Easier debugging for a finance-critical system

---

## 3. High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                        │
│  Dashboard │ Import UI │ Ledger │ Forecast │ Debt Calendar  │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API (JSON)
┌─────────────────────────▼───────────────────────────────────┐
│                    BACKEND (FastAPI)                          │
│                                                              │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐  │
│  │ Import Engine│  │ Classification│  │  Intercompany    │  │
│  │              │  │     Engine    │  │  Matching Engine │  │
│  └──────┬───────┘  └───────┬───────┘  └────────┬─────────┘  │
│         │                  │                   │             │
│  ┌──────▼───────────────────▼───────────────────▼─────────┐  │
│  │                   Treasury Ledger                       │  │
│  │              (Canonical Treasury Truth)                 │  │
│  └──────────────────────────┬──────────────────────────────┘  │
│                             │                               │
│  ┌──────────────┐  ┌────────▼──────┐  ┌──────────────────┐  │
│  │   Forecast   │  │   Analytics   │  │  Debt Calendar   │  │
│  │    Engine    │  │    Engine     │  │     Engine       │  │
│  └──────────────┘  └───────────────┘  └──────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Excel Integration Layer                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │ SQLAlchemy ORM
┌─────────────────────────▼───────────────────────────────────┐
│                    PostgreSQL Database                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Bounded Contexts

See `/docs/specs/02_bounded_contexts.md` for full definitions.

| Context | Responsibility | Primary Table(s) |
|---------|---------------|-----------------|
| Bank Import Engine | Ingest, normalize, deduplicate bank files | import_batches, raw_movements |
| Treasury Ledger | Canonical normalized movements | movements |
| Classification Engine | Category assignment, rules, overrides | classification_rules, movement_classifications |
| Intercompany Matching | Internal transfer detection, elimination | intercompany_matches |
| Forecast Engine | 3-layer forecast management | forecast_entries, forecast_scenarios |
| Debt Calendar | Debt instruments, schedules, maturities | debt_instruments, debt_schedules |
| Treasury Analytics | KPIs, variance, liquidity | (computed, no primary tables) |
| Excel Integration | Import/export, templates, roundtrip | (service layer, no dedicated tables) |
| Dashboard & Viz | UI aggregation, filtering | (read layer, no dedicated tables) |

---

## 5. Data Flow: Actuals

```
Bank File (Excel/CSV)
       │
       ▼
[Import Engine]
  - Format detection
  - Parsing
  - Normalization
  - Duplicate check (hash)
  - ImportBatch creation
       │
       ▼
[Treasury Ledger]
  - raw_movements stored
  - Movements created
       │
       ├──► [Classification Engine]
       │      - Rule matching
       │      - Category assignment
       │      - Confidence scoring
       │
       └──► [Intercompany Matching]
              - Internal account detection
              - Match pairing
              - Elimination flags
```

---

## 6. Data Flow: Forecast

```
Excel Template (Official Forecast)
       │
       ▼
[Excel Integration Layer]
  - Template validation
  - Parsing
       │
       ▼
[Forecast Engine]
  - ForecastEntry creation
  - Scenario: OFFICIAL
  - Period: 13 weeks rolling
       │
       ▼
[Treasury Analytics]
  - Variance: Forecast vs Actuals
  - Dashboard: 3-layer comparison
```

---

## 7. API Design Philosophy

- **REST** with resource-oriented URLs
- **JSON** for all payloads
- **Pydantic v2** for request/response validation
- **Versioned** from day 1: `/api/v1/`
- **Pagination** on all list endpoints (cursor-based preferred, offset acceptable for Phase 1)
- **Filtering** via query parameters
- **Consistent error schema** across all endpoints

Error schema:
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Human-readable description",
  "details": {}
}
```

---

## 8. Authentication (Phase 1)

Phase 1 uses simple API key authentication or session-based auth with a single admin user. No RBAC.

Architecture MUST remain compatible with:
- JWT-based authentication
- Role-based access control
- Multi-user environments
- Audit trail attribution

This means: user context must flow through all write operations even if the user model is minimal in Phase 1.

---

## 9. Audit & Traceability Requirements

Every write operation MUST record:
- `created_at` (UTC timestamp)
- `created_by` (user or system identifier)
- `updated_at`
- `updated_by`
- Import operations: link to `import_batch_id`
- Manual overrides: explicit audit record

Soft deletes preferred over hard deletes for treasury data.

---

## 10. Multi-Company Architecture

All entities that are company-scoped MUST include a `company_id` foreign key.

The system supports:
- **Individual company view** — filter by `company_id`
- **Consolidated group view** — aggregate all companies
- **Intercompany elimination** — net out internal transfers for consolidated view

Companies are seeded from a master company registry. Phase 1 scope: isEazy group entities only.

---

## 11. Configuration Management

Environment-based configuration with no secrets in code:
- `.env.example` committed
- `.env.local` git-ignored
- Railway environment variable injection for production

See `/docs/specs/16_devops_and_deployment.md` for full config strategy.

---

## 12. Error Handling Philosophy

- **Fail loudly on import errors** — never silently swallow import failures
- **Fail gracefully on classification** — unclassified is a valid state
- **Never lose data** — failed imports log the error but preserve the raw file reference
- **Idempotent imports** — re-importing the same file produces the same result

---

## 13. Performance Targets (Phase 1)

| Operation | Target |
|-----------|--------|
| Dashboard load | < 2s |
| Import processing (1000 rows) | < 10s |
| Ledger query with filters | < 500ms |
| Export generation | < 5s |
| Forecast computation | < 1s |

---

## 14. Open Architecture Questions

| # | Question | Impact | Owner |
|---|----------|--------|-------|
| 1 | AI forecast: external API (Claude/OpenAI) vs local model? | High | User |
| 2 | File storage: local filesystem vs object storage (S3)? | Medium | User |
| 3 | Background jobs: sync in-process vs Celery/worker? | Medium | Technical |
| 4 | WebSocket for real-time import progress? | Low | UX |
