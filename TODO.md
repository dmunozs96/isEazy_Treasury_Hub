# isEazy Treasury Hub — TODO & Work Queue

Last updated: 2026-05-11 (session 11 feature-completion review complete)
Current phase: **Phase 1 — Active Development**
Current milestone: Milestone 1.6c COMPLETE — Next: Railway deploy, then test/polish

---

## Immediate Next Session — Railway Deployment

**Feature-completion review is DONE (2026-05-11). Parser suite, frontend type-check, lint, and production build are passing.**

- [x] ~~Milestone 1.1 — Project Scaffolding~~ ✅ DONE 2026-05-11
- [x] ~~Milestone 1.2 — Bank Import Engine~~ ✅ DONE 2026-05-11
- [x] ~~Milestone 1.3 — Treasury Ledger~~ ✅ DONE 2026-05-11
- [x] ~~Milestone 1.4 — Classification Engine~~ ✅ DONE 2026-05-11
- [x] ~~Milestone 1.5 — Intercompany Matching Engine~~ ✅ DONE 2026-05-11
- [x] ~~Milestone 1.6 — Dashboard & Visualization (core)~~ ✅ DONE 2026-05-11
- [x] ~~Milestone 1.6b — Consistency & Completeness Panel~~ ✅ DONE 2026-05-11
- [x] ~~Milestone 1.6c — Cash Flow Statement view~~ ✅ DONE 2026-05-11
- [ ] Railway Deployment (all config ready — pure ops; Docker Desktop was not running locally, so Postgres-backed full test suite still needs live DB verification)
- [ ] Test & polish pass after deployment target is selected

### Railway first deployment (all config is ready — just needs Railway project creation)
1. Use one Railway project/environment only → the canvas must contain frontend, backend, and PostgreSQL together
2. Set backend root directory `/backend` and config file `/backend/railway.toml`
3. Set frontend root directory `/frontend` and config file `/frontend/railway.toml`
4. Set env vars from `.env.example` files on each service; frontend should use `BACKEND_URL=https://<backend-domain>`
5. Push to GitHub / connect repo — Railway auto-deploys
6. Run seed once: `cd backend && python ../scripts/seed.py` (against Railway DB via Railway CLI)
7. Verify `GET /api/v1/health` returns `{"status":"ok"}` and frontend Network calls hit `/api/v1/...` on the frontend domain

See `infrastructure/RAILWAY_DEPLOYMENT.md` for the exact service and env setup.

### Pre-deploy verification status (session 11)
1. Backend parser integration suite: `77 passed`
2. Backend Python compile check: passed
3. Frontend `npm run type-check`: passed
4. Frontend `npm run lint`: passed
5. Frontend `npm run build`: passed on Next `14.2.35`
6. Remaining npm audit findings require a breaking Next 16 upgrade; do not force-upgrade until scheduled as a dependency upgrade pass

### First full data run (after Railway is live)
1. Seed `bank_accounts` for all 6 companies (~90 accounts)
2. Upload bank files via `POST /api/v1/imports/`
3. Run `POST /api/v1/classifications/batch`
4. Run `POST /api/v1/intercompany/scan`
5. CFO reviews PROPOSED matches in `/intercompany`

---

## Remaining Open Questions

| ID | Question | Priority | Blocks |
|----|----------|----------|--------|
| G1 | ForecastEntry group-level: NULL company_id or GROUP entity? | 🔴 | Forecast module (Milestone 1.6+) |
| G3 | Confirm Spec 10 forecast template structure before Forecast Engine begins | 🟡 | Forecast module |
| G4 | Who reviews intercompany matches — admin team or CFO? | 🟡 | Milestone 1.5 |
| G6 | Names/description patterns for foreign entities (Belgium, Colombia, Mexico, Puerto Rico) | 🟡 | Classification module (Milestone 1.4) |

---

## Phase 0 Checklist ✅ COMPLETE

All spec files, ADRs, templates, and governance documents written.
All 18 original open decisions answered (session 2, 2026-05-11).
Company registry confirmed. Sample files uploaded. Taxonomy validated.

