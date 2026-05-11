# ADR-001 — Tech Stack Selection

**Date:** 2026-05-11  
**Status:** ACCEPTED  
**Deciders:** isEazy Treasury Hub founding architecture session  
**Tags:** architecture, infra

---

## Context

We need to select a technology stack for a treasury intelligence platform used by an SME finance team. The platform is desktop-first, Excel-native, and will be deployed on Railway. The primary users are a CFO and finance operations staff. The team building it is expected to be small (1-2 developers + AI-assisted development sessions).

---

## Decision Drivers

- Rapid development with strong typing (financial data demands correctness)
- Railway deployment compatibility
- Excel import/export capability
- Good table and chart libraries for financial UX
- Long-term maintainability
- Strong AI-assisted development tooling support

---

## Options Considered

### Option A: Next.js + FastAPI + PostgreSQL (Selected)

**Pros:**
- Next.js: excellent TypeScript support, strong ecosystem, shadcn/ui components are finance-grade
- FastAPI: async, Python, openpyxl for Excel, strong Pydantic validation
- PostgreSQL: ACID, NUMERIC type for money, JSON support
- All three are Railway-supported natively
- Excellent AI-assisted development support (Claude knows these stacks deeply)

**Cons:**
- Two language context (TypeScript + Python)
- More complexity than a monolith Node or Python-only stack

---

### Option B: Next.js + Node.js backend (e.g., Hono/Express) + PostgreSQL

**Pros:**
- Single language (TypeScript) across frontend and backend
- Shared types natively

**Cons:**
- Node.js Excel libraries (xlsx, exceljs) are less mature than openpyxl
- Python's data science ecosystem (for Phase 2 AI Forecast) would be lost
- Less established patterns for financial services backends

---

### Option C: Django + HTMX + PostgreSQL

**Pros:**
- Single Python codebase
- Django ORM is mature

**Cons:**
- HTMX is not suitable for the dense interactive financial UX required
- Django admin is not the right UX paradigm
- Recharts / TanStack Table not usable in this paradigm
- Less ecosystem momentum for this type of application

---

## Decision

**Chosen:** Option A — Next.js + FastAPI + PostgreSQL

The combination provides:
- Finance-grade frontend component ecosystem (shadcn/ui, TanStack Table, Recharts)
- Python's superior Excel handling and future data science capabilities
- PostgreSQL's financial data integrity (NUMERIC, ACID, JSONB)
- Full Railway compatibility

The two-language context is acceptable given the team size and AI-assisted development.

---

## Consequences

**Positive:**
- Type safety end-to-end (Pydantic on backend, TypeScript on frontend)
- openpyxl for reliable Excel I/O
- Python positions the backend well for Phase 2 AI Forecast
- Rich frontend ecosystem for financial dashboards

**Negative:**
- Must maintain type synchronization between Pydantic schemas and TypeScript types manually (Phase 1); automate in Phase 2
- Two Docker images to build and deploy

**Neutral:**
- Two package managers (npm + pip)

---

## Compliance

Any deviation from this stack requires a new ADR. Dependencies may be added within the existing stack paradigm (e.g., adding a new Python library) without a new ADR, but significant additions (e.g., adding Redis, adding a new Python framework) require one.

---

## Links

- Related Spec: [/docs/specs/05_frontend_architecture.md](../specs/05_frontend_architecture.md)
- Related Spec: [/docs/specs/06_backend_architecture.md](../specs/06_backend_architecture.md)
