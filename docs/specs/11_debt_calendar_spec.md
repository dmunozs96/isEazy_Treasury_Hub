# Spec 11 — Debt Calendar Engine

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Responsibility

Maintain a structured registry of all isEazy group debt instruments and their payment obligations, providing the CFO with:
- Upcoming maturity and payment alerts
- Total debt exposure per entity and consolidated
- Interest rate sensitivity visibility
- Covenant monitoring (informational only in Phase 1)

---

## 2. Supported Instrument Types

| Type | Description |
|------|-------------|
| LOAN | Term loans from banks |
| CREDIT_LINE | Revolving credit facilities |
| BOND | Bonds or notes payable |
| LEASING | Finance leases with fixed schedules |
| OTHER | Catch-all for non-standard instruments |

---

## 3. Data Entry Model

Phase 1: All debt data entered manually via UI. No banking system integration.

Finance team enters:
- Instrument details (name, bank, type, principal, rate, dates)
- Amortization schedule (manually entered or auto-generated from instrument terms)

Auto-generation of schedule:
- **BULLET:** single principal payment at maturity + periodic interest
- **FRENCH:** fixed installments (system calculates principal/interest split)
- **GERMAN:** fixed principal payments + decreasing interest
- **CUSTOM:** user enters schedule manually row by row

---

## 4. Alert System

### Alert Horizons

Three configurable alert horizons (default: 30, 60, 90 days):

| Alert Level | Horizon | Color |
|-------------|---------|-------|
| CRITICAL | ≤ 30 days | Red |
| WARNING | 31–60 days | Amber |
| UPCOMING | 61–90 days | Yellow |
| FUTURE | > 90 days | Gray |

### Alert Display

Dashboard widget: "Upcoming Debt Obligations"
- List of payments due in next 90 days
- Sorted by payment_date ASC
- Shows: instrument name, company, payment type, amount, days remaining
- Clicking opens instrument detail

---

## 5. Payment Linkage to Actuals

When a debt payment occurs:
1. Finance staff imports bank file (includes the payment movement)
2. Staff can manually link `DebtScheduleEntry` to the actual `Movement`
3. `DebtScheduleEntry.status` updated to PAID
4. `DebtScheduleEntry.movement_id` = linked movement

This creates traceability between the debt calendar and actual bank data.

---

## 6. Consolidated Debt View

| Metric | Computation |
|--------|-------------|
| Total outstanding | SUM(outstanding_balance) across all active instruments |
| Total scheduled payments (next 12m) | SUM(amount) WHERE payment_date BETWEEN now AND now+365 |
| Debt by entity | GROUP BY company_id |
| Debt by instrument type | GROUP BY instrument_type |
| Weighted average rate | WAVG(interest_rate, outstanding_balance) for fixed-rate instruments |

---

## 7. API Endpoints

```
GET    /api/v1/debt/instruments
POST   /api/v1/debt/instruments
GET    /api/v1/debt/instruments/{id}
PUT    /api/v1/debt/instruments/{id}
DELETE /api/v1/debt/instruments/{id}  (soft delete)

GET    /api/v1/debt/instruments/{id}/schedule
POST   /api/v1/debt/instruments/{id}/schedule/generate
  Body: { method: "FRENCH"|"GERMAN"|"BULLET" }
  — Auto-generate amortization schedule

POST   /api/v1/debt/schedule/{entry_id}/pay
  Body: { movement_id: UUID, notes: str }
  — Mark as paid and link to actual movement

GET    /api/v1/debt/alerts
  Query: horizon_days=90, company_id
  — Upcoming obligations within horizon

GET    /api/v1/debt/summary
  — Consolidated debt metrics
```

---

## 8. Acceptance Criteria

- [ ] A loan can be registered with full terms and auto-generated French amortization schedule
- [ ] Alerts appear for payments due within configured horizons
- [ ] A payment can be marked as PAID and linked to an actual bank movement
- [ ] Consolidated debt summary shows total outstanding by company and type
- [ ] Soft-delete works: instrument removed from active view, data preserved
- [ ] Schedule generation produces mathematically correct installment amounts

---

## 9. Edge Cases

| Case | Handling |
|------|---------|
| Variable rate loan (EURIBOR + spread) | Store reference_rate and spread; note that rate changes require manual update |
| Credit line (revolving, no fixed schedule) | Instrument stored without schedule; outstanding_balance updated manually |
| Overdue payment | DebtScheduleEntry.status = OVERDUE after payment_date passes without payment |
| Refinancing (old loan replaced by new) | Old instrument soft-deleted with notes; new instrument created |
| Loan in currency other than EUR | Not supported in Phase 1; reject with clear error |
