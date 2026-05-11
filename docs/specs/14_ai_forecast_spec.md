# Spec 14 — AI Forecast Engine

**Version:** 1.0  
**Status:** Draft — Phase 2 (Not in Phase 1 Scope)  
**Date:** 2026-05-11

---

## 1. Status

**Phase 2 only.** AI Forecast is NOT in Phase 1 scope.

This spec defines the architecture for when it is built, so Phase 1 design decisions do not block Phase 2 implementation.

---

## 2. Responsibility

Generate a statistical/AI-assisted cash flow forecast for the 13-week rolling horizon, based on historical movement patterns. Provide this as the third layer alongside Actuals and Official Forecast.

---

## 3. Architectural Constraints

- AI Forecast is ALWAYS labeled as AI-generated
- AI Forecast NEVER overrides Official Forecast without explicit user action
- AI Forecast confidence intervals must be displayed alongside point estimates
- AI Forecast is computed asynchronously (not blocking the user)
- AI Forecast can be toggled off entirely by the CFO

---

## 4. Input Data Requirements

Minimum data requirements before AI Forecast can be enabled:
- At least 13 weeks of historical actuals data
- At least 80% of historical movements classified
- Intercompany movements properly marked (to avoid polluting forecast)

If requirements not met: AI Forecast shows "Insufficient data" message, not an empty chart.

---

## 5. Forecasting Approach Options

| Approach | Pros | Cons | Decision |
|----------|------|------|---------|
| Simple moving average | Easy to explain, deterministic | Misses seasonality | Baseline |
| SARIMA/ETS | Handles seasonality, well-understood | Requires tuning | Phase 2 default |
| LLM-based (Claude API) | Can incorporate qualitative context | Cost, latency, explainability | Phase 3 research |
| Prophet (Meta) | Good for business time series | ML dependency | Alternative |

**Recommended approach:** ETS/SARIMA per category, then aggregate. This is explainable, doesn't require an external API, and handles Spanish business seasonality (August, Christmas, Q1 tax payments).

ADR required before implementation.

---

## 6. Forecast Output Schema

```python
class AIForecastEntry(BaseModel):
    company_id: UUID
    week_start_date: date
    category_code: str
    point_estimate: Decimal   # midpoint forecast
    lower_bound: Decimal      # 80% confidence interval lower
    upper_bound: Decimal      # 80% confidence interval upper
    confidence_score: float   # 0.0 to 1.0 (model quality for this category)
    model_version: str        # which model/parameters generated this
    generated_at: datetime
```

---

## 7. Training and Refresh

- Initial training: triggered manually by admin
- Refresh: weekly (Monday morning, before work starts)
- Model artifacts: not stored in DB — recomputed from historical movements on each run
- No persistent ML model state in Phase 2 (recompute is fast enough for SME data volumes)

---

## 8. Explainability Requirements

Each AI Forecast entry must be accompanied by:
- Confidence score
- Data basis: "Based on X weeks of history"
- Trend indicator: "Category is trending +12% vs 4-week average"

No black-box outputs. Every AI forecast number must have a simple human-readable explanation.

---

## 9. Human Supervision Requirements

- CFO can dismiss AI Forecast from dashboard with one click
- CFO can flag AI Forecast as "unreliable" for a specific category
- Finance team can upload Official Forecast which always supersedes AI Forecast
- System does not auto-apply AI Forecast to any planning or reporting

---

## 10. Privacy and Data Considerations

- All AI computation uses only internal treasury data — no data sent to external services in Phase 2
- If LLM-based forecasting is considered (Phase 3): separate ADR required covering data privacy, no raw transaction descriptions to be sent to external APIs

---

## 11. Phase 1 Placeholder

During Phase 1, the AI Forecast layer is shown in the UI as:
- Visible section in the forecast chart
- Labeled: "AI Forecast (Coming Soon)"
- Not clickable
- No phantom data displayed

This ensures the UI is designed for 3 layers from day 1.
