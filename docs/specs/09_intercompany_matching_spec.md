# Spec 09 — Intercompany Matching Engine

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Responsibility

Detect internal fund transfers between isEazy group entities and:
- Prevent double-counting in consolidated cash flow views
- Surface intercompany balance positions
- Maintain individual entity visibility (intercompany flows visible at entity level)

This is a CRITICAL domain. Errors here inflate or deflate consolidated cash flow figures.

---

## 2. Why This Matters

Without intercompany elimination, consolidated cash flow would show:
- An outflow from Company A (paying Company B)
- An inflow to Company B (receiving from Company A)

This inflates both gross inflows and gross outflows by the intercompany amount, distorting the consolidated picture.

The elimination means: at consolidated level, these cancel out. At individual entity level, both sides remain visible.

---

## 3. Internal Account Registry

All isEazy group bank accounts are stored in `bank_accounts` with `is_internal = TRUE`.

The registry is the foundation of matching:
- A movement is a candidate for intercompany matching if either `bank_account_id` OR `counterpart_iban` corresponds to an internal account.

The registry must be complete and accurate. Missing internal accounts = missed matches.

---

## 4. Matching Algorithm (Deterministic)

### Candidate Generation

For each new movement M:
1. Check if `M.bank_account_id` → `bank_account.is_internal = TRUE`
2. OR check if `M.counterpart_iban` is an IBAN of an internal bank account
3. If either: M is an intercompany candidate

### Match Criteria (ALL must be satisfied)

| Criterion | Rule |
|-----------|------|
| Opposite sign | `amount_A + amount_B ≈ 0` (within tolerance) |
| Same absolute value | `|amount_A| == |amount_B|` within €0.01 tolerance |
| Date proximity | `|value_date_A - value_date_B| ≤ 3 business days` |
| Internal accounts | Both movements in internal accounts |
| Not already matched | Neither movement has a confirmed match |

### Match Scoring

When multiple candidates match a given movement, score by:
1. Exact amount match scores higher than tolerance match
2. Same date scores higher than ±3 day match
3. Counterpart IBAN directly identified scores higher than amount-only match

Highest-scoring candidate presented first for human confirmation.

---

## 5. Match States

```
IN_TRANSIT  — One leg detected in an internal account; other leg not yet found
              Treated as "pending match" for up to 5 business days
              Excluded from consolidated view optimistically (avoids spurious net imbalance)
              After 5 business days without the second leg → escalates to UNRESOLVED for human review

PROPOSED    — Both legs found; system proposing a match pair; awaiting human confirmation

CONFIRMED   — Human confirmed this is a true intercompany transfer
              Both movement legs marked is_intercompany = TRUE
              Eliminated from consolidated view

REJECTED    — Human rejected this match (not actually intercompany)
              Movements return to normal — not eliminated

UNRESOLVED  — IN_TRANSIT escalated after 5 business days without a matching leg
              Requires human investigation — may be a real external payment misrouted
              Shown in the Consistency & Completeness panel as an alert
```

Only **CONFIRMED** matches trigger elimination in the consolidated view.
**IN_TRANSIT** matches are also excluded from the consolidated view (optimistic exclusion) to prevent temporary double-counting during the transit window.
**INT_INTERCOMPANY_FOREIGN** movements are never subject to elimination — they are classified and labeled but treated as real cash flows.

### Cash in Transit — Design Rationale

When Company A sends €X to Company B, both legs may hit the banking system 1–3 business days apart. During that window, the consolidated view would show a real debit from Company A with no matching credit in Company B — creating a spurious net outflow in the consolidated statement.

The IN_TRANSIT state handles this: as soon as one leg is detected in an internal account and its counterpart IBAN is another internal account, the system creates an IN_TRANSIT match and excludes that movement from the consolidated total. If Company B's leg appears within 5 business days, it upgrades to PROPOSED for human confirmation. If not, it escalates to UNRESOLVED for investigation.

---

## 6. Confirmation Workflow

1. System detects match → creates `IntercompanyMatch` with `status=PROPOSED`
2. Dashboard shows "X pending intercompany matches to review"
3. User opens Intercompany review screen
4. User reviews pair: Company A outflow | Company B inflow
5. User clicks CONFIRM or REJECT
6. On CONFIRM:
   - `IntercompanyMatch.status = CONFIRMED`
   - Both movements: `is_intercompany = TRUE`, `intercompany_match_id = match.id`
   - Both movements: category overridden to `INT_INTERCOMPANY`
