# Open Decisions — isEazy Treasury Hub

**Purpose:** This file captures all decisions and questions that require user input before or during Phase 1 development.

**Last updated:** 2026-05-11 (all 18 decisions answered — session 2)  
**Status key:** 🔴 Blocking | 🟡 Important | 🟢 Can proceed without (lower priority) | ✅ Answered

---

## GROUP A — Scope & Phase

---

### A1 ✅ Is the Debt Calendar in Phase 1 or Phase 2?

**Decision: Phase 2.**

Not required for cash flow visibility. No direct dependency on daily operations in Phase 1. Movements that appear to be debt repayments or drawdowns will be classified as `FCF_DEBT_REPAYMENT` or `FCF_DEBT_DRAWDOWN` in the Classification Engine, but no matching against a debt schedule will occur. Phase 1 dashboard will show a "Coming Soon" placeholder for the Debt Calendar section.

---

### A2 ✅ How many companies are in scope for Phase 1?

**Decision: All 6 companies from day one.**

- 5 operating companies (opcos)
- 1 holding company
- All 6 included in Phase 1 scope — no pilot subset

**Impact:** Company registry must be seeded with all 6 entities at setup. Intercompany matching engine must cover all entity pairs from launch.

---

### A3 ✅ All accounts or rolling onboarding?

**Decision: All accounts from day one.**

Rationale: The only way to verify that imported figures reconcile is to have all accounts present. Partial onboarding would make reconciliation impossible.

**Approximate total:** ~90 bank accounts across all 6 entities and all banks.

**Prerequisite:** Before building parsers, the user will submit one sample Excel export per bank so we can map each format and design the normalization pipeline. See `/samples/bank_statements/` folder.

---

## GROUP B — Bank Import

---

### B1 ✅ Which specific bank formats are in use today?

**Decision: More than 10 banks — exact list TBD pending sample file analysis.**

The original assumption (Santander, BBVA, CaixaBank, Sabadell) is likely a subset. The exact list will be determined when the user submits one sample export file per bank to the `/samples/bank_statements/` folder.

**Process agreed:**
1. User places one anonymized sample Excel per bank in `/samples/bank_statements/`
2. Claude analyses each file: column structure, date formats, amount sign conventions, available fields
3. Claude produces a normalization mapping per bank
4. Parsers are designed based on confirmed mappings
5. A master unified bank statement schema is defined

**Parser design goal:** Unify all formats into the canonical `Movement` model — single consolidated view across all ~90 accounts.

---

### B2 ✅ Consistent export format per bank?

**Decision: Each bank has its own layout — no cross-bank consistency expected.**

Each bank's portal produces its own column structure, date format, amount representation, and field availability. Some banks may even differ across portal sections. The parser abstraction layer (one parser class per bank) must handle this. Sample analysis (B1 process above) will reveal the full extent of variation.

---

### B3 ✅ Historical import range?

**Decision: Full calendar year 2025 + 2026 ongoing (weekly updates).**

- **Initial load:** All of 2025 (January 1 – December 31, 2025)
- **Ongoing:** 2026 movements imported on a weekly basis by the admin team
- This gives 12+ months of history at launch, sufficient for seasonality patterns if AI Forecast is activated later

---

## GROUP C — Forecast Engine

---

### C1 ✅ Current Official Forecast Excel structure?

**Decision: No existing forecast Excel exists.**

The finance team does not currently use a structured Excel for cash flow forecasting. The proposed template structure from Spec 10 will be used as the basis. Spec 10 template should be reviewed and confirmed in the next session before the Forecast Engine module begins.

---

### C2 ✅ Weekly or daily forecast granularity?

**Decision: Weekly (13-week rolling horizon), with monthly aggregation as output.**

- Forecast input and storage: weekly (Monday–Sunday)
- Rolling horizon: 13 weeks forward
- Dashboard output: both weekly and monthly views must be available
- Monthly view = aggregation of weekly data, not a separate data model
- This is the industry standard for treasury direct cash flow forecasting

**Impact:** `ForecastEntry.week_start_date` model confirmed. The weekly-to-monthly aggregation is a query/presentation layer concern, not a data model change.

---

### C3 ✅ One file or one per company for Official Forecast?

