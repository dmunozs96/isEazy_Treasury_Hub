# Spec 03 — Canonical Models

**Version:** 1.0  
**Status:** Draft — Requires User Validation on Field Names  
**Date:** 2026-05-11

---

## Overview

Canonical models define the shape of all core domain entities. These are the contracts that all system layers (API, database, frontend) must respect. Changes to canonical models require a new spec version and an ADR if breaking.

All monetary amounts are stored as `NUMERIC(18,2)` in EUR. All timestamps are UTC.

---

## Model: Company

```
Company
├── id: UUID (PK)
├── name: str — full legal name ("isEazy Learning SL")
├── short_name: str — display name ("isEazy Learning")
├── tax_id: str — Spanish CIF/NIF
├── is_holding: bool — true for the holding entity
├── is_active: bool
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

**Notes:**
- All companies in the isEazy group are seeded during setup
- `is_holding` used for consolidated view logic

---

## Model: BankAccount

```
BankAccount
├── id: UUID (PK)
├── company_id: UUID (FK → Company)
├── bank_name: str — ("Santander", "BBVA", "CaixaBank", ...)
├── account_name: str — internal label
├── iban: str — full IBAN (masked for display)
├── currency: str — "EUR" always in Phase 1
├── is_internal: bool — true if this is a known intercompany account
├── is_active: bool
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

**Notes:**
- `is_internal` flags accounts that appear in intercompany transfers
- IBAN stored unmasked in DB; API returns masked version by default

---

## Model: ImportBatch

```
ImportBatch
├── id: UUID (PK)
├── company_id: UUID (FK → Company)
├── bank_account_id: UUID (FK → BankAccount)
├── filename: str — original filename
├── file_hash: str — SHA-256 of file content (deduplication key)
├── file_format: str — ("SANTANDER_EXCEL", "BBVA_CSV", "GENERIC_CSV", ...)
├── status: enum — PENDING | PROCESSING | COMPLETED | FAILED | DUPLICATE
├── row_count: int — total rows in file
├── imported_count: int — rows successfully imported
├── error_count: int — rows with errors
├── error_log: JSON — list of row-level errors
├── imported_by: str — user identifier
├── imported_at: datetime (UTC)
├── processed_at: datetime (UTC, nullable)
└── notes: str (nullable) — operator notes
```

---

## Model: RawMovement

```
RawMovement
├── id: UUID (PK)
├── import_batch_id: UUID (FK → ImportBatch)
├── row_number: int — source row in original file
├── raw_data: JSON — original parsed row as key-value pairs
├── normalized_date: date (nullable) — value date extracted
├── normalized_amount: NUMERIC(18,2) (nullable)
├── normalized_description: str (nullable)
├── parse_status: enum — OK | ERROR | SKIPPED
├── parse_error: str (nullable)
└── movement_id: UUID (FK → Movement, nullable) — link after canonicalization
```

---

## Model: Movement (Core Entity)

```
Movement
├── id: UUID (PK)
├── company_id: UUID (FK → Company)
├── bank_account_id: UUID (FK → BankAccount)
├── import_batch_id: UUID (FK → ImportBatch)
├── raw_movement_id: UUID (FK → RawMovement)
│
├── value_date: date — date the movement was valued by the bank
├── accounting_date: date — date the movement was booked (may differ)
│
├── amount: NUMERIC(18,2) — signed (+ inflow, - outflow)
├── currency: str — "EUR" in Phase 1
├── balance_after: NUMERIC(18,2, nullable) — running balance if provided
│
├── description: str — normalized description from bank
├── counterpart_name: str (nullable) — payer/payee name if available
├── counterpart_iban: str (nullable)
├── reference: str (nullable) — bank reference/concept number
│
├── deduplication_hash: str — hash of (bank_account_id, value_date, amount, description)
│
├── is_intercompany: bool (default false)
├── intercompany_match_id: UUID (nullable, FK → IntercompanyMatch)
│
├── created_at: datetime (UTC)
├── created_by: str
└── is_deleted: bool (soft delete)
```

**Notes:**
- `deduplication_hash` prevents re-importing the same movement if the file is re-uploaded
- Amount sign convention: positive = money arriving in account (inflow), negative = money leaving (outflow)
- This is the MOST CRITICAL model — any change requires full impact analysis

---

## Model: MovementClassification

```
MovementClassification
├── id: UUID (PK)
├── movement_id: UUID (FK → Movement)
├── category_code: str (FK → CategoryTaxonomy)
├── subcategory_code: str (nullable, FK → CategoryTaxonomy)
├── source: enum — RULE | MANUAL | AI_SUGGESTION
├── rule_id: UUID (nullable, FK → ClassificationRule)
├── confidence: float (nullable) — 0.0 to 1.0 for AI suggestions
├── is_confirmed: bool — true once human-confirmed
├── classified_by: str — user or "system"
├── classified_at: datetime (UTC)
├── override_reason: str (nullable) — for MANUAL source
└── previous_category_code: str (nullable) — for override audit trail
```

---

## Model: ClassificationRule