See `/docs/OPEN_DECISIONS.md` for the full decision log.

---

## Phase 1 Backlog

### Milestone 1.1 — Project Scaffolding
*Start after bank format analysis is complete and G5 is confirmed.*

- [ ] Initialize Next.js project in `/frontend`
- [ ] Initialize FastAPI project in `/backend`
- [ ] Set up PostgreSQL on Railway (dev environment)
- [ ] Configure Alembic migrations
- [ ] Set up shared types in `/shared`
- [ ] Configure environment variable management (.env templates)
- [ ] Seed company registry (6 entities — see `/docs/company_registry.md`)
- [ ] Seed foreign entity registry (pending G6)
- [ ] Set up CI skeleton

### Milestone 1.2 — Bank Import Engine ✅ COMPLETE 2026-05-11

- [x] Parser abstraction base class (`parsers/base.py` — ParsedRow + BankParser + utilities)
- [x] One parser per bank (12 parsers: Abanca, BBVA, Banca March, Bankinter, CaixaBank, Cajamar, Deutsche Bank, Eurocaja Rural, Ibercaja, Ruralvia, Sabadell, Santander)
- [x] CSV parser for Eurocaja Rural
- [x] Parser auto-detection logic (`detector.py` — filename prefix matching)
- [x] Excel normalization pipeline (`normalizer.py` — ParsedRow → Movement fields)
- [x] Duplicate prevention (`deduplicator.py` — file_hash + movement_hash SHA-256)
- [x] ImportBatch model + API endpoints (POST/GET /api/v1/imports/)
- [x] File traceability audit trail (raw_data JSON in RawMovement, linked to Movement)
- [x] Unit tests per parser (`tests/test_import_engine/test_parsers.py`)

### Milestone 1.3 — Treasury Ledger ✅ COMPLETE 2026-05-11

- [x] Movement canonical model + DB table
- [x] CRUD API with filtering and pagination (`GET /movements/`, `GET /movements/{id}`)
- [x] Excel export endpoint (`GET /movements/export`) — styled xlsx, max 10k rows
- [x] Basic Treasury Ledger UI (TanStack Table) — server-side pagination + filters
- [x] Inline category edit — click badge → select → auto-saves via `PATCH /movements/{id}/category`
- [x] Category taxonomy list endpoint (`GET /classifications/categories`)

### Milestone 1.4 — Classification Engine ✅ COMPLETE 2026-05-11

- [x] Rules engine (deterministic, keyword-based) — `backend/app/services/classification/engine.py`
- [x] Seed taxonomy v1.1 (21 entries: 4 section headers + 16 leaves + UNCLASSIFIED) — `scripts/seed.py`
- [x] Seed standard classification rules (27 rules: 10 intercompany + 17 treasury)
- [x] Seed intercompany rules from company registry (all 6 entities, all keywords)
- [ ] Seed foreign intercompany rules — **blocked on G6** (entity names unknown)
- [x] Manual override workflow — already in Milestone 1.3 (`PATCH /movements/{id}/category`)
- [x] Batch re-classification endpoint (`POST /classifications/batch`)
- [x] Single movement classify endpoint (`POST /movements/{id}/classify`)
- [x] Rules CRUD API (GET/POST/PUT/DELETE `/classifications/rules`)
- [x] Classification UI — `/classification` page (rules table + batch buttons + taxonomy reference)

### Milestone 1.5 — Intercompany Matching Engine ✅ COMPLETE 2026-05-11

- [x] Migration 0002 — IN_TRANSIT/UNRESOLVED status, nullable movement_in_id, score, transit_expires_at, foreign_entities table
- [x] Deterministic matching algorithm (amount ±€2, ≤3 business days, score 0–1)
- [x] IN_TRANSIT state logic — created when counterpart_iban is internal but second leg not yet imported
- [x] UNRESOLVED escalation — after 5 business days in IN_TRANSIT
- [x] Scan API — `POST /api/v1/intercompany/scan` (escalate → resolve transit → match new)
- [x] Confirm/Reject workflow — marks both movements `is_intercompany=TRUE` on confirm
- [x] Manual match creation — `POST /api/v1/intercompany/matches/manual`
- [x] Balance matrix — `GET /api/v1/intercompany/summary`
- [x] Intercompany review UI — match cards with expand/collapse, confirm/reject buttons, balance matrix tab
- [x] Foreign entity registry CRUD (table + API)
- [ ] Seed foreign entities — **blocked on G6** (CFO to provide names for Belgium, Colombia, Mexico, Puerto Rico)

