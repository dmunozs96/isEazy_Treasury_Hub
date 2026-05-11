# Spec 16 — Bank Format Normalization Mappings

**Version:** 1.1  
**Date:** 2026-05-11  
**Status:** CONFIRMED — user sign-off 2026-05-11  
**Session:** Bank Format Analysis (session 3) + user confirmation  
**Blocks:** Milestone 1.2 (Bank Import Engine), parser implementation

---

## User Confirmation Log (2026-05-11)

| Question | Answer |
|----------|--------|
| P1 — Deutsche Bank entity | **SKILLS** (`ES72 0019 0032 59 4010073742` = Iseazy Skills, S.L.) |
| P2 — Cajamar newline split | Implementation detail — no user decision needed; parser handles internally |
| P3 — Santander LMS 3917 multi-sheet | **Yes — parse ALL monthly sheets and merge** (team manually split into tabs from working papers) |
| P4 — Bankinter IMPORTE vs DEBE/HABER | **Confirmed — use `IMPORTE` as authoritative signed amount** |
| P5 — 4 banks with no VLOOKUP rules | **User requested AI-drafted rules** based on observed transaction patterns — see Section 4.5 |
| P6 — Overall mappings | **Confirmed correct** |

---

## 1. Overview

This document captures the raw column structure of all 12 banks' statement exports, the normalization mapping from each bank's raw columns to the canonical `Movement` model fields, and all format quirks that parsers must handle.

**Canonical `Movement` fields targeted:**
| Field | Type | Notes |
|-------|------|-------|
| `booking_date` | date | When the bank posted the transaction |
| `value_date` | date | Settlement / interest date |
| `description` | str | Primary description text |
| `description_detail` | str (nullable) | Secondary description or counterpart info |
| `counterpart_name` | str (nullable) | Payer or payee name |
| `amount` | Decimal | Signed EUR; negative = outflow, positive = inflow |
| `running_balance` | Decimal | Account balance after movement |
| `operation_code` | str (nullable) | Bank-internal operation type code |
| `reference` | str (nullable) | Payment reference, IBAN, or document number |

---

## 2. Per-Bank Format Analysis

### 2.1 Abanca

**Files:** 1 × `.xlsx`  
**Engine:** `openpyxl`  
**Header row:** 4 (0-indexed) — 4 metadata rows above  
**Columns:** 9  
**Amount convention:** Signed single `IMPORTE` column  
**Date format:** `YYYY-MM-DD` (parsed by pandas as date objects)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `F. VALOR` | `value_date` | |
| `F. CONTABLE` | `booking_date` | |
| `F. OPERACIÓN` | *(skip)* | Redundant with booking_date in practice |
| `TIPO OPERACIÓN` | `operation_code` | Abanca internal type string (e.g. `OPERS PRESTAMOS`, `COMIS.MANTENIM.`) |
| `DESCRIPCIÓN` | `description` | |
| `REFERENCIA` | `reference` | Often NaN |
| `IMPORTE` | `amount` | Signed float, EUR |
| `SALDO` | `running_balance` | |
| `DIVISA` | *(skip)* | Always `EUR` |

**Quirks:**
- Column names have encoding issues when read with xlrd (`OPERACI?N`) — use `openpyxl` engine only
- `F. OPERACIÓN` and `F. CONTABLE` differ by at most 1 day (settlement lag); use `F. CONTABLE` as `booking_date`
- `REFERENCIA` is NaN for all observed rows; map to `reference` but expect nulls

---

### 2.2 BBVA

**Files:** 6 × `.xlsx`  
**Engine:** `openpyxl`  
**Header row:** 15 (0-indexed) — large metadata block rows 0–14  
**Data starts:** row 16  
**Columns:** 11 (data section; columns C–M in spreadsheet; leading empty columns A–B)  
**Amount convention:** Signed single `IMPORTE` column  
**Date format:** `DD/MM/YYYY` strings

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `F. OPERACIÓN` | `booking_date` | Parse `DD/MM/YYYY` |
| `F. VALOR` | `value_date` | Parse `DD/MM/YYYY` |
| `CÓDIGO` | `operation_code` | 5-digit string (e.g. `00181`, `00007`, `00313`) |
| `CONCEPTO` | `description` | Operation type label |
| `BENEFICIARIO/ORDENANTE` | `counterpart_name` | Payer or payee name (often same as account entity for IC) |
| `OBSERVACIONES` | `description_detail` | Free-text remittance info or IBAN reference |
| `IMPORTE` | `amount` | Signed float |
| `SALDO` | `running_balance` | |
| `DIVISA` | *(skip)* | Always `EUR` |
| `OFICINA` | *(skip)* | Branch code — not needed |
| `REMESA` | `reference` | IBAN-format reference string |

