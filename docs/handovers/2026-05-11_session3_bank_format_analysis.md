# Handover — 2026-05-11 — Session 3: Bank Format Analysis

**Session Date:** 2026-05-11  
**Session Focus:** Bank format analysis — reading all 12 bank statement formats, producing normalization mappings  
**Session Type:** Architecture / Spec Writing (no implementation code)  
**Status:** COMPLETE — Spec 16 confirmed by user (2026-05-11); all open questions resolved; ready for Milestone 1.1 + 1.2

---

## 1. What Was Done

- Read all 60+ bank statement files across 12 banks using Python (pandas + openpyxl + xlrd + calamine)
- Documented column structure, header row location, date format, amount convention, and quirks for each bank
- Read VLOOKUP classification file — extracted `Mapping` sheet with ~120 keyword → category rules
- Mapped CFO categories to canonical taxonomy codes (Spec 08 v1.1)
- Discovered 4 banks with zero classification rules (Deutsche Bank, Eurocaja Rural, Ruralvia, Sabadell)
- Discovered 2 banks requiring non-standard parsers (Cajamar + Sabadell: xlrd fails, must use calamine)
- Discovered 1 multi-sheet workbook (Santander LMS 3917.xls: monthly sheets with variable header rows)
- Produced complete Spec 16 — Bank Format Normalization Mappings
- Drafted parser class interface and auto-detection logic

---

## 2. Files Created

| File | Purpose |
|------|---------|
| `docs/specs/16_bank_format_normalization.md` | Full normalization mapping per bank; parser interface design; open issues |
| `docs/handovers/2026-05-11_session3_bank_format_analysis.md` | This document |

---

## 3. Key Findings

### Engine requirements (critical — wrong engine = parse failure)

| Engine | Banks |
|--------|-------|
| `openpyxl` | Abanca, BBVA, Banca March, Bankinter, Ibercaja, Ruralvia, Santander (.xlsx) |
| `xlrd` | CaixaBank, Deutsche Bank, Santander LMS 3917 (.xls) |
| `calamine` | Cajamar, Sabadell (.xls — xlrd fails with AssertionError) |
| `pandas csv` | Eurocaja Rural (.csv, utf-8-sig, semicolon) |

### Amount parsing anomalies

| Bank | Issue |
|------|-------|
| Deutsche Bank | Amounts are strings: `"-11.193,56"` — European format (`.` = thousands, `,` = decimal) |
| Eurocaja Rural | Amounts are strings with € symbol: `"-38.000,00 €"` — strip € then European parse |
| All others | Signed floats — straightforward Decimal cast |

### Structural anomalies

| Bank | Issue |
|------|-------|
| BBVA | Header at row 15 — 15-row metadata block before data |
| Santander LMS 3917 | Multi-sheet .xls — Hoja1 is a lookup table (skip), monthly sheets have variable header row |
| Cajamar | `Concepto` field has embedded `\n` — split on first newline |
| CaixaBank LMS 5705 | Empty file — `SIN MOVIMIENTOS` — must not throw exception |
| Bankinter | `REF. 16` column absent in 2 of 7 files |

### Classification rule gaps

4 banks have NO rules in the VLOOKUP: **Deutsche Bank, Eurocaja Rural, Ruralvia, Sabadell**. Their first import will produce all UNCLASSIFIED movements. Rules must be built manually post-import.

### Deutsche Bank entity unknown

The filename `DEUSTCHE_Movimientos_2025.xls` does not indicate the entity. IBAN in file is `ES72 0019 0032 59 4010073742`. **This needs confirmation from the user before the parser seeds the entity.**

---

## 4. VLOOKUP Mapping Sheet — Category Summary

All 12 categories found in the `Mapping` sheet:
- `Préstamos` → `FCF_LOAN_REPAYMENT` / `FCF_LOAN_DRAWDOWN` (sign-dependent)
- `Comisiones bancarias` → `FCF_BANK_FEES`
- `Transferencia Intercompañía` → `INT_INTERCOMPANY` / `INT_INTERCOMPANY_FOREIGN`
- `Cobro de clientes` → `OCF_INCOME`
- `Pago de nóminas` → `OCF_PAYROLL`
- `Pago de impuestos` / `Impuestos` → `OCF_TAX`
- `Cuotas Seguridad Social` → `OCF_SOCIAL_SECURITY`
- `Pago a proveedores` → `OCF_PAYMENTS`
- `Inversiones financieras` → `FCF_DEPOSIT_ISSUED` / `FCF_DEPOSIT_RETURN`

---

## 5. User Confirmations (2026-05-11)

All questions answered in session 3 continuation:

| # | Question | Answer |
|---|----------|--------|
| P1 | Deutsche Bank entity | **SKILLS** (Iseazy Skills, S.L.) |
| P2 | Cajamar newline split | Implementation detail — no user decision needed |
| P3 | Santander LMS 3917 multi-sheet | **Merge ALL monthly sheets** (team manually split tabs from working papers) |
| P4 | Bankinter IMPORTE vs DEBE/HABER | **Use IMPORTE — confirmed** |
| P5 | 4 banks with no rules | **AI to draft seed rules** — done in Spec 16 Section 4.5; CFO reviews post-import |
| P6 | Overall mappings | **Confirmed correct** |

---

## 6. State at End of Session

**Done:**
- All 12 bank formats analyzed
- All 60+ files successfully read (with correct engine)
- Spec 16 written with complete mapping tables
- Parser interface drafted
- VLOOKUP mappings extracted and canonical codes assigned

**Not started (requires confirmation first):**
- No parser code written
- No `RawMovement` / `Movement` models implemented
- No classification rules seeded

**Blocked:**
- Deutsche Bank entity assignment (P1)
- Milestone 1.2 parser implementation (needs P2–P6 confirmed)

---

## 7. Recommended Next Steps

**Option A — Confirm spec and begin parser implementation (Milestone 1.2)**
1. User reads Spec 16 and answers P1–P6
2. Begin project scaffolding (Milestone 1.1) in parallel
3. Implement parser base class + 12 bank parsers
4. Unit tests per parser against actual sample files

**Option B — Address remaining open questions first**
1. Answer Deutsche Bank entity question (P1)
2. Answer G6 (foreign entity names/patterns)
3. Then begin implementation

Recommended: Answer P1–P6 in this session if possible, then proceed to Milestone 1.1 scaffolding.

---

## 8. Quick Context for Next Session

All 12 bank formats are fully analyzed. The normalization mappings live in `docs/specs/16_bank_format_normalization.md`. Each bank needs a dedicated parser class using the engine specified in the spec. Two banks (Cajamar, Sabadell) require the `calamine` engine. Two banks (Deutsche Bank, Eurocaja Rural) have amounts stored as European-format strings requiring parsing. Santander has a multi-sheet edge-case file. The VLOOKUP file contains ~120 classification rules covering 8 of 12 banks; 4 banks have no rules and will produce UNCLASSIFIED on first import. The next step is: user confirms Spec 16, then either begin Milestone 1.1 (scaffolding) or go straight to Milestone 1.2 (parsers).
