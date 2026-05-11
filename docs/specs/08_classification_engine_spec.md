# Spec 08 — Classification Engine

**Version:** 1.1  
**Status:** User-validated taxonomy — ready for implementation  
**Date:** 2026-05-11 (taxonomy revised session 2)

---

## 1. Responsibility

Assign treasury categories to movements using:
1. **Deterministic rules engine** (primary, always-on)
2. **Manual overrides** (human always wins)
3. **AI-assisted suggestions** (Phase 2, advisory only)

Classification is NOT accounting. It is treasury cash flow categorization for operational visibility.

---

## 2. Architecture: Rules-First

```
Movement Created / Classification Requested
    │
    ▼
[Rules Engine]
    - Load active rules, sorted by priority ASC
    - For each rule: evaluate match condition against movement fields
    - First matching rule wins
    - If no rule matches: category = UNCLASSIFIED
    │
    ▼
[MovementClassification record created]
    - source = RULE
    - rule_id = winning rule id
    - is_confirmed = TRUE (rules auto-confirm)
    │
    ▼ (Optional Phase 2)
[AI Suggestion Engine]
    - Only runs if no rule matched OR if confidence < threshold
    - Creates separate suggestion record
    - source = AI_SUGGESTION
    - is_confirmed = FALSE (requires human)
```

---

## 3. Category Taxonomy

All movements are mapped to this hierarchy. **This taxonomy is user-validated (session 2, 2026-05-11).**

```
OPERATING (OCF)
├── OCF_INCOME          — All operating inflows: client payments + other income (unified)
├── OCF_PAYMENTS        — All operating outflows: suppliers + operating expenses (unified)
├── OCF_PAYROLL         — Payroll, salaries, and social security contributions
└── OCF_TAX             — Tax payments (VAT, Corporate Tax, IRPF, etc.)

INVESTING (ICF)
├── ICF_CAPEX           — Capital expenditure / asset acquisitions
└── ICF_ASSET_SALE      — Asset disposals / proceeds from asset sales

FINANCING (FCF)
├── FCF_DEBT_DRAWDOWN   — Loan / credit line drawdowns (cash in)
├── FCF_DEBT_REPAYMENT  — Loan principal repayments (cash out)
├── FCF_INTEREST        — Interest payments on debt instruments (cash out)
├── FCF_DEPOSIT_ISSUED  — Short/long-term deposit placed (cash out from account; deposit with bank)
├── FCF_DEPOSIT_INCOME  — Interest received on deposits (cash in during deposit life)
├── FCF_DEPOSIT_RETURN  — Deposit principal returned at maturity (cash in; often combined with FCF_DEPOSIT_INCOME on the same date)
├── FCF_DIVIDENDS       — Dividends paid (rare; kept for identification when it occurs)
└── FCF_EQUITY          — Capital contributions received (rare; kept for identification)

INTERNAL
├── INT_INTERCOMPANY         — Transfers between the 6 Spanish group entities
│                              Subject to consolidation elimination when both legs confirmed
└── INT_INTERCOMPANY_FOREIGN — Transfers to/from foreign entities outside the group scope
                               (Brussels, Colombia, Mexico, Puerto Rico)
                               NOT eliminated in consolidated view — treated as real cash flow
                               Visible and labeled distinctly in entity and consolidated views

UNCLASSIFIED
└── UNCLASSIFIED        — No rule matched — flagged for manual review
```

### Taxonomy Design Rationale

**OCF merged categories:** Distinguishing suppliers from opex, or revenue from other income, is not reliably possible from bank statement descriptions alone. Merging these pairs avoids systematic misclassification.

**ICF scope:** Only CAPEX and asset sales. Financial instruments (deposits) are Financing, not Investing — deposits are a treasury liquidity management tool, not a capital allocation decision.

**FCF deposits:** Three-event lifecycle — issued (cash out), interest received periodically (cash in), principal returned at maturity (cash in, often on same date as final interest). All three must be present for the deposit life to net to zero in the cash flow view.