**Metadata available in rows 0–14 (extract at parse time):**
- Row 6 col 5: Account holder name (`Titular`)
- Row 7 col 5: IBAN (`Cuenta`)
- Row 12 col 5: Period string (e.g. `01/01/2025-31/01/2025`)

**Quirks:**
- Data columns start at spreadsheet column C (index 2), not column A — use `usecols` or shift
- Rows after last data row may be blank — drop rows where `F. OPERACIÓN` is NaN
- All 6 BBVA files have identical structure; IBAN in row 7 col 5 is the per-file account identifier

---

### 2.3 Banca March

**Files:** 6 × `.xlsx`  
**Engine:** `openpyxl`  
**Header row:** 3 (0-indexed)  
**Columns:** 7  
**Amount convention:** Signed single `Importe` column  
**Date format:** Mixed (see quirks below)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `F. operación` | `booking_date` | `DD/MM/YYYY` string |
| `F. valor` | `value_date` | Mixed format — see quirks |
| `Oficina` | *(skip)* | Branch code integer |
| `Concepto` | `description` | |
| `Concepto ordenante` | `description_detail` | Counterpart's remittance info (nullable) |
| `Importe` | `amount` | Signed; integer or float |
| `Saldo` | `running_balance` | |

**Quirks:**
- `F. valor` has inconsistent format: some rows are full datetime objects (pandas parses dates with year), other rows show only `DD/MM` (short format, year omitted) — treat short-format values as same year as `F. operación`
- `Concepto ordenante` is NaN for internal account charges (e.g. `LIQUID.PROPIA CUENTA`)
- `Importe` may be integer (e.g. `11000`) or float — always cast to `Decimal`

---

### 2.4 Bankinter

**Files:** 7 × `.xlsx`  
**Engine:** `openpyxl`  
**Header row:** 5 (0-indexed)  
**Columns:** 10 or 11 (REF. 16 column present in some files)  
**Amount convention:** Three columns — `DEBE` (debits, negative), `HABER` (credits, positive), `IMPORTE` (signed redundant sum)  
**Date format:** `YYYY-MM-DD` (pandas date objects)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `FECHA CONTABLE` | `booking_date` | |
| `FECHA VALOR` | `value_date` | |
| `CLAVE` | `operation_code` | Mixed alphanumeric (e.g. `T50`, `100`, `108`, `C59`, `278`, `218`, `276`) |
| `REFERENCIA` | `reference` | Internal sequential reference number |
| `CATEGORÍA` | *(skip or note)* | Bankinter's own category — do not use for canonical classification |
| `DESCRIPCIÓN` | `description` | |
| `REF. 16` | `description_detail` | SEPA remittance reference (column absent in some files — handle missing column) |
| `DEBE` | *(component)* | Debit amount as negative float, 0 when credit |
| `HABER` | *(component)* | Credit amount as positive float, 0 when debit |
| `IMPORTE` | `amount` | Signed float (= HABER − abs(DEBE)); use this directly |
| `SALDO` | `running_balance` | |

**Quirks:**
- Column `REF. 16` is absent in 2 of 7 files — parser must check column presence before reading
- `DEBE` values are negative floats (not positive debits with separate sign) — `IMPORTE` is the reliable field
- `FECHA VALOR` for one file (Factory 2602) has NaT for some rows (empty accounts)  
- Trailing rows after data contain footer text ("INFORMACIÓN DE INTERÉS") — drop rows where `FECHA CONTABLE` is NaT

---

### 2.5 CaixaBank

