# Spec 04 — Database Design

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Database Technology

**PostgreSQL** (managed on Railway)

Rationale:
- Native JSON support for `raw_data` and `error_log` fields
- UUID generation via `gen_random_uuid()`
- Full ACID compliance for financial data
- Excellent SQLAlchemy support
- Railway's managed PostgreSQL is reliable and simple to operate

---

## 2. Schema Conventions

| Convention | Value |
|-----------|-------|
| Primary keys | UUID (not integer — prevents enumeration attacks) |
| Timestamps | `TIMESTAMP WITH TIME ZONE` stored as UTC |
| Amounts | `NUMERIC(18, 2)` — never FLOAT for money |
| Boolean fields | PostgreSQL `BOOLEAN`, never `SMALLINT` |
| Enum fields | PostgreSQL native `ENUM` type via SQLAlchemy |
| Soft deletes | `is_deleted BOOLEAN DEFAULT FALSE` on mutable entities |
| Audit fields | `created_at`, `created_by`, `updated_at`, `updated_by` on all tables |
| JSON fields | `JSONB` (binary JSON for indexing and query support) |
| Text | `TEXT` (no arbitrary `VARCHAR(n)` unless DB constraint needed) |

---

## 3. Table Definitions

### 3.1 companies

```sql
CREATE TABLE companies (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    short_name  TEXT NOT NULL,
    tax_id      TEXT UNIQUE,
    is_holding  BOOLEAN NOT NULL DEFAULT FALSE,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.2 bank_accounts

```sql
CREATE TABLE bank_accounts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id   UUID NOT NULL REFERENCES companies(id),
    bank_name    TEXT NOT NULL,
    account_name TEXT NOT NULL,
    iban         TEXT NOT NULL,
    currency     TEXT NOT NULL DEFAULT 'EUR',
    is_internal  BOOLEAN NOT NULL DEFAULT FALSE,
    is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (iban)
);

CREATE INDEX idx_bank_accounts_company ON bank_accounts(company_id);
CREATE INDEX idx_bank_accounts_internal ON bank_accounts(is_internal) WHERE is_internal = TRUE;
```

### 3.3 import_batches

```sql
CREATE TYPE import_status AS ENUM (
    'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'DUPLICATE'
);

CREATE TABLE import_batches (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id       UUID NOT NULL REFERENCES companies(id),
    bank_account_id  UUID NOT NULL REFERENCES bank_accounts(id),
    filename         TEXT NOT NULL,
    file_hash        TEXT NOT NULL,
    file_format      TEXT NOT NULL,
    status           import_status NOT NULL DEFAULT 'PENDING',
    row_count        INTEGER,
    imported_count   INTEGER DEFAULT 0,
    error_count      INTEGER DEFAULT 0,
    error_log        JSONB DEFAULT '[]',
    imported_by      TEXT NOT NULL,
    imported_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at     TIMESTAMPTZ,
    notes            TEXT,
    UNIQUE (file_hash)
);

CREATE INDEX idx_import_batches_company ON import_batches(company_id);
CREATE INDEX idx_import_batches_account ON import_batches(bank_account_id);
CREATE INDEX idx_import_batches_status ON import_batches(status);
```

### 3.4 raw_movements

```sql
CREATE TYPE parse_status AS ENUM ('OK', 'ERROR', 'SKIPPED');

CREATE TABLE raw_movements (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    import_batch_id      UUID NOT NULL REFERENCES import_batches(id),
    row_number           INTEGER NOT NULL,
    raw_data             JSONB NOT NULL,
    normalized_date      DATE,
    normalized_amount    NUMERIC(18, 2),
    normalized_description TEXT,
    parse_status         parse_status NOT NULL DEFAULT 'OK',
    parse_error          TEXT,
    movement_id          UUID  -- FK to movements added after table creation
);

CREATE INDEX idx_raw_movements_batch ON raw_movements(import_batch_id);
CREATE INDEX idx_raw_movements_movement ON raw_movements(movement_id) WHERE movement_id IS NOT NULL;
```

### 3.5 movements

```sql
CREATE TABLE movements (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id           UUID NOT NULL REFERENCES companies(id),
    bank_account_id      UUID NOT NULL REFERENCES bank_accounts(id),
    import_batch_id      UUID NOT NULL REFERENCES import_batches(id),
    raw_movement_id      UUID REFERENCES raw_movements(id),

    value_date           DATE NOT NULL,
    accounting_date      DATE,

    amount               NUMERIC(18, 2) NOT NULL,
    currency             TEXT NOT NULL DEFAULT 'EUR',
    balance_after        NUMERIC(18, 2),

    description          TEXT NOT NULL DEFAULT '',
    counterpart_name     TEXT,
    counterpart_iban     TEXT,
    reference            TEXT,

    deduplication_hash   TEXT NOT NULL,

    is_intercompany      BOOLEAN NOT NULL DEFAULT FALSE,
    intercompany_match_id UUID,  -- FK added after intercompany_matches table

    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by           TEXT NOT NULL DEFAULT 'system',
    is_deleted           BOOLEAN NOT NULL DEFAULT FALSE,

    UNIQUE (deduplication_hash)
);

