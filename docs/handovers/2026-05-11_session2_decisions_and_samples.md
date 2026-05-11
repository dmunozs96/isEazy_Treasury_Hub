# Handover — Session 2: All Decisions Answered + Sample Files Uploaded

**Date:** 2026-05-11  
**Session focus:** Resolving all 18 open decisions from Phase 0 + taxonomy revision + sample file inventory  
**Next session:** Bank format analysis — read each bank Excel, produce normalization mappings

---

## Session Summary

All 18 original open decisions from `OPEN_DECISIONS.md` were answered. The cash flow taxonomy was revised based on CFO input. Sample files were uploaded for bank format analysis and classification rule bootstrapping. The project is now unblocked for Phase 1, pending the bank format analysis session.

---

## Key Decisions Made This Session

### Scope
- **6 companies** in Phase 1: 5 opcos + 1 holding (all from day one)
- **Debt Calendar**: Phase 2. Phase 1 classifies debt-related movements but does no schedule matching.
- **All ~90 bank accounts** from day one — partial onboarding not viable for reconciliation purposes

### Bank Import
- **12 banks confirmed** (see inventory below)
- **No single consistent format** — each bank has its own column layout
- **Approach**: analyse sample files → produce normalization mapping per bank → build one parser per bank
- **File formats in use**: `.xlsx`, `.xls`, `.csv` (Eurocaja Rural uses CSV — parser must handle both Excel and CSV)
- **Historical load**: Full 2025 + 2026 ongoing weekly

### Forecast
- **Weekly, 13-week rolling**; output available in both weekly and monthly aggregation views
- **Group-consolidated** — CFO forecasts at group level; entity-level maintained for drill-down
- **No existing forecast Excel** — Spec 10 template will be used as the basis
- **AI Forecast**: Phase 2, last priority after all other modules complete

### Taxonomy (Spec 08 revised to v1.1 — user-validated)
```
OPERATING:  OCF_INCOME, OCF_PAYMENTS, OCF_PAYROLL, OCF_TAX
INVESTING:  ICF_CAPEX, ICF_ASSET_SALE
FINANCING:  FCF_DEBT_DRAWDOWN, FCF_DEBT_REPAYMENT, FCF_INTEREST,
            FCF_DEPOSIT_ISSUED, FCF_DEPOSIT_INCOME, FCF_DEPOSIT_RETURN,
            FCF_DIVIDENDS (rare), FCF_EQUITY (rare)
INTERNAL:   INT_INTERCOMPANY (domestic 6 entities — eliminated in consolidated view)
            INT_INTERCOMPANY_FOREIGN (BE/CO/MX/PR — NOT eliminated)
UNCLASSIFIED
```

Key changes from original taxonomy:
- OCF: merged revenue+other income → `OCF_INCOME`; merged suppliers+opex → `OCF_PAYMENTS`
- ICF: deposits moved to FCF (treasury instrument, not capital allocation); renamed to `ICF_CAPEX`
- FCF: deposit 3-event lifecycle added (`FCF_DEPOSIT_ISSUED` / `FCF_DEPOSIT_INCOME` / `FCF_DEPOSIT_RETURN`)
- INTERNAL: split into domestic (eliminable) and foreign (non-eliminable)

### Intercompany Matching (Spec 09 updated)
- Added `IN_TRANSIT` state: one leg found, other not yet seen → optimistically excluded from consolidated view for up to 5 business days → prevents spurious net imbalance from settlement timing
- Added `UNRESOLVED` state: IN_TRANSIT escalated after 5 business days → manual investigation required
- `INT_INTERCOMPANY_FOREIGN` movements are never eliminated (foreign entities are out of scope — their leg is invisible to the system)
- Added `ForeignEntity` registry model