**Files:** 11 × `.xls`  
**Engine:** `xlrd`  
**Header row:** 2 (0-indexed)  
**Columns:** 6  
**Amount convention:** Signed single `Importe` column  
**Date format:** `YYYY-MM-DD` (pandas date objects via xlrd)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `Fecha` | `booking_date` | |
| `Fecha valor` | `value_date` | |
| `Movimiento` | `description` | Operation type keyword |
| `Más datos` | `description_detail` | Counterpart info (format: `NNNNNN-NAME` where NNNNNN = partial account ref); nullable |
| `Importe` | `amount` | Signed float |
| `Saldo` | `running_balance` | |

**Quirks:**
- One file (`CAIXA LMS 5705`) contains only the text `SIN MOVIMIENTOS` — detect at parse time (shape `(0, 1)`) and produce zero-row result without error
- `Más datos` format varies: sometimes `00000000-NOMBRE` (account+name), sometimes just a reference code, sometimes NaN
- Rows 0–1 above header contain account metadata — skip

---

### 2.6 Cajamar

**Files:** 1 × `.xls`  
**Engine:** `calamine` (xlrd fails — corrupted SST table in compound binary)  
**Header row:** 0 (0-indexed) — data starts immediately  
**Columns:** 5  
**Amount convention:** Signed single `Importe` column  
**Date format:** `YYYY-MM-DD` datetime objects

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `Fecha` | `booking_date` | datetime — truncate to date |
| `F. valor` | `value_date` | datetime — truncate to date |
| `Concepto` | `description` + `description_detail` | Split on first `\n` — see quirks |
| `Importe` | `amount` | Signed float |
| `Saldo` | `running_balance` | |

**Quirks:**
- `Concepto` field contains embedded newlines (`\n`). Split on first `\n`:
  - Part before `\n` → `description` (operation type, e.g. `INTERESES DE PRESTAMO`)
  - Part after `\n` → `description_detail` (reference/details, e.g. `PTMO.:000190616490225649`)
- File uses `calamine` engine specifically — do not attempt `xlrd` or `openpyxl`

---

### 2.7 Deutsche Bank

**Files:** 1 × `.xls`  
**Engine:** `xlrd`  
**Header row:** 5 (0-indexed)  
**Data starts:** row 6  
**Columns:** 6 (6th column always empty — skip)  
**Amount convention:** Signed `IMPORTE` column — **string with European number format**  
**Date format:** `DD.MM.YYYY` strings (dot-separated, not slash)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `FECHA OPERACIÓN` | `booking_date` | Parse `DD.MM.YYYY` |
| `FECHA VALOR` | `value_date` | Parse `DD.MM.YYYY` |
| `CONCEPTO` | `description` | Right-padded with spaces — always `.strip()` |
| `IMPORTE` | `amount` | String, European format — see quirks |
| `SALDO` | `running_balance` | String, European format — see quirks |
| *(col 5 empty)* | *(skip)* | |

**Metadata in rows 0–3:**
- Row 1 col 1: IBAN (`ES72 0019...`)
- Row 2: date range
- Row 3: current balance, reserved balance, available balance

**Quirks:**
- `IMPORTE` and `SALDO` are **strings** with European number format: `.` = thousands separator, `,` = decimal. Parse: `s.replace('.', '').replace(',', '.')` → `Decimal`
- `CONCEPTO` is fixed-width padded — always strip
- Date format uses dots: `27.12.2025` → parse as `%d.%m.%Y`
- Only 1 file — entity confirmed as **SKILLS** (Iseazy Skills, S.L.) — IBAN `ES72 0019 0032 59 4010073742`

---

### 2.8 Eurocaja Rural

**Files:** 1 × `.csv`  
**Encoding:** `utf-8-sig` (BOM-prefixed UTF-8)  
**Separator:** `;` (semicolon)  
**Header row:** 8 (0-indexed) — metadata block rows 0–7  
**Amount convention:** Signed `Importe` column — **string with EUR symbol and European format**  
**Date format:** `DD/MM/YYYY HH:MM` (Fecha de ejecución), `DD/MM/YYYY` (Fecha valor)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `Fecha de ejecución` | `booking_date` | Parse `DD/MM/YYYY HH:MM` — truncate time |
| `Fecha valor` | `value_date` | Parse `DD/MM/YYYY` |
| `Descripción` | `description` | |
| `Importe` | `amount` | String with € symbol — see quirks |
| `Saldo` | `running_balance` | String with € symbol — see quirks |

