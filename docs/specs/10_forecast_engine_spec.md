# Spec 10 — Forecast Engine

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Responsibility

Manage three parallel treasury forecast layers and provide a 13-week rolling view:
1. **ACTUALS** — real bank data from Treasury Ledger (read-only reference)
2. **OFFICIAL FORECAST** — finance team's committed view (imported via Excel)
3. **AI FORECAST** — system-generated statistical projection (Phase 2)

---

## 2. 13-Week Rolling View

The forecast horizon is always:
- **Start:** current Monday (or most recent Monday)
- **End:** 13 weeks from start (91 days)
- **Granularity:** weekly (7-day periods, Monday–Sunday)

The view "rolls" automatically: each week the horizon advances by one week.

Historical weeks show ACTUALS. Future weeks show OFFICIAL FORECAST (and AI FORECAST when available).

```
Week | Period        | Shows
-----|---------------|---------------------------
 -4  | Past          | ACTUALS (closed)
 -3  | Past          | ACTUALS (closed)
 -2  | Past          | ACTUALS (closed)
 -1  | Past          | ACTUALS (closed)
  0  | Current week  | ACTUALS (partial) + FORECAST
  1  | Future        | OFFICIAL FORECAST + AI FORECAST
  2  | Future        | OFFICIAL FORECAST + AI FORECAST
 ...
 13  | Future        | OFFICIAL FORECAST + AI FORECAST
```

---

## 3. Official Forecast Import

### Excel Template Format

The Official Forecast is entered by the finance team into a standardized Excel template:
- Template versioned (v1, v2, etc.)
- Template available for download from the platform
- Finance team fills in weekly amounts by category
- File uploaded to platform → imported as ForecastScenario

Template structure:
```
Sheet: "Forecast"
Row 1: Headers — "Category" | "Week 1 (DD/MM)" | "Week 2" | ... | "Week 13"
Row 2+: One row per category code
```

### Import Process

1. Finance team downloads template
2. Fills in weekly cash flow projections per category
3. Uploads to platform via Import UI
4. System creates `ForecastScenario` (source=OFFICIAL)
5. System creates `ForecastEntry` for each (company, week, category) cell
6. Previous active scenario for same period is deactivated (not deleted — versioned)

### Scenario Versioning

- Each upload creates a new `ForecastScenario`
- Only ONE scenario can be `is_active = TRUE` per company per period
- Previous scenarios are kept for comparison and audit
- User can reactivate a previous scenario if needed

---

## 4. Actuals Aggregation

Actuals are NOT stored in the forecast tables. They are computed on-demand:

```sql
SELECT
  date_trunc('week', value_date) AS week_start,
  category_code,
  SUM(amount) AS total_amount
FROM movements m
JOIN movement_classifications mc ON mc.movement_id = m.id
WHERE company_id = :company_id
  AND value_date BETWEEN :start AND :end
  AND is_deleted = FALSE
GROUP BY 1, 2
```

For the Actuals layer in the forecast view, this computation is called at query time.

---

## 5. Three-Layer Comparison API

```
GET /api/v1/forecast/comparison
Query:
  company_id: UUID (optional, null = consolidated)
  week_start: date (defaults to current week - 4)
  weeks: int (defaults to 17 = 4 past + 13 future)
  scenario_id: UUID (optional, defaults to active scenario)

Response:
{
  "weeks": [
    {
      "week_start": "2026-05-11",
      "week_label": "W20",
      "actuals": {
        "total": -45000.00,
        "by_category": { "OCF_REVENUE": 120000.00, "OCF_SUPPLIERS": -165000.00, ... }
      },
      "official_forecast": {
        "scenario_id": "uuid",
        "total": -38000.00,
        "by_category": { ... }
      },
      "ai_forecast": null  // Phase 2
    },
    ...
  ],
  "variance": [
    {
      "week_start": "2026-05-11",
      "actuals_total": -45000.00,
      "forecast_total": -38000.00,
      "variance_amount": -7000.00,
      "variance_pct": -18.4
    },
    ...
  ]
}
```

---

## 6. Variance Analysis

Variance = Actuals − Official Forecast

For weeks with both actuals and forecast data:
- Favorable variance: actuals better than forecast (e.g., higher inflows, lower outflows)
- Adverse variance: actuals worse than forecast

Variance computed:
- By week
- By category within week
- Cumulative (rolling total)

---

## 7. API Endpoints

```
GET  /api/v1/forecast/scenarios
POST /api/v1/forecast/scenarios/import     — upload Official Forecast Excel
GET  /api/v1/forecast/scenarios/{id}
PUT  /api/v1/forecast/scenarios/{id}/activate
DELETE /api/v1/forecast/scenarios/{id}

GET  /api/v1/forecast/entries
  Query: scenario_id, company_id, week_start, week_end, category_code

GET  /api/v1/forecast/comparison
  — Three-layer comparison (see above)

GET  /api/v1/forecast/variance
  — Variance analysis table

GET  /api/v1/forecast/template
  — Download Excel template
```

---

## 8. Acceptance Criteria

- [ ] Official Forecast Excel import creates a ForecastScenario with correct ForecastEntries
- [ ] Uploading a new forecast deactivates the previous active scenario for that period
- [ ] Actuals layer shows aggregated movements by week and category
- [ ] Three-layer comparison API returns data for both past (actuals) and future (forecast) weeks
- [ ] Variance computed correctly: actuals - forecast, per week and category
- [ ] Template download returns a valid Excel file with correct structure
- [ ] Multiple scenarios can exist for the same period (versioning)
- [ ] User can reactivate a previous scenario

---

## 9. Open Questions (Require User Input)

| # | Question |
|---|---------|
| 1 | Does the Official Forecast include all companies in one file, or one file per company? |
| 2 | What is the current Excel format the finance team uses for cash flow forecasting? |
| 3 | Weekly or daily forecast granularity needed? |
| 4 | Should the AI Forecast be in Phase 1 or Phase 2? |
| 5 | What is the "current" starting week — business week or calendar week? |
