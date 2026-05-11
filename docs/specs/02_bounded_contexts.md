# Spec 02 — Bounded Contexts

**Version:** 1.0  
**Status:** Draft — Pending User Review  
**Date:** 2026-05-11

---

## Overview

The system is divided into 9 bounded contexts. Each context has:
- A clear single responsibility
- Explicit input/output contracts
- Defined ownership of data
- No cross-context schema sharing (data is replicated/projected, not joined across contexts)

---

## Context 1: Bank Import Engine

**Responsibility:** Accept raw bank files, detect their format, parse and normalize them, prevent duplicate imports, and emit raw treasury movements.

**Owns:**
- `ImportBatch` — record of each file import operation
- `RawMovement` — parser output before canonicalization

**Consumes:** File uploads (multipart/form-data)

**Emits:** Normalized movement records to Treasury Ledger

**Key Rules:**
- Each file import creates exactly one `ImportBatch`
- Duplicates detected by file hash AND movement-level deduplication
- Parser is selected by format detection, not user selection
- Import is atomic: all rows succeed or the batch fails
- Failed imports are logged with full error details; raw file is preserved

**Does NOT:**
- Classify movements
- Match intercompany transfers
- Store final canonical movements

---

## Context 2: Treasury Ledger

**Responsibility:** Own and serve the canonical record of all treasury movements. This is the operational treasury truth.

**Owns:**
- `Movement` — canonical treasury movement record

**Consumes:** Normalized movements from Import Engine

**Emits:** Movement data to Classification Engine, Intercompany Matching, Analytics, Dashboard

**Key Rules:**
- Each `Movement` has a stable `movement_id` that never changes
- Movements are immutable after creation (overrides are via linked records, not mutation)
- `company_id` is always populated
- `bank_account_id` is always populated
- Amount is always signed (positive = inflow, negative = outflow)
- `value_date` and `accounting_date` both stored separately

**Does NOT:**
- Classify movements (delegates to Classification Engine)
- Match intercompany (delegates to Intercompany Matching Engine)
- Store forecast entries

---

## Context 3: Classification Engine

**Responsibility:** Assign categories to movements using a deterministic rules engine. Support manual overrides and (Phase 2) AI-assisted suggestions.

**Owns:**
- `ClassificationRule` — keyword/pattern rule definitions
- `MovementClassification` — the classification assigned to a movement
- `CategoryTaxonomy` — the hierarchy of treasury categories

**Consumes:** Movements from Treasury Ledger

**Emits:** Classification results back to movements (via MovementClassification link)

**Key Rules:**
- Rules are evaluated in priority order (highest priority wins)
- A movement can have only one active classification at a time
- Manual overrides always win over rule-based classifications
- Override is audited: who, when, previous classification, new classification
- Unclassified is a valid and explicit state
- AI suggestions are advisory only (never auto-applied without human confirmation in Phase 1)

**Classification taxonomy is hierarchical:**
```
Operating Cash Flow
  ├── Revenue Collections
  ├── Supplier Payments
  ├── Payroll
  └── Tax Payments
Investing Cash Flow
  ├── Asset Purchases
  └── Asset Sales
Financing Cash Flow
  ├── Debt Drawdown
  ├── Debt Repayment
  └── Intercompany
Internal Transfers
  └── Intercompany
Unclassified
```

**Does NOT:**
- Access bank files directly
- Make final decisions without human confirmation for overrides

---

## Context 4: Intercompany Matching Engine

**Responsibility:** Detect internal transfers between group entities, pair them, and flag them for consolidated elimination.

**Owns:**
- `InternalAccountRegistry` — known isEazy group bank accounts
- `IntercompanyMatch` — a confirmed pair of internal transfers

**Consumes:** Movements from Treasury Ledger

**Emits:**
- `IntercompanyMatch` records (to Analytics for elimination in consolidated views)
- Writes `is_intercompany = TRUE` and `intercompany_match_id` to both matched `Movement` records upon confirmation (this is the only cross-context write in the system; it is permitted because the Intercompany Matching Engine is the authoritative owner of intercompany status on movements)
- Overwrites category to `INT_INTERCOMPANY` on both matched movements via the Classification Engine's override workflow

**Key Rules:**
- Deterministic matching criteria: same absolute amount, opposite sign, within configurable date window (default: ±3 business days), both accounts in InternalAccountRegistry
- Matches require human confirmation before being marked as confirmed
- Unconfirmed matches are "proposed" — they do not affect consolidated view
- Confirmed matches are immutable (require explicit unmatching workflow)
- A movement can belong to at most one confirmed match

**Does NOT:**
- Eliminate accounting entries (this is treasury visibility, not accounting)
- Auto-confirm matches without human review (Phase 1)
- Write to any Movement fields other than `is_intercompany` and `intercompany_match_id`

---

## Context 5: Forecast Engine

**Responsibility:** Manage the three-layer forecast: Actuals, Official Forecast, and AI Forecast. Provide the 13-week rolling view.