**Metadata in rows 0–7 (for IBAN extraction):**
- Row 2 col 1: full IBAN (`ES45 3081 0297 9150 0073 9601 - CUENTA EMPRESAREA`)
- Row 3: date from, Row 4: date to

**Quirks:**
- `Importe` format example: `"-38.000,00 €"` — parse: strip `€` and whitespace, then European number conversion
- Amounts appear with the currency symbol and a non-breaking space — use `str.strip().rstrip('€').strip().replace('.', '').replace(',', '.')`
- Rows 0–7 are metadata — skip by using `skiprows=8` and `header=0`
- Only 1 file (SKILLS entity, full year 2025)

---

### 2.9 Ibercaja

**Files:** 6 × `.xlsx`  
**Engine:** `openpyxl`  
**Header row:** 6 (0-indexed)  
**Columns:** 8  
**Amount convention:** Signed single `Importe` column  
**Date format:** `DD-MM-YYYY` strings (hyphen-separated — unique among all banks)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `Nº Orden` | *(skip)* | Sequential row counter within file, not stable |
| `Fecha Oper` | `booking_date` | Parse `DD-MM-YYYY` (hyphens, not slashes) |
| `Fecha Valor` | `value_date` | Parse `DD-MM-YYYY` |
| `Concepto` | `operation_code` | Ibercaja type string (e.g. `TRANSFERENCIA OTRA ENTIDAD`, `NOMINA`, `TRANSFERENCIA INTERNA`) |
| `Descripción` | `description` | Free text including counterpart name and reference |
| `Referencia` | `reference` | Float (12-digit account ref read as float) or NaN — cast to string, strip `.0` |
| `Importe` | `amount` | Signed float |
| `Saldo` | `running_balance` | |

**Quirks:**
- Date separator is `-` not `/` — use `strptime('%d-%m-%Y')` specifically
- `Referencia` parsed as float (e.g. `6.503116e+11`) — convert: `str(int(value))` when not NaN
- `Descripción` often contains counterpart name — consider extracting for `counterpart_name` via pattern matching
- `Concepto = "TRANSFERENCIA INTERNA"` identifies intercompany transfers
- `Concepto = "NOMINA"` identifies payroll (referenced in VLOOKUP rules)

---

### 2.10 Ruralvia

**Files:** 1 × `.xlsx`  
**Engine:** `openpyxl`  
**Header row:** 3 (0-indexed)  
**Rows 0–1:** Account metadata (Nombre, IBAN)  
**Columns:** 6  
**Amount convention:** Signed single `Importe` column  
**Date format:** `datetime` objects with time `HH:59:16` (always same — truncate)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `Fecha de la operación` | `booking_date` | datetime → `.date()` |
| `Fecha valor` | `value_date` | datetime → `.date()` |
| `Tipo movimiento` | `description` | Concatenated without separator — see quirks |
| `Importe` | `amount` | Signed float |
| `Saldo` | `running_balance` | |
| `Nro. Apunte` | *(skip)* | Sequential counter |

**Metadata in rows 0–1:**
- Row 0 col 1: Entity name (e.g. `Iseazy Skills, S.L.`)
- Row 1 col 1: IBAN (`ES83 3187 0876 1360 4276 1921`)

**Quirks:**
- `Tipo movimiento` has no separator between type and reference: `rcbo. préstamo6042762754` → description is the full string as-is; no reliable split
- All datetime objects include time component (`00:59:16`) — always call `.date()` or `.normalize()`
- Only 1 file (SKILLS entity, full year 2025 — labeled "completo")

---

### 2.11 Sabadell

**Files:** 3 × `.xls`  
**Engine:** `calamine` (xlrd fails — corrupted SST table)  
**Header row:** 7 (0-indexed) — metadata block rows 0–5, blank row 6  
**Columns:** 7  
**Amount convention:** Signed single `Importe` column  
**Date format:** `DD/MM/YYYY` strings

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `F. Operativa` | `booking_date` | Parse `DD/MM/YYYY` |
| `Concepto` | `description` | Free text |
| `F. Valor` | `value_date` | Parse `DD/MM/YYYY` |
| `Importe` | `amount` | Signed float |
| `Saldo` | `running_balance` | |
| `Referencia 1` | `reference` | Often NaN |
| `Referencia 2` | `description_detail` | Sometimes counterpart name (e.g. `VOLKSWAGEN INTER`) |

