# Spec 13 — Dashboard & UX

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Design Principles

- **Desktop-first:** optimized for 1440px+ screens; minimum supported: 1280px
- **Finance-grade density:** maximum information per screen; no wasted whitespace
- **Fast scanning:** CFO needs to absorb dashboard in < 30 seconds
- **No ambiguity:** every number shows its unit, its sign, and its date range
- **Export everywhere:** every view can be exported to Excel in one click

---

## 2. Navigation Structure

```
Sidebar (left, collapsible)
├── Dashboard          — overview and KPIs
├── Treasury Ledger    — movement table
├── Forecast           — 13-week view
├── Intercompany       — match review
├── Debt Calendar      — obligations
├── Analytics          — variance analysis, liquidity
└── Settings           — companies, accounts, rules
```

---

## 3. Dashboard View

### Global Filters (persistent, top of screen)

```
[Company: All ▼] [Date Range: This Month ▼] [Apply]
```

Filters persist across navigation via Zustand global state.

### KPI Cards Row

```
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  CASH POSITION  │ │  NET FLOW (WTD) │ │   RUNWAY        │ │  PENDING ALERTS │
│  €4,231,450     │ │  − €87,300      │ │  34 weeks       │ │  3 debt / 5 IC  │
│  Consolidated   │ │  This week      │ │  At current burn│ │  Need review    │
└─────────────────┘ └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Cash Position by Company (Bar Chart)

- Stacked horizontal bar chart (Recharts)
- One bar per company
- Color by company
- Click to drill down to company ledger

### 13-Week Cash Flow Chart

- X-axis: weeks (current week centered)
- Y-axis: net cash flow
- Three lines: Actuals (solid), Official Forecast (dashed), AI Forecast (dotted, Phase 2)
- Shaded background: past weeks vs future weeks
- Recharts AreaChart or ComposedChart

### Upcoming Obligations (Debt Calendar Widget)

- Table: next 5 debt payments
- Columns: Date | Days | Company | Instrument | Type | Amount
- Color-coded by alert level
- "See all" link → Debt Calendar page

### Intercompany Alerts

- Count of pending intercompany matches awaiting confirmation
- "Review X matches" CTA → Intercompany page

---

## 4. Treasury Ledger View

### Filters Panel (top)

```
[Date From] [Date To] [Company ▼] [Bank ▼] [Category ▼] [Amount Min] [Amount Max] [Search] [Apply] [Reset]
```

### Movements Table (TanStack Table)

| Column | Width | Notes |
|--------|-------|-------|
| Value Date | 100px | Sortable |
| Company | 120px | Filterable |
| Bank | 80px | Filterable |
| Amount | 120px | Right-aligned, monospace, red if negative |
| Description | 300px | Truncated with tooltip |
| Counterpart | 150px | |
| Category | 150px | Click to override |
| Source | 80px | RULE / MANUAL / AI icon badge |
| Intercompany | 40px | Icon if flagged |

- 50 rows per page, server-side pagination
- Sortable by date, amount
- Inline category edit: click category → dropdown → save
- Bulk select + bulk re-classify action
- Export button: "Export filtered view to Excel"

---

## 5. Forecast View

### Period Selector

```
[← Previous] [13 weeks: 2026-05-11 → 2026-08-09] [Next →] [Monthly view]
```

### Three-Layer Chart

- X-axis: weeks
- Three datasets: Actuals (bar), Official Forecast (line), AI Forecast (dotted line)
- Toggle each layer on/off

### Variance Table

```
Week | Actuals | Forecast | Variance € | Variance % | Direction
W20  | -42,000 | -38,000  | -4,000     | -10.5%     | ▼ Adverse
W21  | -31,000 | -35,000  | +4,000     | +11.4%     | ▲ Favorable
...
```

### Category Drill-Down

Click a week to expand: shows variance by category.

---

## 6. Intercompany Review View

### Pending Matches Table

```
Status: PROPOSED (5 matches)

Movement OUT           | Movement IN           | Amount    | Date Gap | Action
Company A → (BBVA)     | Company B ← (Santan.) | €100,000  | 0 days   | [Confirm] [Reject]
Company C → (CaixaB.)  | Company A ← (BBVA)    | €45,000   | 1 day    | [Confirm] [Reject]
```

- Click row to expand full movement details for both legs
- Confirm/Reject buttons with confirmation dialog
- Rejection requires reason text

### Confirmed Matches Tab

- Historical list of confirmed intercompany matches
- Filter by company pair, date range
- Unmatch action (requires reason, elevated action)

### Balance Matrix

```
         | Company A | Company B | Company C | Holding
