# isEazy Treasury Hub — Claude Session Guide

This file is the **primary session continuity document**. Every AI session MUST read this file first.

## Project Identity

**Name:** isEazy Treasury Hub  
**Type:** Internal Treasury Intelligence Platform  
**Company:** isEazy Group (Spanish SME e-learning group, multiple opcos + holding)  
**Phase:** Phase 1 — EUR-only, desktop-first, Excel-native  
**Deployment:** Railway  
**Status:** Phase 0 — Architectural Foundation (no feature code yet)

## Mandatory Reading Before Any Work

1. `/docs/specs/00_architecture.md` — system architecture overview
2. `/docs/specs/02_bounded_contexts.md` — domain boundaries
3. `/docs/specs/03_canonical_models.md` — canonical data models
4. `/TODO.md` — current work queue and blockers
5. `/docs/OPEN_DECISIONS.md` — user decisions pending (check for new answers before proceeding)
6. Latest handover in `/docs/handovers/` sorted by date descending

## Absolute Rules (Non-Negotiable)

### SDD FIRST — CODE SECOND
- No implementation without approved spec
- Every module starts with spec, contracts, edge cases, acceptance criteria
- Spec approval = explicit sign-off in session or written in TODO.md

### ONE SESSION = ONE MODULE
- One bounded context per session
- Never mix domain concerns
- If scope creep appears, log it in TODO.md and stop

### MANDATORY HANDOVERS
- Every session ends with a handover document at `/docs/handovers/YYYY-MM-DD_<module>.md`
- Format is standardized — use `/docs/templates/HANDOVER_TEMPLATE.md`

### PERSIST STATE IN FILES
- No conversational memory
- All decisions live in specs, ADRs, or handovers
- Repository = system memory

## Tech Stack (Mandatory — No Substitutions Without ADR)

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js, TypeScript, TailwindCSS, shadcn/ui, TanStack Table, Recharts, Zustand |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.0 typed, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Infra | Railway |

## Monorepo Structure

```
/frontend       — Next.js application
/backend        — FastAPI application
/shared         — shared types, contracts, schemas
/docs           — all specs, ADRs, handovers, templates
/scripts        — data migration, seeding, tooling
/infrastructure — Railway config, Docker, env templates
```

## Bounded Contexts (Do Not Cross Without Explicit Design)

1. Bank Import Engine
2. Treasury Ledger
3. Classification Engine
4. Intercompany Matching Engine
5. Forecast Engine
6. Debt Calendar Engine
7. Treasury Analytics Engine
8. Excel Integration Layer
9. Dashboard & Visualization Layer

## Phase Gate: Architectural Foundation

Current milestone: **ARCHITECTURAL FOUNDATION COMPLETE**  
This milestone is reached when ALL of the following are done:
- [ ] All 19 spec files exist and are substantive
- [ ] All ADRs for major decisions are written
- [ ] Canonical models are fully defined
- [ ] Database schema draft is complete
- [ ] Contract interfaces are defined for all bounded contexts
- [ ] Handover template is validated
- [ ] TODO.md governance is operational

Do NOT begin implementation until this milestone is checked off.

## How to Start a New Session

1. Read this file
2. Read `/TODO.md`
3. Read the latest handover
4. Read the relevant spec for the current module
5. Confirm scope with user before writing any code
6. At session end: write handover, update TODO.md
