# Spec 12 — Excel Interoperability

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Design Philosophy

Excel is NOT a temporary workaround. Excel is part of the permanent operating model.

The platform must:
- Accept Excel as input (imports)
- Produce Excel as output (exports)
- Maintain versioned Excel templates
- Support roundtrip operations (export → edit → import)

---

## 2. Import Scenarios

| Scenario | Template | Context |
|----------|----------|---------|
| Bank statement import | Bank-native format (no template) | Import Engine |
| Official Forecast import | Standardized template (versioned) | Forecast Engine |
| Debt schedule import | Standardized template | Debt Calendar (future) |
| Classification rule import | Standardized template | Classification Engine (future) |

---

## 3. Export Scenarios

| Scenario | Output | Trigger |
|----------|--------|---------|
| Treasury ledger export | Filtered movements → Excel | User clicks "Export" in Ledger view |
| Cash flow statement | Weekly/monthly CF statement → Excel | Dashboard export |
| Forecast comparison | 3-layer forecast table → Excel | Forecast view export |
| Debt calendar export | Scheduled payments → Excel | Debt Calendar export |
| Intercompany summary | Match matrix → Excel | Intercompany view |
| Error report | Import errors → Excel | After failed/partial import |

---

## 4. Excel Library

**openpyxl** for all Excel operations (no dependency on Excel installation).

Rationale:
- Pure Python, no COM interop required
- Supports modern .xlsx format
- Supports rich formatting needed for financial reports
- Well-maintained, widely used

---

## 5. Template Design Principles

1. **Named ranges** — use Excel named ranges for data areas (not hardcoded cell references)
2. **Version header** — every template has a version cell (e.g., A1 = "TEMPLATE_VERSION: 2")
3. **Validation sheets** — drop-down lists for categories, companies use hidden validation sheets
4. **Protected structure** — header rows and formatting are protected; only data cells editable
5. **Backward compatibility** — system supports importing old template versions

---

## 6. Official Forecast Template (v1)

### Sheet: Instructions
- Human-readable description of how to fill the template
- Category code reference table

### Sheet: Forecast
```
A1: TEMPLATE_VERSION: 1
A3: Company
B3: Category Code
C3: Category Name
D3: [Week 1 date, e.g., "11/05/2026"]
E3: [Week 2 date]
...
P3: [Week 13 date]

Row 4+: One row per (Company, Category) combination
Column D-P: EUR amounts (positive = inflow, negative = outflow)
```

### Validation
- Category codes validated against taxonomy (error if invalid code)
- Amounts validated as numeric
- Company names validated against company registry
- Missing weeks treated as 0 (not an error)

---

## 7. Export Format Design

### Treasury Ledger Export

Columns: Date | Value Date | Company | Bank | Account (IBAN masked) | Amount | Description | Counterpart | Category | Classification Source | Import Batch

Formatting:
- Amounts: currency format EUR, 2 decimal places, red for negative
- Dates: DD/MM/YYYY
- Header row: frozen, bold, light blue background
- Alternating row shading

### Cash Flow Statement Export

```
Sheet: Cash Flow Statement

Period: [Month or Week] | [Column per period]

Operating Cash Flow
  Revenue Collections         | 120,000 | 98,000 | ...
  Supplier Payments          | (65,000) | (70,000) | ...
  Payroll                    | (45,000) | (45,000) | ...
  ...
Total Operating CF           | 10,000  | (17,000) | ...

Investing Cash Flow
  ...

Financing Cash Flow
  ...

NET CASH FLOW               | 10,000  | (17,000) | ...
Opening Balance             | 500,000 | 510,000 | ...
Closing Balance             | 510,000 | 493,000 | ...
```

---

## 8. Export API Design

All exports served as streaming responses:

```python
@router.get("/exports/ledger")
async def export_ledger(params: LedgerExportParams) -> StreamingResponse:
    excel_bytes = await excel_service.export_ledger(params)
    filename = f"ledger_{params.date_from}_{params.date_to}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
```

---

## 9. Template Versioning

Templates stored in `/public/templates/` in the frontend and `/backend/templates/` for import parsing.

Version management:
- Template version is embedded in the file (cell A1 or dedicated header)
- Parser selects correct parsing logic based on detected version
- Old versions remain parseable (backward compatibility guaranteed)
- Breaking template changes require new version number

---

## 10. Acceptance Criteria

- [ ] A bank statement (Santander format) imports correctly
- [ ] Official Forecast template v1 imports correctly and creates ForecastEntries
- [ ] Treasury ledger export produces valid Excel with correct formatting
- [ ] Cash flow statement export produces correct totals
- [ ] Template download serves a valid, fillable Excel file
- [ ] Old template versions remain importable after template upgrades
- [ ] Error report export shows row-level errors clearly