**Metadata in rows 0–5:**
- Row 3 col 1: Account number (format `0081-XXXX-XX-XXXXXXXXXX`)
- Row 4 col 1: Currency
- Row 5 col 1: Entity name (e.g. `ISEAZY FACTORY, S.L.`)

**Quirks:**
- Must use `calamine` engine — xlrd will raise `AssertionError` on SST table
- Column order: `F. Operativa`, `Concepto`, `F. Valor`, `Importe`, `Saldo`, `Referencia 1`, `Referencia 2` (NOT `F. Operativa`, `F. Valor`, ... — note `Concepto` is column B)

---

### 2.12 Santander

**Files:** 15 × `.xlsx`, 1 × `.xls` (multi-sheet)  
**Engine:** `openpyxl` (`.xlsx`), `xlrd` (`.xls`)  
**Header row:** 7 (0-indexed) for standard `.xlsx` files  
**Columns:** 12  
**Amount convention:** Signed single `Importe` column  
**Date format:** `DD/MM/YYYY` strings (Title Case in `Concepto` — dates appear in description text only)

| Raw column | → Canonical field | Notes |
|------------|-------------------|-------|
| `Fecha Operación` | `booking_date` | Parse `DD/MM/YYYY` |
| `Fecha Valor` | `value_date` | Parse `DD/MM/YYYY` |
| `Concepto` | `description` | Rich free text (Title Case, often includes counterpart name) |
| `Importe` | `amount` | Signed float |
| `Divisa` | *(skip)* | Always `EUR` |
| `Saldo` | `running_balance` | |
| `Divisa.1` | *(skip)* | Duplicate of `Divisa` |
| `Código` | `operation_code` | Numeric string: 71=inbound transfer, 72=outbound transfer/traspaso, 70=loan, 100=contract liquidation, 174=direct debit, 2=commission |
| `Número de documento` | `reference` | Often NaN; may be float or 13-digit number |
| `Referencia 1` | `description_detail` | Remittance ref (e.g. invoice number); often NaN |
| `Referencia 2` | *(skip)* | Often NaN |
| `Información adicional` | *(skip)* | Almost always NaN |

**Special case — `Santander_Santander LMS 3917.xls`:**
- Multi-sheet workbook
- Sheet `Hoja1` = operation code lookup table — skip
- Monthly sheets: `ENERO-FEBRERO`, `MARZO - ABRIL`, `MAYO`, ... `DICIEMBRE`
- Each monthly sheet has header at row **7** (same 12-column format) EXCEPT sheet `MARZO - ABRIL` which has header at **row 0**
- Some sheets contain `NO HAY MOVIMIENTOS` — handle as empty
- Parser must iterate all sheets, detect header row dynamically, concat results

**Metadata in rows 0–6 (standard files):**
- Row 1 col 2 area: `Titular` / `Saldo disponible` / `Saldo real`
- Row 4 col 2: IBAN
- Row 6: Date range string

**Quirks:**
- `Concepto` is Title Case (e.g. `Transferencia De Iseazy Factory Sl, Concepto Pago...`) — normalize to upper for keyword matching
- `Número de documento` is sometimes a float (13-digit number as float) — convert to string `str(int(value))`
- Drop rows where `Fecha Operación` is NaN (footer rows)

---

## 3. Cross-Bank Normalization Summary

| Bank | Format | Engine | Header Row | Date Format | Amount Format | Has Counterpart | Quirk severity |
|------|--------|--------|-----------|-------------|---------------|-----------------|----------------|
| Abanca | xlsx | openpyxl | 4 | YYYY-MM-DD | signed float | No | Low |
| BBVA | xlsx | openpyxl | 15 | DD/MM/YYYY | signed float | Yes | Medium (deep header) |
| Banca March | xlsx | openpyxl | 3 | DD/MM/YYYY | signed float | Partial | Medium (mixed date) |
| Bankinter | xlsx | openpyxl | 5 | YYYY-MM-DD | signed float | No | Medium (variable cols) |
| CaixaBank | xls | xlrd | 2 | YYYY-MM-DD | signed float | Partial | Low (empty file) |
| Cajamar | xls | calamine | 0 | YYYY-MM-DD | signed float | No | High (newlines in field) |
| Deutsche Bank | xls | xlrd | 5 | DD.MM.YYYY | **string (EU)** | No | High (string amounts) |
| Eurocaja Rural | csv | pandas | 8 | DD/MM/YYYY HH:MM | **string (EU+€)** | No | High (string amounts+€) |
| Ibercaja | xlsx | openpyxl | 6 | DD-MM-YYYY | signed float | Partial | Medium (hyphen dates) |
| Ruralvia | xlsx | openpyxl | 3 | datetime | signed float | No | Low (truncate time) |
| Sabadell | xls | calamine | 7 | DD/MM/YYYY | signed float | Partial | Medium (calamine only) |
| Santander | xlsx/xls | openpyxl/xlrd | 7 | DD/MM/YYYY | signed float | No | High (multi-sheet xls) |