CREATE INDEX idx_movements_company ON movements(company_id);
CREATE INDEX idx_movements_account ON movements(bank_account_id);
CREATE INDEX idx_movements_value_date ON movements(value_date);
CREATE INDEX idx_movements_amount ON movements(amount);
CREATE INDEX idx_movements_intercompany ON movements(is_intercompany) WHERE is_intercompany = TRUE;
CREATE INDEX idx_movements_not_deleted ON movements(is_deleted) WHERE is_deleted = FALSE;
```

### 3.6 category_taxonomy

```sql
CREATE TYPE cash_flow_section AS ENUM (
    'OPERATING', 'INVESTING', 'FINANCING', 'INTERNAL', 'UNCLASSIFIED'
);

CREATE TABLE category_taxonomy (
    code              TEXT PRIMARY KEY,
    parent_code       TEXT REFERENCES category_taxonomy(code),
    name              TEXT NOT NULL,
    description       TEXT NOT NULL DEFAULT '',
    cash_flow_section cash_flow_section NOT NULL,
    level             INTEGER NOT NULL DEFAULT 1,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE
);
```

### 3.7 classification_rules

```sql
CREATE TYPE match_type AS ENUM (
    'KEYWORD', 'REGEX', 'COUNTERPART_NAME', 'AMOUNT_RANGE', 'COMPOSITE'
);

CREATE TABLE classification_rules (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    priority      INTEGER NOT NULL DEFAULT 100,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    match_type    match_type NOT NULL,
    match_field   TEXT NOT NULL,
    match_pattern TEXT NOT NULL,
    category_code TEXT NOT NULL REFERENCES category_taxonomy(code),
    subcategory_code TEXT REFERENCES category_taxonomy(code),
    created_by    TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_classification_rules_priority ON classification_rules(priority) WHERE is_active = TRUE;
```

### 3.8 movement_classifications

```sql
CREATE TYPE classification_source AS ENUM ('RULE', 'MANUAL', 'AI_SUGGESTION');

CREATE TABLE movement_classifications (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movement_id      UUID NOT NULL REFERENCES movements(id),
    category_code    TEXT NOT NULL REFERENCES category_taxonomy(code),
    subcategory_code TEXT REFERENCES category_taxonomy(code),
    source           classification_source NOT NULL,
    rule_id          UUID REFERENCES classification_rules(id),
    confidence       NUMERIC(4, 3),  -- 1.000 for rules; 0.000-1.000 for AI suggestions only
    is_confirmed     BOOLEAN NOT NULL DEFAULT FALSE,
    classified_by    TEXT NOT NULL DEFAULT 'system',
    classified_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    override_reason  TEXT,
    previous_category_code TEXT,
    UNIQUE (movement_id)  -- one active classification per movement; overrides REPLACE (UPDATE) existing row
);

-- Override mechanism: when a manual override is applied, the existing row is UPDATED in place.
-- The UNIQUE constraint on movement_id ensures there is always exactly one classification per movement.
-- The previous_category_code and override_reason fields provide the audit trail.
-- Row is never deleted — only updated. This preserves the full override history in the row itself.

CREATE INDEX idx_movement_classifications_category ON movement_classifications(category_code);
```

### 3.9 intercompany_matches

```sql
CREATE TYPE match_status AS ENUM ('PROPOSED', 'CONFIRMED', 'REJECTED');
CREATE TYPE match_method AS ENUM ('AUTOMATIC', 'MANUAL');

CREATE TABLE intercompany_matches (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movement_out_id  UUID NOT NULL REFERENCES movements(id),
    movement_in_id   UUID NOT NULL REFERENCES movements(id),
    company_from_id  UUID NOT NULL REFERENCES companies(id),
    company_to_id    UUID NOT NULL REFERENCES companies(id),
    amount           NUMERIC(18, 2) NOT NULL,
    match_date       DATE NOT NULL,
    status           match_status NOT NULL DEFAULT 'PROPOSED',
    match_method     match_method NOT NULL,
    confirmed_by     TEXT,
    confirmed_at     TIMESTAMPTZ,
    rejection_reason TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes            TEXT,
    UNIQUE (movement_out_id),
    UNIQUE (movement_in_id)
);
```

### 3.10 forecast_scenarios

```sql
CREATE TYPE forecast_source AS ENUM ('OFFICIAL', 'AI');

CREATE TABLE forecast_scenarios (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             TEXT NOT NULL,
    description      TEXT NOT NULL DEFAULT '',
    source           forecast_source NOT NULL,
    week_start       DATE NOT NULL,
    week_end         DATE NOT NULL,
    is_active        BOOLEAN NOT NULL DEFAULT FALSE,
    import_batch_ref TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by       TEXT NOT NULL
);
```

### 3.11 forecast_entries

```sql
CREATE TABLE forecast_entries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id      UUID NOT NULL REFERENCES companies(id),
    scenario_id     UUID NOT NULL REFERENCES forecast_scenarios(id),
    week_start_date DATE NOT NULL,
    category_code   TEXT NOT NULL REFERENCES category_taxonomy(code),
    amount          NUMERIC(18, 2) NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'EUR',
    source          forecast_source NOT NULL,
    confidence      NUMERIC(4, 3),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      TEXT NOT NULL
);