**INT_INTERCOMPANY_FOREIGN:** Foreign entities (Brussels, Colombia, Mexico, Puerto Rico) are out of scope for this platform. Their bank accounts are unknown, so we cannot see both legs of a transfer. Transfers to/from them represent real cash flows for the group and must NOT be eliminated. They are labeled as foreign intercompany so the CFO can identify them but knows they are external to the Spanish group perimeter.

---

## 4. Rule Evaluation

### Rule Priority

Rules evaluated lowest priority number first (priority 1 = evaluated first = highest importance).

### Match Types

**KEYWORD** — case-insensitive substring match:
```python
match_field = "description"
match_pattern = "NOMINA"
# Matches: "PAGO NOMINA ENERO", "NOMINAS FEBRERO", "NOMINA"
```

**REGEX** — full regex match against field:
```python
match_field = "description"
match_pattern = r"TRANSF.*HACIENDA"
```

**COUNTERPART_NAME** — match against counterpart_name field:
```python
match_field = "counterpart_name"
match_pattern = "AGENCIA TRIBUTARIA"
```

**AMOUNT_RANGE** — match by amount boundaries:
```python
match_pattern = '{"min": -5000, "max": 0}'
# Matches outflows up to -5000
```

**COMPOSITE** — AND of multiple conditions:
```python
match_pattern = '[
  {"type": "KEYWORD", "field": "description", "value": "SEGURIDAD SOCIAL"},
  {"type": "AMOUNT_RANGE", "min": -50000, "max": 0}
]'
```

### Rule Evaluation Algorithm

```python
def classify_movement(movement: Movement, rules: List[ClassificationRule]) -> ClassificationResult:
    # Rules sorted ascending by priority number — priority 1 is evaluated first (highest precedence)
    for rule in sorted(rules, key=lambda r: r.priority):
        if rule.is_active and evaluate_rule(rule, movement):
            return ClassificationResult(
                category_code=rule.category_code,
                source=ClassificationSource.RULE,
                rule_id=rule.id,
                confidence=1.0,  # Rules are deterministic — confidence is always 1.0
            )
    return ClassificationResult(
        category_code="UNCLASSIFIED",
        source=ClassificationSource.RULE,
        rule_id=None,
        confidence=1.0,  # "Unclassified" is also a deterministic outcome
    )
```

**Priority convention:** Lower priority number = higher precedence. Priority 1 is evaluated before priority 100. This matches the seeded rules table below.

**Confidence score convention:**
- Rule-based classifications: always `1.0` (deterministic, no uncertainty)
- UNCLASSIFIED result: always `1.0` (no rule matched — this is a certain outcome, not an uncertain one)
- AI suggestions (Phase 2): `0.0` to `1.0` (probabilistic — the only case with genuine uncertainty)

The `confidence` field in `MovementClassification` exists solely to support the Phase 2 AI suggestion layer. For Phase 1, all classifications have confidence = 1.0.

---

## 5. Manual Override Workflow

1. User selects a movement in the ledger
2. User selects a new category from the taxonomy dropdown
3. User optionally enters override reason
4. System creates new `MovementClassification`:
   - source = MANUAL
   - is_confirmed = TRUE
   - previous_category_code = current category
   - classified_by = user identifier
5. Previous classification is replaced (UNIQUE constraint on movement_id)

Override audit log: the `previous_category_code` and `override_reason` fields provide full audit trail.

---

## 6. Batch Classification

Endpoint to trigger classification for all unclassified or re-classify all movements:

```
POST /api/v1/classifications/batch
Body: {
  "movement_ids": ["uuid", ...] | null,  // null = all unclassified
  "force_reclassify": false
}
Response: {
  "processed": 150,
  "classified": 143,
  "unclassified": 7,
  "overrides_preserved": 12  // manual overrides are never touched
}
```

Manual overrides are ALWAYS preserved during batch re-classification.

---

## 7. Seeded Rules (Default Rule Set)

The system ships with a set of default classification rules for Spanish treasury operations.
Additional rules will be added once sample transaction descriptions are provided (see `/samples/transaction_descriptions/`).