---

## 4. VLOOKUP Classification Rules Analysis

**Source file:** `VLOOKUP_Best-try_Bank-Stataments.xlsb`  
**Engine:** `calamine`  
**Relevant sheet:** `Mapping` (410 rows including header)

### 4.1 Mapping Structure

The `Mapping` sheet has columns: `Banco`, `Descripción 1`, `Concat` (= Banco + `-` + Descripción), `[classification]`

The classification key is the value in column 4 (0-indexed). The mapping key used is `BANK_NAME + "-" + RAW_DESCRIPTION`.

### 4.2 CFO Category → Canonical Taxonomy Mapping

| VLOOKUP Category | → Canonical Code | Notes |
|------------------|------------------|-------|
| `Préstamos` | `FCF_LOAN_REPAYMENT` (outflow) / `FCF_LOAN_DRAWDOWN` (inflow) | Distinguish by sign |
| `Comisiones bancarias` | `FCF_BANK_FEES` | |
| `Transferencia Intercompañía` | `INT_INTERCOMPANY` (domestic) / `INT_INTERCOMPANY_FOREIGN` (foreign) | Distinguish by counterpart entity |
| `Cobro de clientes` | `OCF_INCOME` | Inbound only |
| `Pago de nóminas` | `OCF_PAYROLL` | |
| `Pago de impuestos` | `OCF_TAX` | |
| `Impuestos` | `OCF_TAX` | Same as above (two labels in VLOOKUP) |
| `Cuotas Seguridad Social` | `OCF_SOCIAL_SECURITY` | |
| `Pago a proveedores` | `OCF_PAYMENTS` | |
| `Inversiones financieras` | `FCF_DEPOSIT_ISSUED` (outflow) / `FCF_DEPOSIT_RETURN` (inflow) | Distinguish by sign |

### 4.3 Rules Count by Bank

| Bank | Rule count (approx) |
|------|-------------------|
| Abanca | 7 |
| Banca March | ~15 |
| Bankinter | ~10 |
| BBVA | ~20 |
| CaixaBank | ~15 |
| Cajamar | ~5 |
| Ibercaja | ~10 |
| Santander | ~15 |
| Deutsche Bank | 0 (not in VLOOKUP — needs rules from scratch) |
| Eurocaja Rural | 0 (not in VLOOKUP — needs rules from scratch) |
| Ruralvia | 0 (not in VLOOKUP — needs rules from scratch) |
| Sabadell | 0 (not in VLOOKUP — needs rules from scratch) |

**Note:** Deutsche Bank, Eurocaja Rural, Ruralvia, and Sabadell have zero VLOOKUP rules. Their transactions will classify as `UNCLASSIFIED` on first import. Rules must be added manually after first import.

### 4.4 Known Rule Gaps in VLOOKUP

- Missing rules for 4 banks (Deutsche Bank, Eurocaja Rural, Ruralvia, Sabadell) — drafted in Section 4.5 below
- Missing intercompany rules for foreign entities (Belgium, Colombia, Mexico, Puerto Rico) — blocked on G6
- VLOOKUP rules match on `Descripción 1` (primary description) only — secondary fields not used in rules

---

### 4.5 Drafted Classification Rules — 4 Banks Without VLOOKUP Coverage

These rules were drafted by AI based on the actual transaction data observed in the sample files. They follow the same keyword-match logic as the VLOOKUP sheet. **CFO should review and correct after the first import reveals UNCLASSIFIED items.**

All rules use case-insensitive substring matching on the `description` field. Sign-dependent rules apply only when `amount < 0` (outflow) or `amount > 0` (inflow) as noted.

