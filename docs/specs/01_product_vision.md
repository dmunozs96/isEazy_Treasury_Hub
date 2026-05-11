# Spec 01 — Product Vision

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Problem Statement

isEazy Group operates multiple legal entities with ~90 bank accounts and no centralized treasury visibility. The CFO and finance team currently:

- Cannot see consolidated cash position without manual Excel aggregation
- Cannot generate direct cash flow statements without significant manual effort
- Cannot produce rolling 13-week forecasts reliably
- Cannot detect intercompany transfer imbalances easily
- Cannot monitor debt maturities and treasury obligations in one place
- Cannot perform variance analysis between forecast and actuals systematically

This creates:
- Operational risk (missed payments, liquidity gaps not spotted early)
- Decision-making latency (CFO lacks real-time data)
- Manual labor overhead (finance staff spend hours reconciling Excel files)
- Forecast unreliability (no structured forecast vs actuals comparison)

---

## 2. Vision Statement

**isEazy Treasury Hub is the single source of treasury truth for the isEazy Group**, providing the CFO and finance team with:

- Real-time visibility into consolidated and per-entity cash positions
- Direct (cash-basis) cash flow statements automatically generated from bank data
- 13-week rolling treasury forecasts compared against actuals
- Intercompany monitoring with automatic internal transfer detection
- Debt calendar visibility with upcoming obligation alerts
- Finance-grade variance analysis and treasury KPIs

The platform operates **alongside** existing accounting tools, not replacing them.

---

## 3. Three-Layer Data Model

The system is built around three parallel data layers:

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: ACTUALS                                   │
│  Source: Bank files (Excel/CSV imports)             │
│  Truth: Bank transactions as they occurred          │
│  Owner: System (automated from imports)             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  LAYER 2: OFFICIAL FORECAST                         │
│  Source: Finance team Excel template uploads        │
│  Truth: Finance team's committed view of cash flow  │
│  Owner: Finance team (human-authored)               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  LAYER 3: AI FORECAST                               │
│  Source: System-generated from actuals patterns     │
│  Truth: Statistical/AI projection                   │
│  Owner: System (AI-assisted, human-supervised)      │
└─────────────────────────────────────────────────────┘
```

These three layers are always visible together for comparison, never as the only truth.

---

## 4. Target Users

### Primary User: CFO

**Needs:**
- Dashboard with consolidated cash position (morning briefing view)
- 13-week cash flow forecast vs actuals
- Debt maturity calendar with alerts
- Intercompany balance summary
- Variance analysis: Why did this week differ from forecast?

**Usage pattern:** Read-mostly. Reviews dashboards and exports. Occasional configuration of forecast scenarios.

### Secondary User: Finance Operations Staff

**Needs:**
- Upload bank files (Excel/CSV)
- Upload official forecast Excel templates
- Review and confirm classification suggestions
- Confirm intercompany matches
- Export reports

**Usage pattern:** Write-heavy. Operational data entry and review workflows.

---

## 5. What Success Looks Like

### Phase 1 Success Criteria

- [ ] CFO can see consolidated cash position for all group entities in under 2 seconds
- [ ] Finance staff can import a bank file and see categorized movements in under 1 minute
- [ ] 13-week rolling forecast is visible with actuals overlay
- [ ] Intercompany transfers are automatically detected and flagged for confirmation
- [ ] Debt calendar shows upcoming maturities with 30/60/90 day alerts
- [ ] CFO can export any view to Excel with one click
- [ ] System handles the full set of isEazy bank accounts without manual aggregation

---

## 6. What This Is NOT

See `/docs/specs/15_non_goals.md` for the full non-goals register.

Brief summary:
- NOT an ERP or accounting system
- NOT a reconciliation engine
- NOT a PSD2/Open Banking platform
- NOT a Sage XRT replacement
- NOT a multi-currency system (Phase 1: EUR only)
- NOT a mobile platform
- NOT an invoice management system

---

## 7. Operating Model

The platform is **Excel-native** by design. This means:

- Finance staff continue working in Excel for forecast authoring
- Bank data arrives as Excel/CSV exports from banking portals
- All platform outputs can be exported to Excel
- Excel is not a workaround — it is part of the permanent operating model

The platform adds:
- Centralization of data
- Automation of aggregation
- Intelligence layer (classification, matching, forecasting)
- Visualization and dashboards

---

## 8. Deployment Philosophy

- Railway-hosted (cloud, managed infrastructure)
- Single production environment for Phase 1
- Desktop browser as primary client (no mobile optimization required)
- Finance-grade reliability required (99.5% uptime target)
