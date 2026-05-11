# Company Registry — isEazy Group

**Last updated:** 2026-05-11  
**Status:** Confirmed by CFO (session 2). Holding flag TBD (pending user confirmation).

This is the seed data for the `Company` table. All 6 entities are in Phase 1 scope.

---

## Entities

| Display Name | Legal Name | Known Aliases / Bank File Labels | Shortcode | is_holding |
|---|---|---|---|---|
| BPO | Bizpills Group BPO, S.L. | Bizpills Group, BIZPILLS, BPO | BPO | **true** (HoldCo) |
| Author | IsEazy, S.L. | isEazy Author, ISEAZY, AUTHOR, AUTHORING | AUTHOR | false (OpCo) |
| Skills | IsEazy Skills, S.L. | SKILLS | SKILLS | false (OpCo) |
| Factory | IsEazy Factory, S.L. | FACTORY | FACTORY | false (OpCo) |
| Engage | IsEazy Engage, S.L. | ENGAGE | ENGAGE | false (OpCo) |
| LMS | IsEazy LMS, S.L. | LMS | LMS | false (OpCo) |

**Confirmed by CFO, 2026-05-11.**

---

## Business Rules

- **HoldCo (BPO) does not receive customer collections.** Any movement classified as `OCF_INCOME` on a BPO account should be flagged as a data quality warning in the Consistency & Completeness panel. It may be a misclassification, an intercompany transfer incorrectly labelled, or a genuine exception requiring CFO review.

---

## Intercompany Classification Rules (seeded from this registry)

The following patterns will be used to auto-classify `INT_INTERCOMPANY` movements at rule priority 5–6.
Rules match case-insensitively against the movement description and counterpart name fields.

| Entity | Keywords to match in bank descriptions |
|--------|----------------------------------------|
| BPO | `BIZPILLS`, `BPO` |
| Author | `ISEAZY` (standalone), `ISAZY`, `AUTHOR`, `AUTHORING` |
| Skills | `SKILLS` |
| Factory | `FACTORY` |
| Engage | `ENGAGE` |
| LMS | `LMS` |

**Note:** These patterns need validation against actual bank statement descriptions once the bank format analysis session runs. Adjust after seeing real data.

---

## Foreign Entities (Out of Scope — INT_INTERCOMPANY_FOREIGN)

Transfers to/from these entities are classified as `INT_INTERCOMPANY_FOREIGN` and are **NOT** eliminated in the consolidated view.

| Location | Entity name(s) | Keywords (TBD) |
|----------|---------------|----------------|
| Belgium (Brussels) | TBD | TBD |
| Colombia | TBD | TBD |
| Mexico | TBD | TBD |
| Puerto Rico | TBD | TBD |

**Action required:** User to provide names/patterns for the foreign entities so classification rules can be seeded.