### Classification Rules
- **Source**: VLOOKUP Excel uploaded to `/samples/classification_rules/`
- **Status**: Good starting point, known to have omissions and possible errors — treat as draft v0, not ground truth
- **Intercompany detection**: Will use description patterns from VLOOKUP file (NOT full legal names — they don't reliably appear in bank statement descriptions)
- **Approach**: Extract keyword → category mappings from VLOOKUP → seed rules engine → gaps surface as UNCLASSIFIED → fixed iteratively

### Dashboard
- **Filters**: Restore last-used + "Reset to defaults" button; default = Last 30 days; quick shortcuts include Current Month
- **NEW requirement**: Consistency & Completeness panel — shows per-account import status for a period, flags missing accounts, validates opening/closing balance reconciliation

### Operations & Deployment
- **Admin team** imports bank files; **CFO** reads dashboard
- **Railway**: one project, multiple services/environments; default Railway domain until further notice

---

## Sample Files Inventory

### Classification Rules
| File | Format | Notes |
|------|--------|-------|
| `VLOOKUP_Best-try_Bank-Stataments.xlsb` | Excel Binary (.xlsb) | CFO's manual VLOOKUP classification. Draft v0 — good starting point, known omissions. |

### Bank Statements — 12 Banks, ~60 account files

| Bank | Files | Format | Entities covered |
|------|-------|--------|-----------------|
| **Santander** | 16 | .xlsx / .xls | BPO (×2), LMS (×4), ENGAGE (×2), ISEAZY (×3), SKILLS (×3), FACTORY (×1) |
| **CaixaBank** | 11 | .xls | BPO, ENGAGE, FACTORY (×3), ISEAZY (×2), LMS (×3), SKILLS |
| **Bankinter** | 7 | .xlsx | BPO, ENGAGE, FACTORY (×2), ISEAZY, LMS, SKILLS |
| **Banca March** | 6 | .xlsx | LMS, BPO, ENGAGE, FACTORY, SKILLS, AUTHOR |
| **Ibercaja** | 6 | .xlsx | LMS, BPO, FACTORY, AUTHOR, SKILLS, ENGAGE |
| **BBVA** | 6 | .xlsx | Bizpills Group, ENGAGE, FACTORY, ISEAZY, LMS, SKILLS |
| **Sabadell** | 3 | .xls | FACTORY, BPO, LMS |
| **Abanca** | 1 | .xlsx | FACTORY |
| **Cajamar** | 1 | .xls | SKILLS |
| **Deutsche Bank** | 1 | .xls | (entity unclear from filename) |
| **Ibercaja** | _(counted above)_ | | |
| **Ruralvia** | 1 | .xlsx | (single "completo" file — may cover multiple accounts) |
| **Eurocaja Rural** | 1 | **CSV** | (different format — requires CSV parser, not Excel) |

**Total files: ~60**  
**Total banks: 12**  
**File formats: .xlsx, .xls, .xlsb, .csv**

### Entity shortcodes observed in filenames
From the file names, the following entity shortcodes appear:
- **ISEAZY** — likely the holding company
- **LMS** — isEazy LMS (opco)
- **FACTORY** — isEazy Factory (opco)
- **ENGAGE** — isEazy Engage (opco)
- **SKILLS** — isEazy Skills (opco)
- **BPO** — likely an opco (6th entity?)
- **AUTHOR / AUTHORING** — appears in some files; may be same entity as another shortcode or a 7th entity
- **BIZPILLS** — appears only in one BBVA file; may be a product/brand rather than a legal entity

**Action required before next session:** User to confirm the mapping of shortcodes to legal entity names and clarify BPO, AUTHOR, and BIZPILLS status. See open question G5.

---

## Specs Updated This Session

| Spec | Version | Change |
|------|---------|--------|
| `08_classification_engine_spec.md` | 1.0 → 1.1 | Full taxonomy revision (user-validated) |
| `09_intercompany_matching_spec.md` | 1.0 → 1.1 | IN_TRANSIT + UNRESOLVED states; foreign entity handling; ForeignEntity registry |
| `03_canonical_models.md` | 1.0 → 1.1 | IntercompanyMatch.status enum updated |

---

## Open Questions Remaining

| ID | Question | Priority | Blocks |
|----|----------|----------|--------|
| G1 | ForecastEntry group-level: NULL company_id or GROUP entity? | 🔴 | Forecast module |
| G3 | Confirm Spec 10 forecast template before Forecast Engine begins | 🟡 | Forecast module |
| G4 | Who reviews intercompany matches? (admin team or CFO?) | 🟡 | Milestone 1.5 |
| G5 | Display names of all 6 entities + clarify BPO / AUTHOR / BIZPILLS shortcodes | 🔴 | Project scaffolding |

---

## Next Session: Bank Format Analysis

**What to do:**
1. Open each bank's sample file(s)
2. For each bank, document:
   - Column headers (raw)
   - Date column name and format
   - Amount column(s) — is it one signed column, or separate debit/credit?
   - Balance column (if present)
   - Description / concept column name
   - Counterpart name column (if present)
   - IBAN column (if present)
   - Number of header rows before data begins
   - Any footer rows to skip
3. Produce a normalization mapping table: `raw column → canonical Movement field`
4. Note any bank-specific quirks (encoding, merged cells, multi-row headers, etc.)
5. Define the parser class interface for each bank
6. Confirm mappings with user before writing any parser code

**After bank analysis:**
- Answer G5 (entity names)
- Begin Milestone 1.1 (project scaffolding)

---

## Files to Read at Start of Next Session

1. This handover (`2026-05-11_session2_decisions_and_samples.md`)
2. `OPEN_DECISIONS.md` — check G1, G3, G4, G5
3. `TODO.md` — current blockers and Phase 1 backlog
4. `docs/specs/07_import_engine_spec.md` — Import Engine spec (relevant for bank format analysis session)
5. `docs/specs/08_classification_engine_spec.md` v1.1 — validated taxonomy
