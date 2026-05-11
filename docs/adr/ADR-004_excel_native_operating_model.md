# ADR-004 — Excel-Native Operating Model

**Date:** 2026-05-11  
**Status:** ACCEPTED  
**Deciders:** isEazy Treasury Hub founding architecture session  
**Tags:** architecture, ux, data

---

## Context

The isEazy finance team operates with Excel as their primary tool. Bank statements arrive as Excel/CSV exports. Forecasts are authored in Excel. Reports are expected in Excel. We must decide whether to treat Excel as a temporary workaround to be eliminated, or as a permanent part of the operating model.

---

## Decision

**Excel is part of the permanent operating model, not a temporary workaround.**

This means:
- The platform ALWAYS imports from Excel (no plan to eliminate this)
- The platform ALWAYS exports to Excel
- Official Forecast is always authored in Excel (the platform provides templates)
- Roundtrip operations (export → edit → import) are fully supported
- Excel template versioning is maintained indefinitely

---

## Rationale

- The finance team's Excel workflows are mature and effective for authoring
- Eliminating Excel requires replacing finance team workflows — that is not this project's scope
- Banking portals export Excel/CSV — this will not change in Phase 1 or 2
- CFO and finance directors are Excel-native users
- Excel as output format is non-negotiable for ad-hoc analysis

---

## Consequences

**Positive:**
- No friction from forcing workflow change on finance team
- Bank file ingestion is always possible even without API integrations
- Reports are immediately useful in finance team's existing tools

**Negative:**
- Import engine must handle heterogeneous bank Excel formats (ongoing maintenance)
- Template management adds complexity
- Excel cannot replace real-time data — users must remember to import files regularly

**Neutral:**
- PSD2/Open Banking integration remains a future option but is not required

---

## Compliance

Any proposal to "eliminate Excel" or treat it as a "legacy interface" should be rejected. New import sources (e.g., bank API feeds) are additive — they do not replace the Excel import path.

---

## Links

- Related Spec: [/docs/specs/12_excel_interoperability.md](../specs/12_excel_interoperability.md)
- Related Non-Goal: Excel replacement is in [/docs/specs/15_non_goals.md](../specs/15_non_goals.md) (PSD2) but Excel itself is kept