7. On REJECT:
   - `IntercompanyMatch.status = REJECTED`
   - Movements unchanged
   - System will not re-propose this pair automatically

---

## 7. Consolidated View Elimination

**Domestic intercompany (INT_INTERCOMPANY):**
- Filter out all movements where `is_intercompany = TRUE` AND `intercompany_match_id` points to a CONFIRMED match
- Also exclude IN_TRANSIT movements optimistically (one leg detected, transit window not yet expired)
- This eliminates both legs of the transfer from the consolidated view

**Foreign intercompany (INT_INTERCOMPANY_FOREIGN):**
- NOT eliminated. These represent real cash leaving or entering the Spanish group.
- Shown in the consolidated view with a distinct label ("Intercompany Foreign") so the CFO can identify them
- No matching attempted — we do not have visibility into the foreign entity's books

**In individual entity view:**
- All movements shown regardless of intercompany status
- INT_INTERCOMPANY movements labeled and colored distinctly (e.g., orange/amber)
- INT_INTERCOMPANY_FOREIGN movements labeled distinctly (e.g., purple)
- IN_TRANSIT movements shown with a "clock" indicator — pending match

## 7a. Foreign Entity Registry

A separate registry of known foreign entity names and any known IBANs or reference patterns is maintained to support INT_INTERCOMPANY_FOREIGN classification rules.

```
ForeignEntity
├── id: UUID (PK)
├── name: str — legal name of the foreign entity
├── country: str — ISO 3166-1 alpha-2 country code (BE, CO, MX, PR, ...)
├── known_ibans: list[str] — known IBANs if available (optional)
├── keyword_patterns: list[str] — description keywords to auto-classify
└── is_active: bool
```

This registry seeds classification rules at priority 7 (before all other operating rules).

---

## 8. API Endpoints

```
GET  /api/v1/intercompany/matches
  Query: status=PROPOSED|CONFIRMED|REJECTED, company_id, date_from, date_to

GET  /api/v1/intercompany/matches/{id}

POST /api/v1/intercompany/matches/{id}/confirm
  Body: { notes: str (optional) }

POST /api/v1/intercompany/matches/{id}/reject
  Body: { reason: str }

POST /api/v1/intercompany/matches/manual
  Body: { movement_out_id, movement_in_id, notes }
  — Manual match creation (when automatic detection missed it)

POST /api/v1/intercompany/scan
  — Trigger match detection scan for new unmatched movements
  Response: { new_proposals: int }

GET  /api/v1/intercompany/summary
  — Net intercompany positions per company pair
```

---

## 9. Intercompany Balance Summary

For each company pair (A → B), the system shows:
- Total confirmed intercompany flows A→B (outflow from A, inflow to B)
- Total confirmed intercompany flows B→A
- Net position: A→B net

This surfaces structural intercompany funding relationships.

---

## 10. Acceptance Criteria

- [ ] A transfer from Company A to Company B (same amount, within 3 days) is auto-proposed
- [ ] User can confirm or reject the proposed match
- [ ] Confirmed match excludes both legs from consolidated cash flow
- [ ] Individual entity view shows both legs regardless of intercompany status
- [ ] A movement cannot be in two simultaneous confirmed matches
- [ ] Manual match creation works when automatic detection misses a pair
- [ ] Rejection prevents automatic re-proposal of the same pair
- [ ] Intercompany balance summary correctly aggregates all confirmed matches

---

## 11. Edge Cases

| Case | Handling |
|------|---------|
| Round-trip same day (A→B and B→A same day) | Both proposed as separate matches |
| Partial transfers (A sends 1000, B receives 998 after bank fees) | Tolerance: ≤ €2.00 accepted as match, flagged for review |
| Three-way transfers (A→B→C) | Only direct pairs matched; A→C not proposed |
| Multiple movements with same amount same day | All proposed as candidates; human selects correct pair |
| Holding company treasury pooling | Each pool movement matched individually |
| Unmatched movement in internal account | Stays as normal movement (not all internal account movements are intercompany) |