### Milestone 1.6 — Dashboard & Visualization ✅ CORE COMPLETE 2026-05-11

- [x] Cash position widget (consolidated + per entity) — KPI card + horizontal bar chart by company
- [x] 13-week cash flow chart (actuals only in Phase 1) — ComposedChart inflow/outflow bars + net line
- [x] Intercompany summary widget — pending/in-transit/unresolved counts with links
- [x] Quick filter shortcuts: Last 7 days | Last 30 days | Current Month | Last 13 Weeks + Reset
- [x] Net flow week-to-date KPI card
- [x] Cash flow statement view (weekly + monthly aggregation table) — DONE 2026-05-11
- [x] ~~Consistency & Completeness panel (3 sections)~~ ✅ DONE 2026-05-11 (Milestone 1.6b)
- [x] ~~HoldCo (BPO) revenue warning in data quality section~~ ✅ DONE 2026-05-11 (Milestone 1.6b)
- [x] Export to Excel for Cash Flow Statement — DONE 2026-05-11

---

## Known Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Bank format heterogeneity | High | High | One parser class per bank; mappings confirmed before code |
| VLOOKUP classification gaps | High | Medium | UNCLASSIFIED state surfaces gaps; rules updated iteratively |
| Intercompany matching false positives | Medium | High | Human confirmation required; IN_TRANSIT window prevents noise |
| Foreign entity transfers misclassified as domestic | Medium | High | Foreign entity registry seeded before classification runs |
| Forecast group-level design (G1) | Medium | High | Decision required before Forecast module — do not start without it |
| Scope creep | Medium | High | Non-goals spec (Spec 15) enforced aggressively |

---

## Completed Work

| Date | Item |
|------|------|
| 2026-05-11 | Phase 0 — Full architectural foundation (19 specs, 5 ADRs, templates, governance) |
| 2026-05-11 | Session 2 — All 18 open decisions answered |
| 2026-05-11 | Spec 08 v1.1 — Taxonomy revised and user-validated |
| 2026-05-11 | Spec 09 updated — IN_TRANSIT state, UNRESOLVED escalation, foreign entity handling |
| 2026-05-11 | Spec 13 updated — Consistency & Completeness panel added |
| 2026-05-11 | Spec 03 updated — IntercompanyMatch status enum updated |
| 2026-05-11 | Company registry created and fully confirmed (`/docs/company_registry.md`) |
| 2026-05-11 | Sample files uploaded: 12 banks (~60 files) + VLOOKUP classification Excel |
| 2026-05-11 | Milestone 1.2 — Full Bank Import Engine (12 parsers, detector, normalizer, deduplicator, import service, router, tests) |
| 2026-05-11 | Milestone 1.3 — Treasury Ledger (movements API, Excel export, category override, TanStack Table UI) |
| 2026-05-11 | Milestone 1.4 — Classification Engine (rules engine, taxonomy v1.1, 27 seeded rules, batch classify API, classification UI) |
| 2026-05-11 | Milestone 1.5 — Intercompany Matching Engine (matching algorithm, IN_TRANSIT/UNRESOLVED state machine, scan API, confirm/reject workflow, balance matrix UI, Railway deployment readiness) |
| 2026-05-11 | Milestone 1.6 — Dashboard core (analytics backend endpoint, cash position chart, 13-week chart, IC alerts widget, quick date filters, KPI cards) |
| 2026-05-11 | Milestone 1.6b — Consistency & Completeness Panel (GET /analytics/consistency, Section A import coverage, Section B balance reconciliation, Section C data quality warnings, Settings page, dashboard alert banner) |