Company A |     —     | +100,000  | 0         | -250,000
Company B | -100,000  |     —     | 0         | 0
Company C |     0     |     0     | —         | -45,000
Holding   | +250,000  |     0     | +45,000   | —
```

---

## 7. Debt Calendar View

### Timeline View

- Gantt-style timeline showing debt instruments
- Each instrument: horizontal bar from drawdown_date to maturity_date
- Alert markers at upcoming payment dates

### Upcoming Payments Table

```
Date       | Days | Company | Instrument     | Type      | Amount     | Status
15/05/2026 |   4  | OpCo A  | Préstamo Santan| PRINCIPAL | €125,000   | ⚠ CRITICAL
30/05/2026 |  19  | OpCo B  | Leasing Fleet  | INTEREST  | €8,400     | ⚠ WARNING
15/06/2026 |  35  | Holding | Línea Crédito  | MIXED     | €500,000   | UPCOMING
```

---

## 8. Accessibility & Interaction

- All tables: keyboard navigation (arrow keys, Tab, Enter to select)
- All forms: proper `<label>` associations
- All modal dialogs: focus trap, Escape to close
- Date pickers: accessible, keyboard-operable
- Amount inputs: always EUR, comma or dot decimal accepted, formatted on blur
- Color + icon always paired (never color-only status indicator)

---

## 9. Loading States

- Skeleton loaders for all table views
- Spinner overlay for form submissions
- Import progress: polling every 2 seconds, progress bar
- Error states: inline error messages, not just toast notifications

---

## 10. Export Buttons

Every view has an export button:
```
[↓ Export to Excel]
```

Export filename includes view name, filters applied, and date:
```
ledger_all-companies_2026-01-01_2026-03-31.xlsx
forecast_comparison_W20-W33.xlsx
```

---

## 11. Consistency & Completeness Panel

**Purpose:** Allows the CFO to verify that the import phase is complete and that the data is internally consistent before reading any analytics. This panel is the quality gate — if it shows issues, the CFO knows not to trust the figures until they are resolved.

Access: Settings → Consistency Check, or as a banner alert on the Dashboard when issues are detected.

### Section A — Import Completeness

Answers: "Have all expected bank accounts been imported for the selected period?"

```
Period: [Month ▼]  Company: [All ▼]   [Run check]

Account                         | Expected | Last Import | Coverage | Status
BPO — Santander 0416            | Jan–May  | 2026-05-03  | Full     | ✅
BPO — BBVA Bizpills Group       | Jan–May  | 2026-04-28  | Partial  | ⚠ 5 weeks missing
Author — CaixaBank 4002          | Jan–May  | 2026-05-03  | Full     | ✅
Skills — Bankinter 7545         | Jan–May  | (none)      | Missing  | 🔴 Not imported
...
```

- Status ✅ = imported and covers the full selected period
- Status ⚠ = imported but gaps detected (date range has holes)
- Status 🔴 = no import found for this period

### Section B — Balance Reconciliation

Answers: "Do the imported movements reconcile with the bank's reported opening and closing balances?"

For each imported batch where the bank file includes a balance column:

```
Account                  | Period      | Opening Bal | Closing Bal (bank) | Closing Bal (computed) | Delta   | Status
BPO — Santander 0416     | May 2026    | €1,234,500  | €1,189,300         | €1,189,300             | €0.00   | ✅
BPO — BBVA Bizpills      | May 2026    | €450,000    | €420,100           | €420,087.43            | −€12.57 | ⚠ Review
```

- ✅ = closing balance matches to within €0.01
- ⚠ = difference within €50 — flag for review (may be bank rounding)
- 🔴 = difference > €50 — data integrity issue, investigation required

### Section C — Data Quality Warnings

Business rule violations surfaced as warnings for CFO review:

| Rule | Description |
|------|-------------|
| HoldCo revenue | Any `OCF_INCOME` movement on a BPO (HoldCo) account. HoldCo does not receive customer collections — likely a misclassification or an intercompany transfer labelled incorrectly. |
| High unclassified rate | If > 15% of movements for a company/period are UNCLASSIFIED, flag as a classification coverage warning. |
| Unresolved intercompany | Any `INT_INTERCOMPANY` movement older than 5 business days with no confirmed match. |
| IN_TRANSIT timeout | Intercompany movements in IN_TRANSIT state past the 5-business-day window. |

Each warning shows: company, account, movement details, and a direct link to the movement in the Treasury Ledger for inline review.