**Decision: Group-level consolidated forecast (one file for all entities combined).**

- The Official Forecast is submitted at group level — not entity by entity
- The system must still store and display entity-level granularity (for drill-down and intercompany analysis)
- Primary comparison view (Actual vs. Official vs. AI) is at group level
- Entity-level breakdown available as a secondary drill-down

**Impact on data model:** `ForecastEntry` must support a `company_id = NULL` or a special "GROUP" company record for group-level entries, OR the forecast template requires the user to specify amounts per company even if the CFO views it consolidated. This needs a design decision before the Forecast Engine module — log as a new open question for that session.

---

### C4 ✅ AI Forecast priority?

**Decision: Critical but not urgent — Phase 2, last priority.**

- AI Forecast is important to the CFO but not needed at launch
- Build order: all Phase 1 modules first → AI Forecast last (after rest of project is complete)
- Prerequisite: 80%+ classification coverage and 13+ weeks of actual data (which Phase 1 will accumulate)
- Spec 14 (AI Forecast) remains unchanged; no spec work needed now

---

## GROUP D — Classification

---

### D1 ✅ Cash flow taxonomy — CONFIRMED AND REVISED (session 2)

**Status: Validated. Spec 08 updated to v1.1. Spec 09 updated with IN_TRANSIT state and foreign entity handling.**

Revised taxonomy (user-validated):
```
OPERATING:  OCF_INCOME, OCF_PAYMENTS, OCF_PAYROLL, OCF_TAX
INVESTING:  ICF_CAPEX, ICF_ASSET_SALE
FINANCING:  FCF_DEBT_DRAWDOWN, FCF_DEBT_REPAYMENT, FCF_INTEREST,
            FCF_DEPOSIT_ISSUED, FCF_DEPOSIT_INCOME, FCF_DEPOSIT_RETURN,
            FCF_DIVIDENDS (rare), FCF_EQUITY (rare)
INTERNAL:   INT_INTERCOMPANY (domestic 6 entities — eliminated in consolidated view)
            INT_INTERCOMPANY_FOREIGN (BE/CO/MX/PR — NOT eliminated, real cash flow)
UNCLASSIFIED
```

Key changes from original:
- OCF: Merged revenue+other income → OCF_INCOME; merged suppliers+opex → OCF_PAYMENTS
- ICF: Removed ICF_INVESTMENT (deposits moved to FCF); renamed ICF_ASSET_PURCHASE → ICF_CAPEX
- FCF: Added deposit lifecycle (ISSUED / INCOME / RETURN)
- INTERNAL: Split into domestic (eliminable) and foreign (non-eliminable)
- Matching engine: Added IN_TRANSIT and UNRESOLVED states for cash in transit handling

---

### D2 ✅ Sample transaction descriptions?

**Decision: User will provide. Folder created.**

Path: `/samples/transaction_descriptions/`

User should place a text or Excel file with 30–50 anonymized transaction descriptions from bank statements (descriptions only — no amounts or IBANs needed). These will be used to seed the initial classification rules before go-live.

Example format:
```
TRANSF. RECIBIDA DE ISEAZY AUTHORING SL
RECIBO NOMINAS MARZO 2026
LIQUIDACION IVA 1T 2026 AEAT
PAGO PROVEEDOR ADOBE SYSTEMS
```

---

## GROUP E — UX & Product Decisions

---

### E1 ✅ Filter persistence?

**Decision: Restore last-used, with a "Reset to defaults" button.**

When the CFO reopens the dashboard, filters restore to the previous session's state. A clearly visible "Reset" button resets to defaults (Last 30 days, All Companies) with a single click.

---

### E2 ✅ Default date range on the dashboard?

**Decision: Last 30 days (with "Current Month" as a quick shortcut).**

- Default on first open or after reset: Last 30 days
- Quick filter buttons should include: Last 7 days | Last 30 days | Current Month | Last 13 Weeks | Custom

---

### E3 ✅ Debt payment tolerance — N/A for Phase 1.

**Decision: Not applicable.**