```
ClassificationRule
├── id: UUID (PK)
├── name: str — human label
├── priority: int — lower number = higher priority
├── is_active: bool
│
├── match_type: enum — KEYWORD | REGEX | COUNTERPART_NAME | AMOUNT_RANGE | COMPOSITE
├── match_field: str — which Movement field to match against
├── match_pattern: str — keyword, regex, or composite JSON
│
├── category_code: str (FK → CategoryTaxonomy)
├── subcategory_code: str (nullable)
│
├── created_by: str
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

---

## Model: CategoryTaxonomy

```
CategoryTaxonomy
├── code: str (PK) — e.g., "OCF", "OCF_REVENUE", "FCF_DEBT_REPAYMENT"
├── parent_code: str (nullable, FK → CategoryTaxonomy)
├── name: str — display label
├── description: str
├── cash_flow_section: enum — OPERATING | INVESTING | FINANCING | INTERNAL | UNCLASSIFIED
├── level: int — 1 = top-level, 2 = subcategory
└── is_active: bool
```

---

## Model: IntercompanyMatch

```
IntercompanyMatch
├── id: UUID (PK)
├── movement_out_id: UUID (FK → Movement) — the outflow leg
├── movement_in_id: UUID (FK → Movement) — the inflow leg
├── company_from_id: UUID (FK → Company)
├── company_to_id: UUID (FK → Company)
├── amount: NUMERIC(18,2) — matched amount (always positive)
├── match_date: date — date of the match event
├── status: enum — PROPOSED | CONFIRMED | REJECTED
├── match_method: enum — AUTOMATIC | MANUAL
├── confirmed_by: str (nullable)
├── confirmed_at: datetime (UTC, nullable)
├── rejection_reason: str (nullable)
├── created_at: datetime (UTC)
└── notes: str (nullable)
```

---

## Model: ForecastEntry

```
ForecastEntry
├── id: UUID (PK)
├── company_id: UUID (FK → Company)
├── scenario_id: UUID (FK → ForecastScenario)
├── week_start_date: date — Monday of the forecast week
├── category_code: str (FK → CategoryTaxonomy)
├── amount: NUMERIC(18,2) — signed (+ inflow, - outflow)
├── currency: str — "EUR"
├── source: enum — OFFICIAL | AI
├── confidence: float (nullable) — for AI source only
├── notes: str (nullable)
├── created_at: datetime (UTC)
└── created_by: str
```

**IMPORTANT:** ForecastEntry stores ONLY OFFICIAL and AI forecast entries. The ACTUALS layer in the 3-layer forecast view is NOT stored in this table — it is computed on-demand by aggregating Movement records from the Treasury Ledger (grouped by week and category). This means the ACTUALS layer is always up-to-date and never out of sync with the ledger. The `source` enum deliberately omits ACTUALS to enforce this separation.

---

## Model: ForecastScenario

```
ForecastScenario
├── id: UUID (PK)
├── name: str — e.g., "Budget 2026 Q2", "Revised May 2026"
├── description: str
├── source: enum — OFFICIAL | AI
├── week_start: date — first week of this scenario
├── week_end: date — last week of this scenario
├── is_active: bool — currently active scenario for display
├── import_batch_ref: str (nullable) — Excel upload reference
├── created_at: datetime (UTC)
└── created_by: str
```

---

## Model: DebtInstrument

```
DebtInstrument
├── id: UUID (PK)
├── company_id: UUID (FK → Company)
├── name: str — e.g., "Préstamo Bankia 2023"
├── instrument_type: enum — LOAN | CREDIT_LINE | BOND | LEASING | OTHER
├── lender_name: str
├── principal_amount: NUMERIC(18,2)
├── outstanding_balance: NUMERIC(18,2)
├── currency: str — "EUR"
├── drawdown_date: date
├── maturity_date: date
├── interest_type: enum — FIXED | VARIABLE | MIXED
├── interest_rate: NUMERIC(6,4) — annual rate
├── reference_rate: str (nullable) — e.g., "EURIBOR_12M"
├── spread: NUMERIC(6,4) (nullable)
├── amortization_type: enum — BULLET | FRENCH | GERMAN | CUSTOM
├── is_active: bool
├── notes: str (nullable)
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

---

## Model: DebtScheduleEntry

```
DebtScheduleEntry
├── id: UUID (PK)
├── debt_instrument_id: UUID (FK → DebtInstrument)
├── payment_date: date
├── payment_type: enum — PRINCIPAL | INTEREST | MIXED
├── amount: NUMERIC(18,2) — always positive
├── principal_component: NUMERIC(18,2, nullable)
├── interest_component: NUMERIC(18,2, nullable)
├── status: enum — SCHEDULED | PAID | OVERDUE | CANCELLED
├── movement_id: UUID (nullable, FK → Movement) — link to actual payment
├── created_at: datetime (UTC)
└── updated_at: datetime (UTC)
```

---

## Enum Reference

```
ImportBatch.status:       PENDING | PROCESSING | COMPLETED | FAILED | DUPLICATE
RawMovement.parse_status: OK | ERROR | SKIPPED
MovementClassification.source: RULE | MANUAL | AI_SUGGESTION
ClassificationRule.match_type: KEYWORD | REGEX | COUNTERPART_NAME | AMOUNT_RANGE | COMPOSITE
CategoryTaxonomy.cash_flow_section: OPERATING | INVESTING | FINANCING | INTERNAL | UNCLASSIFIED
IntercompanyMatch.status: IN_TRANSIT | PROPOSED | CONFIRMED | REJECTED | UNRESOLVED
IntercompanyMatch.match_method: AUTOMATIC | MANUAL
ForecastEntry.source:     OFFICIAL | AI
ForecastScenario.source:  OFFICIAL | AI
DebtInstrument.instrument_type: LOAN | CREDIT_LINE | BOND | LEASING | OTHER
DebtInstrument.interest_type:   FIXED | VARIABLE | MIXED
DebtInstrument.amortization_type: BULLET | FRENCH | GERMAN | CUSTOM
DebtScheduleEntry.payment_type:  PRINCIPAL | INTEREST | MIXED
DebtScheduleEntry.status:        SCHEDULED | PAID | OVERDUE | CANCELLED
```