#### Deutsche Bank (entity: SKILLS)

| Keyword pattern | Condition | → Canonical code | Rationale |
|----------------|-----------|-----------------|-----------|
| `RECIBO PRESTAMO` | any | `FCF_LOAN_REPAYMENT` | Monthly loan repayment (observed: `RECIBO PRESTAMO 027-30471457`) |
| `LIQUIDACIÓN CUENTA` | any | `FCF_BANK_FEES` | Account fee / liquidation charge |
| `COMISION BANCA ONLINE` | any | `FCF_BANK_FEES` | Online banking fee |
| `TRF` + isEazy entity name¹ | inflow | `INT_INTERCOMPANY` | Intercompany incoming (e.g. `TRF ISEAZY SKILLS SL`) |
| `TRF INM` + isEazy entity name¹ | inflow | `INT_INTERCOMPANY` | Immediate intercompany transfer |
| `TRF` (no isEazy entity) | inflow | `OCF_INCOME` | Customer/external receipt |
| `TRF` (no isEazy entity) | outflow | `OCF_PAYMENTS` | Outbound supplier payment |

¹ isEazy entity names to match: `BIZPILLS`, `BPO`, `ISEAZY`, `LMS`, `ENGAGE`, `FACTORY`, `SKILLS`, `AUTHOR`

#### Eurocaja Rural (entity: SKILLS)

| Keyword pattern | Condition | → Canonical code | Rationale |
|----------------|-----------|-----------------|-----------|
| `TRANS INMEDIATA` + isEazy entity¹ | any | `INT_INTERCOMPANY` | Intercompany immediate transfer (e.g. `TRANS INMEDIATA ISEAZY LMS`) |
| `TRANSFERENCIA RECIBIDA` + isEazy entity¹ | inflow | `INT_INTERCOMPANY` | Intercompany inbound |
| `TRANS INMEDIATA` (no isEazy entity) | inflow | `OCF_INCOME` | External receipt |
| `TRANS INMEDIATA` (no isEazy entity) | outflow | `OCF_PAYMENTS` | External payment |
| `RECIBO` or `CUOTA` | outflow | `FCF_LOAN_REPAYMENT` | Loan / direct debit repayment |
| `COMISION` or `MANTENIMIENTO` | outflow | `FCF_BANK_FEES` | Bank fee |
| `LIQUIDACION` + `INTERESES` | inflow | `FCF_DEPOSIT_INCOME` | Deposit interest |

#### Ruralvia (entity: SKILLS)

| Keyword pattern | Condition | → Canonical code | Rationale |
|----------------|-----------|-----------------|-----------|
| `rcbo. préstamo` or `rcbo. prestamo` | outflow | `FCF_LOAN_REPAYMENT` | Loan repayment (observed: `rcbo. préstamo6042762754`) |
| `liq.cta.vista` | outflow | `FCF_BANK_FEES` | Account maintenance fee (observed: `liq.cta.vista 6042761921`) |
| `trf.` + isEazy entity¹ | any | `INT_INTERCOMPANY` | Intercompany transfer (observed: `trf. bizpills group bpo s.l.`, `trf. iseazy skills sl`) |
| `trf.` (no isEazy entity) | inflow | `OCF_INCOME` | External receipt |
| `trf.` (no isEazy entity) | outflow | `OCF_PAYMENTS` | External payment |
| `remuneraci` | inflow | `FCF_DEPOSIT_INCOME` | Deposit/capital interest income |
| `impuesto` or `irc` | outflow | `OCF_TAX` | Withholding tax on interest |

#### Sabadell