| Priority | Name | Match Type | Pattern | Category |
|----------|------|-----------|---------|----------|
| 5  | Intercompany domestic (outbound) | COUNTERPART_NAME | (seeded from company registry) | INT_INTERCOMPANY |
| 6  | Intercompany domestic (inbound) | COUNTERPART_NAME | (seeded from company registry) | INT_INTERCOMPANY |
| 7  | Intercompany foreign | KEYWORD | (seeded from foreign entity names) | INT_INTERCOMPANY_FOREIGN |
| 10 | Seguridad Social | COUNTERPART_NAME | TESORERIA GENERAL | OCF_PAYROLL |
| 11 | Hacienda | COUNTERPART_NAME | AGENCIA TRIBUTARIA | OCF_TAX |
| 12 | Hacienda (desc) | KEYWORD | HACIENDA | OCF_TAX |
| 20 | Nóminas | KEYWORD | NOMINA | OCF_PAYROLL |
| 21 | Nóminas 2 | KEYWORD | SALARIO | OCF_PAYROLL |
| 30 | IVA | KEYWORD | LIQUIDACION IVA | OCF_TAX |
| 31 | Impuesto Sociedades | KEYWORD | IMPUESTO SOCIEDADES | OCF_TAX |
| 40 | Interés deuda | KEYWORD | LIQUIDACION INTERES | FCF_INTEREST |
| 41 | Interés deuda 2 | KEYWORD | CUOTA INTERES | FCF_INTEREST |
| 50 | Amortización préstamo | KEYWORD | AMORTIZACION PRESTAMO | FCF_DEBT_REPAYMENT |
| 51 | Amortización 2 | KEYWORD | CUOTA PRESTAMO | FCF_DEBT_REPAYMENT |
| 60 | Disposición crédito | KEYWORD | DISPOSICION CREDITO | FCF_DEBT_DRAWDOWN |
| 70 | Depósito constituido | KEYWORD | CONSTITUCION DEPOSITO | FCF_DEPOSIT_ISSUED |
| 71 | Depósito cancelado | KEYWORD | CANCELACION DEPOSITO | FCF_DEPOSIT_RETURN |
| 72 | Interés depósito | KEYWORD | LIQUIDACION DEPOSITO | FCF_DEPOSIT_INCOME |
| 80 | Inmovilizado | KEYWORD | COMPRA INMOVILIZADO | ICF_CAPEX |

**Note on intercompany rules (priority 5–7):** These are dynamically seeded at setup time from the Company registry (names and known IBANs of all group entities). They run first, before all other rules, to prevent misclassification of intercompany transfers as operating flows.

Additional rules to be built from sample transaction descriptions once provided.

---

## 8. API Endpoints

```
GET  /api/v1/classifications/rules
POST /api/v1/classifications/rules
PUT  /api/v1/classifications/rules/{id}
DELETE /api/v1/classifications/rules/{id}

POST /api/v1/movements/{id}/classify
  — Trigger re-classification of a single movement

POST /api/v1/movements/{id}/override
  Body: { category_code, reason }
  — Apply manual override

POST /api/v1/classifications/batch
  — Batch re-classify

GET  /api/v1/classifications/taxonomy
  — Return full category taxonomy
```

---

## 9. Acceptance Criteria

- [ ] A movement matching a KEYWORD rule is classified correctly
- [ ] A movement matching no rule is classified as UNCLASSIFIED
- [ ] Manual override persists after batch re-classification runs
- [ ] Override audit trail records previous category and user
- [ ] Rule priority order is respected (lower number wins)
- [ ] Batch classification processes 1000 movements in < 5 seconds
- [ ] Taxonomy endpoint returns full hierarchy in correct order

---

## 10. Phase 2: AI Suggestions

When implemented (Phase 2), the AI classification layer:
- Runs AFTER rules engine
- Only suggests for UNCLASSIFIED movements
- Confidence score attached to each suggestion
- User must confirm before suggestion is applied
- AI model (Claude or fine-tuned local model) — decision pending ADR
- AI suggestions are never auto-applied in Phase 1 or Phase 2 without confirmation
