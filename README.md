# isEazy Treasury Hub

Internal Treasury Intelligence Platform for the isEazy Group.

## Quick Start for New Sessions

1. Read [CLAUDE.md](CLAUDE.md) — absolute rules and project identity
2. Read [TODO.md](TODO.md) — current work queue and open questions
3. Read the latest handover in [/docs/handovers/](docs/handovers/)
4. Read the relevant spec before touching any module

## Current Phase

**Phase 0 — Architectural Foundation** — COMPLETE  
**Phase 1 — Active Development** — implementation complete through Milestone 1.6c  
**Next step:** Railway deployment, then test/polish against the live environment

See [TODO.md](TODO.md) for full status.

## Current Product Surface

- Bank import engine with 12 bank parsers and raw movement audit trail
- Treasury ledger with filtering, Excel export, and manual category override
- Rules-first classification engine with batch reclassification
- Intercompany matching workflow with proposed, in-transit, unresolved, confirmed, and rejected states
- Dashboard, consistency panel, settings view, and cash flow statement view

## Documentation

| Document | Path |
|----------|------|
| System Architecture | [docs/specs/00_architecture.md](docs/specs/00_architecture.md) |
| Product Vision | [docs/specs/01_product_vision.md](docs/specs/01_product_vision.md) |
| Bounded Contexts | [docs/specs/02_bounded_contexts.md](docs/specs/02_bounded_contexts.md) |
| Canonical Models | [docs/specs/03_canonical_models.md](docs/specs/03_canonical_models.md) |
| Database Design | [docs/specs/04_database_design.md](docs/specs/04_database_design.md) |
| All Specs | [docs/specs/](docs/specs/) |
| ADRs | [docs/adr/](docs/adr/) |
| Handovers | [docs/handovers/](docs/handovers/) |
| Templates | [docs/templates/](docs/templates/) |

## Tech Stack

- **Frontend:** Next.js, TypeScript, TailwindCSS, shadcn/ui, TanStack Table, Recharts, Zustand
- **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.0, Pydantic v2, Alembic
- **Database:** PostgreSQL
- **Deployment:** Railway

## Architecture

Modular monolith with 9 bounded contexts:
1. Bank Import Engine
2. Treasury Ledger
3. Classification Engine
4. Intercompany Matching Engine
5. Forecast Engine
6. Debt Calendar Engine
7. Treasury Analytics Engine
8. Excel Integration Layer
9. Dashboard & Visualization Layer

## Development Rules

This project follows **Spec-Driven Development (SDD)**:
- No implementation without an approved spec
- One session = one module
- Every session ends with a handover document
- Repository is the system memory — no reliance on conversational memory

See [docs/specs/18_session_workflow.md](docs/specs/18_session_workflow.md) for the full protocol.
