# Spec 17 — Testing Strategy

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Philosophy

Treasury data is operationally critical. Tests must prove:
- Import pipeline produces correct, deduplicated results
- Classification rules produce deterministic results
- Intercompany matching is accurate (false positives are worse than false negatives)
- Financial calculations are correct to 2 decimal places

No mocking of business logic. Mock only: external HTTP calls, file system where not testing IO.

---

## 2. Test Pyramid

```
        ┌─────────────┐
        │    E2E      │  ← Playwright, minimal set, golden paths only
        ├─────────────┤
        │  Integration│  ← API tests with real test database
        ├─────────────┤
        │    Unit     │  ← Business logic, parsers, rules engine (majority)
        └─────────────┘
```

Target coverage: 80% on backend business logic (services). 
Coverage is a means, not a goal — focus on meaningful tests.

---

## 3. Backend Testing (pytest)

### Unit Tests: Import Parsers

Each bank format parser gets a dedicated test file with real anonymized sample files.

```python
# tests/test_import_engine/test_santander_parser.py
def test_parse_200_row_file():
    bytes = load_fixture("santander_sample_200rows.xlsx")
    rows = SantanderParser().parse(bytes)
    assert len(rows) == 200
    assert all(r.parse_error is None for r in rows)

def test_parse_negative_amounts():
    # outflows must be negative
    ...

def test_deduplication_hash_is_stable():
    # same row always produces same hash
    ...
```

### Unit Tests: Rules Engine

```python
# tests/test_classification/test_rules_engine.py
def test_keyword_rule_matches_case_insensitive():
    movement = build_movement(description="PAGO NOMINA ENERO")
    rule = build_rule(match_type=KEYWORD, pattern="nomina", category="OCF_PAYROLL")
    result = rules_engine.classify(movement, [rule])
    assert result.category_code == "OCF_PAYROLL"

def test_priority_order_respected():
    # lower priority number wins
    ...

def test_manual_override_not_touched_by_reclassify():
    ...
```

### Unit Tests: Intercompany Matcher

```python
def test_exact_amount_opposite_sign_proposed():
    ...

def test_beyond_3_day_window_not_proposed():
    ...

def test_tolerance_within_2_eur():
    ...

def test_already_matched_movement_not_re_proposed():
    ...
```

### Unit Tests: Calculations

```python
def test_direct_cash_flow_statement_totals():
    # OCF + ICF + FCF = Net Cash Flow
    ...

def test_variance_calculation():
    # actuals - forecast, correct sign
    ...

def test_opening_closing_balance():
    ...
```

### Integration Tests: API (real test DB)

```python
# tests/test_api/test_import_api.py
@pytest.mark.asyncio
async def test_upload_file_creates_import_batch(client, test_db):
    response = await client.post(
        "/api/v1/imports",
        files={"file": ("test.xlsx", fixture_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"bank_account_id": str(test_bank_account.id)}
    )
    assert response.status_code == 201
    batch = response.json()
    assert batch["status"] == "COMPLETED"
    assert batch["imported_count"] > 0
```

### Test Database Setup

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def test_engine():
    # Use separate test DB: treasury_hub_test
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine

@pytest.fixture(autouse=True)
async def rollback_after_test(test_db):
    # Each test runs in a transaction that is rolled back
    yield
    await test_db.rollback()
```

---

## 4. Frontend Testing (Vitest + React Testing Library)

### Component Unit Tests

Focus on business-critical components:
- Amount formatting (EUR format, negative in red)
- Date range filter state management
- Ledger table sorting and filtering
- Import file upload flow
- Classification override modal

```typescript
// tests/components/AmountDisplay.test.tsx
test("negative amounts display in red with minus sign", () => {
  render(<AmountDisplay amount={-1234.56} />)
  expect(screen.getByText("−€1,234.56")).toHaveClass("text-red-500")
})
```

### No E2E tests in Phase 1

E2E tests (Playwright) are Phase 2. Golden path manual testing for Phase 1.

---

## 5. Test Data Strategy

### Fixture Files

- `/tests/fixtures/bank_files/santander_sample.xlsx` — anonymized real-format file
- `/tests/fixtures/bank_files/bbva_sample.xlsx`
- `/tests/fixtures/bank_files/generic_sample.csv`
- `/tests/fixtures/forecast/official_forecast_v1.xlsx`

**Important:** All fixture files must use fictional company names and scrambled amounts. No real isEazy financial data in the repository.

### Factories / Builders

```python
# tests/factories.py
def build_movement(**overrides) -> Movement:
    defaults = {
        "amount": Decimal("-1000.00"),
        "value_date": date(2026, 1, 15),
        "description": "PAGO PROVEEDOR TEST",
        ...
    }
    return Movement(**{**defaults, **overrides})
```

---

## 6. Financial Calculation Test Requirements

Any function computing financial amounts MUST have tests that verify:
- Exact decimal precision (to 2 decimal places)
- Correct sign convention
- Correct aggregation (SUM, not AVERAGE)
- Edge case: zero amounts
- Edge case: very large amounts (> €1M)
- Edge case: negative total results

---

## 7. CI Integration (Phase 2)

Phase 1: manual test runs before deploy.
Phase 2: GitHub Actions CI pipeline:
```yaml
on: [push, pull_request]
jobs:
  backend-tests:
    - pytest with test database
  frontend-tests:
    - vitest
  type-check:
    - mypy (backend)
    - tsc --noEmit (frontend)
```

---

## 8. Performance Tests (Manual)

Before production launch, manually verify:
- Import 500-row Santander file: < 10 seconds
- Dashboard load with 6 months of data: < 2 seconds
- Ledger query with filters (10,000 movements): < 500ms
- Classification batch (1,000 movements): < 5 seconds