| Keyword pattern | Condition | → Canonical code | Rationale |
|----------------|-----------|-----------------|-----------|
| `ABONO TRANSFERENCIA DE` + isEazy entity¹ | inflow | `INT_INTERCOMPANY` | Intercompany inbound |
| `ABONO TRANSFERENCIA DE` (no isEazy entity) | inflow | `OCF_INCOME` | Customer receipt (observed: `ABONO TRANSFERENCIA DE VOLKSWAGEN INTERNATIONAL BELGIUM`, `GENERALI SEGUROS`) |
| `NUESTRO PAGO s/fra.` | outflow | `OCF_PAYMENTS` | Outbound invoice payment (observed: `NUESTRO PAGO s/fra. F.BP.2024.1067`) |
| `LIQUIDAC.INTERESES IMPOSICION` | inflow | `FCF_DEPOSIT_INCOME` | Deposit interest income (observed: `LIQUIDAC.INTERESES IMPOSICION 179989462-04`) |
| `SEGUROS` (insurance company name) | outflow | `OCF_PAYMENTS` | Insurance premium (observed: `SEGUROS BANSABADELL VIDA,S.A.`) |
| `TRANSFER` + isEazy entity¹ | any | `INT_INTERCOMPANY` | Intercompany generic |
| `COMISION` or `MANTENIMIENTO` | outflow | `FCF_BANK_FEES` | Bank fee |

**Important note for seed validation:** All 4 banks have only SKILLS or FACTORY accounts in the samples. After first import, UNCLASSIFIED items will surface. The CFO should review the UNCLASSIFIED list and add/correct rules iteratively — that is by design (see Spec 08 v1.1).

---

## 5. Parser Interface Design

Based on the above analysis, each parser should implement this interface:

```python
class BankParser(ABC):
    bank_name: str        # e.g. "BBVA"
    file_engine: str      # "openpyxl" | "xlrd" | "calamine" | "csv"
    
    def can_parse(self, file_path: str) -> bool:
        """Return True if this parser handles the given file."""
    
    def parse(self, file_path: str) -> list[RawMovement]:
        """Parse file and return list of raw movements."""
    
    def extract_account_iban(self, file_path: str) -> str | None:
        """Extract IBAN from metadata block if available."""
```

**`RawMovement`** (pre-normalization):
```python
@dataclass
class RawMovement:
    bank: str
    file_path: str
    row_index: int
    booking_date: date
    value_date: date
    description: str
    description_detail: str | None
    counterpart_name: str | None
    amount: Decimal        # always signed, always EUR
    running_balance: Decimal
    operation_code: str | None
    reference: str | None
    raw_row: dict          # original row as dict, for audit trail
```

**Parser auto-detection** — identify bank from filename prefix:
- `Abanca_*` → `AbancaParser`
- `BBVA_*` → `BBVAParser`
- `BancaMarch_*` → `BancaMarchParser`
- `Bankinter_*` → `BankinterParser`
- `Caixa_*` → `CaixaBankParser`
- `Cajamar_*` → `CajamarParser`
- `DEUSTCHE_*` → `DeutscheBankParser`
- `EUROCAJA_*` → `EurocastRuralParser`
- `Ibercaja_*` → `IbercajaParser`
- `Ruralvia_*` → `RuralviaParser`
- `Sabadell_*` → `SabadellParser`
- `Santander_*` → `SantanderParser`

---

## 6. Open Issues

| Issue | Impact | Status |
|-------|--------|--------|
| Deutsche Bank entity | Medium | ✅ RESOLVED — SKILLS (`ES72 0019 0032 59 4010073742`) |
| `Bankinter Factory 2602` has only 1 data row | Low | ✅ Handle as near-empty account; not blocking |
| `CAIXA LMS 5705` is empty (`SIN MOVIMIENTOS`) | Low | ✅ Handle gracefully — zero rows, no exception |
| 4 banks with no VLOOKUP rules | High | ✅ AI-drafted seed rules in Section 4.5 — CFO to review after first import |
| Santander LMS 3917 multi-sheet | Medium | ✅ RESOLVED — merge ALL monthly sheets |
| Cajamar `Concepto` multiline split | Low | ✅ Implementation detail — no user action needed |

---

## 7. Acceptance Criteria for Parsers

- [ ] Each parser reads its file(s) without exception
- [ ] `amount` is always a signed `Decimal` (negative = outflow)
- [ ] `booking_date` and `value_date` are always `date` objects (no time component)
- [ ] Empty files (CaixaBank LMS 5705, Santander monthly sheets with `NO HAY MOVIMIENTOS`) return empty list, not exception
- [ ] `running_balance` is populated from every bank (all 12 banks provide it)
- [ ] `description` is never empty (NaN → empty string at minimum)
- [ ] All amounts for all loaded test files sum-check against known total (manual verification)
- [ ] Parser auto-detection correctly identifies bank from filename prefix for all 61 files