**Owns:**
- `ForecastEntry` — a single forecast line item (amount, period, category, source layer)
- `ForecastScenario` — a named forecast version (e.g., "Budget 2026", "Revised Q2")

**Consumes:**
- Official Forecast: Excel template uploads
- Actuals: from Treasury Ledger (read)
- AI Forecast: from AI Forecast Engine (Phase 2)

**Emits:** Forecast data to Analytics Engine and Dashboard

**Key Rules:**
- Forecast horizon: rolling 13 weeks from current date
- Three source layers: `ACTUALS`, `OFFICIAL`, `AI`
- Actuals layer is always the Treasury Ledger — not a copy
- Official Forecast entries are versioned per upload
- AI Forecast entries are never shown as official — always labeled
- Weekly granularity as minimum; daily optional

**Does NOT:**
- Store actual bank movements (always reads from Treasury Ledger)
- Allow AI forecasts to override Official Forecast without explicit user action

---

## Context 6: Debt Calendar Engine

**Responsibility:** Track debt instruments, their amortization schedules, interest payment schedules, and upcoming treasury obligations.

**Owns:**
- `DebtInstrument` — loan, credit line, bond, or other debt instrument
- `DebtScheduleEntry` — individual principal or interest payment event
- `DebtCovenant` — covenant condition and monitoring status

**Consumes:** Manual data entry (no automated feed in Phase 1)

**Emits:** Upcoming obligation data to Analytics and Dashboard

**Key Rules:**
- All amounts in EUR (Phase 1 only)
- Payment dates generate alerts at configurable horizons (30/60/90 days)
- Instruments have explicit maturity dates
- Interest schedule can be: fixed, variable reference + spread, or manually entered
- Covenants are informational only in Phase 1 (no automated testing)

**Does NOT:**
- Integrate with banking systems for debt balances
- Perform accounting amortization calculations

---

## Context 7: Treasury Analytics Engine

**Responsibility:** Compute treasury KPIs, variance analysis, liquidity metrics, and consolidated cash flow statements from the data owned by other contexts.

**Owns:** No primary data — reads from all other contexts.

**Emits:** Computed metrics to Dashboard

**Key Computations:**
- Cash position: sum of current balances per entity and consolidated
- Direct cash flow statement: classify and aggregate movements by period
- Forecast vs actuals variance: by week, by category
- Liquidity runway: current cash / average weekly outflow
- Intercompany balance summary: net positions between entities
- Concentration analysis: cash by bank, by entity, by category

**Does NOT:**
- Modify any data
- Own canonical records
- Generate forecast entries

---

## Context 8: Excel Integration Layer

**Responsibility:** Provide reliable Excel import and export capabilities for all system functions. Manage Excel templates and ensure roundtrip fidelity.

**Owns:**
- `ExcelTemplate` — versioned template definitions
- No business data

**Consumes:** All contexts (import/export)

**Emits:** Parsed data to relevant contexts; formatted Excel files to users

**Key Rules:**
- Template versions are explicit — old template versions must still be importable for backward compatibility
- All exports must be reproducible (same data = same Excel output)
- Excel is the primary non-UI interface — it is not a legacy workaround

**Does NOT:**
- Store business data itself
- Apply business logic to imported data (delegates to relevant engines)

---

## Context 9: Dashboard & Visualization Layer

**Responsibility:** Aggregate and display treasury data for the CFO and operations staff. Provide filtering, drill-down, and export capabilities.

**Owns:** No data. Read-only aggregation layer with respect to data storage.

**Consumes:** All contexts via API (read)

**Emits:**
- Rendered UI components
- User action requests forwarded to the owning context APIs (e.g., intercompany confirmation → Intercompany Matching API; classification override → Classification Engine API). The Dashboard does NOT write data directly — it calls the relevant context's API endpoint, which owns the write.

**Note on "read-only":** The Dashboard layer does not own or modify any data. However, it surfaces workflow actions (confirm/reject intercompany matches, override classifications) that trigger writes in the respective owning contexts via API calls. This is by design — the Dashboard is the UI surface, the engines own the mutations.

**Key Capabilities:**
- Cash position widget (real-time, by entity/consolidated)
- Cash flow statement view (direct method, weekly/monthly)
- 13-week forecast chart (3 layers)
- Intercompany balance matrix
- Debt calendar timeline
- Variance analysis table
- Advanced filtering: date range, company, bank, category, amount range
- Export any view to Excel

**Does NOT:**
- Apply business logic
- Store data
- Modify data (export and read only, except triggering human confirmations)

---

## Context Interaction Rules

1. Contexts communicate via explicit API contracts (no direct DB joins across contexts)
2. Data flows are unidirectional where possible (see architecture diagram)
3. The Treasury Ledger is the central hub — all movement data flows through it
4. No context may write directly to another context's tables
5. Cross-context reads are acceptable (read-only via service layer)