CREATE INDEX idx_forecast_entries_company ON forecast_entries(company_id);
CREATE INDEX idx_forecast_entries_scenario ON forecast_entries(scenario_id);
CREATE INDEX idx_forecast_entries_week ON forecast_entries(week_start_date);
```

### 3.12 debt_instruments

```sql
CREATE TYPE instrument_type AS ENUM ('LOAN', 'CREDIT_LINE', 'BOND', 'LEASING', 'OTHER');
CREATE TYPE interest_type AS ENUM ('FIXED', 'VARIABLE', 'MIXED');
CREATE TYPE amortization_type AS ENUM ('BULLET', 'FRENCH', 'GERMAN', 'CUSTOM');

CREATE TABLE debt_instruments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID NOT NULL REFERENCES companies(id),
    name                TEXT NOT NULL,
    instrument_type     instrument_type NOT NULL,
    lender_name         TEXT NOT NULL,
    principal_amount    NUMERIC(18, 2) NOT NULL,
    outstanding_balance NUMERIC(18, 2) NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'EUR',
    drawdown_date       DATE NOT NULL,
    maturity_date       DATE NOT NULL,
    interest_type       interest_type NOT NULL,
    interest_rate       NUMERIC(6, 4),
    reference_rate      TEXT,
    spread              NUMERIC(6, 4),
    amortization_type   amortization_type NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_debt_instruments_company ON debt_instruments(company_id);
CREATE INDEX idx_debt_instruments_maturity ON debt_instruments(maturity_date) WHERE is_active = TRUE;
```

### 3.13 debt_schedule_entries

```sql
CREATE TYPE payment_type AS ENUM ('PRINCIPAL', 'INTEREST', 'MIXED');
CREATE TYPE schedule_status AS ENUM ('SCHEDULED', 'PAID', 'OVERDUE', 'CANCELLED');

CREATE TABLE debt_schedule_entries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debt_instrument_id  UUID NOT NULL REFERENCES debt_instruments(id),
    payment_date        DATE NOT NULL,
    payment_type        payment_type NOT NULL,
    amount              NUMERIC(18, 2) NOT NULL,
    principal_component NUMERIC(18, 2),
    interest_component  NUMERIC(18, 2),
    status              schedule_status NOT NULL DEFAULT 'SCHEDULED',
    movement_id         UUID REFERENCES movements(id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_debt_schedule_instrument ON debt_schedule_entries(debt_instrument_id);
CREATE INDEX idx_debt_schedule_payment_date ON debt_schedule_entries(payment_date);
CREATE INDEX idx_debt_schedule_status ON debt_schedule_entries(status);
```

---

## 4. Alembic Migration Strategy

- All schema changes via Alembic migrations — no manual SQL in production
- Migration files named: `YYYY_MM_DD_HHMMSS_description.py`
- Each migration is reversible (downgrade function always implemented)
- No data migrations in DDL migrations (separate data migration scripts in `/scripts`)
- Baseline migration: initial schema from this spec

---

## 5. Indexing Strategy

Primary indexes:
- All foreign keys indexed
- All date columns used in range queries indexed
- `deduplication_hash` unique index (core deduplication mechanism)
- Partial indexes on `is_active`, `is_deleted` flag columns

Future indexes (add when query patterns are known):
- Composite index on `(company_id, value_date)` for ledger queries
- Composite index on `(scenario_id, week_start_date)` for forecast queries

---

## 6. Performance Considerations

- `movements` table will be the largest; consider table partitioning by `value_date` if volume exceeds 1M rows
- `raw_movements.raw_data` is JSONB — do not query on nested JSON fields in hot paths
- Aggregate queries for dashboard should use materialized views or in-application caching in Phase 2