Debt Calendar is Phase 2. No debt schedule matching in Phase 1. All movements that appear to be debt-related will be classified as `FCF_DEBT_DRAWDOWN` or `FCF_DEBT_REPAYMENT` via the classification rules engine, but no amount/date tolerance matching against a schedule is needed.

---

## GROUP F — Deployment & Operations

---

### F1 ✅ Railway environment strategy?

**Decision: One Railway project, multiple services and environments within it.**

Simpler to manage, lower cost. All services (frontend, backend, database) live in one Railway project. Environments: development + production (staging can be added if needed).

---

### F2 ✅ Who does what operationally?

**Decision:**
- **Bank file import:** Admin team — logs into each bank portal, downloads Excel exports, uploads to the application
- **Intercompany match review:** TBD (not specified — likely CFO or admin team; confirm before Milestone 1.5)
- **Debt calendar management:** Phase 2 — not applicable now
- **Dashboard primary user:** CFO (Daniel Muñoz, dmunoz@iseazy.com)

**NEW REQUIREMENT (logged from this decision):**
The dashboard must include a **Consistency & Completeness panel** — a control view that allows the CFO to verify:
1. Which bank accounts have been imported for a given period (completeness — are any missing?)
2. Whether imported movements reconcile with the opening and closing balance reported by the bank (consistency — do the figures add up?)

This is a critical quality-of-life requirement for the CFO to trust the data before reading any analytics. Must be included in Milestone 1.6 (Dashboard & Visualization) scope.

---

### F3 ✅ Preferred domain/URL?

**Decision: Default Railway domain for now.**

No custom domain in Phase 1. The app will use Railway's default generated URL. A proper custom domain (e.g., `treasury.iseazy.com`) will be configured after sufficient testing and internal sign-off. No DNS or domain setup needed at development time.

---

## Answer Tracking

| ID | Question | Status | Answered |
|----|----------|--------|---------|
| A1 | Debt Calendar Phase 1 or 2? | ✅ Done | 2026-05-11 |
| A2 | How many companies in Phase 1? | ✅ Done | 2026-05-11 |
| A3 | All 90 accounts or rolling? | ✅ Done | 2026-05-11 |
| B1 | Which bank formats? | ✅ Done (pending samples) | 2026-05-11 |
| B2 | Consistent export format per bank? | ✅ Done | 2026-05-11 |
| B3 | Historical import range? | ✅ Done | 2026-05-11 |
| C1 | Current forecast Excel structure? | ✅ Done | 2026-05-11 |
| C2 | Weekly or daily granularity? | ✅ Done | 2026-05-11 |
| C3 | One file or one per company? | ✅ Done | 2026-05-11 |
| C4 | AI Forecast priority? | ✅ Done | 2026-05-11 |
| D1 | Taxonomy matches CFO's view? | ✅ Done (revised) | 2026-05-11 |
| D2 | Sample transaction descriptions? | ✅ Done (folder created) | 2026-05-11 |
| E1 | Filter persistence? | ✅ Done | 2026-05-11 |
| E2 | Default date range on dashboard? | ✅ Done | 2026-05-11 |
| E3 | Debt payment tolerance? | ✅ N/A (Phase 2) | 2026-05-11 |
| F1 | Railway environment strategy? | ✅ Done | 2026-05-11 |
| F2 | Who does what operationally? | ✅ Done | 2026-05-11 |
| F3 | Preferred domain/URL? | ✅ Done | 2026-05-11 |

---

## NEW Open Questions (Discovered During Session 2)

| ID | Question | Priority | Origin |
|----|----------|----------|--------|
| G1 | ForecastEntry group-level design: NULL company_id or GROUP entity? | 🔴 Before Forecast module | C3 decision |
| G2 | Confirm or modify cash flow taxonomy (D1) | ✅ Done (session 2) | D1 |
| G3 | Confirm Spec 10 forecast template structure before Forecast Engine begins | 🟡 Before Forecast module | C1 |
| G4 | Who reviews and confirms intercompany matches? | 🟡 Before Milestone 1.5 | F2 |
| G5 | Entity names and holding flag fully confirmed. See `/docs/company_registry.md` | ✅ Done | A2 |
| G6 | Intercompany + foreign entity classification patterns → derived from VLOOKUP Excel | ✅ Source material approach agreed | D1 |
