# ADR-005 — Rules-First Classification Architecture

**Date:** 2026-05-11  
**Status:** ACCEPTED  
**Deciders:** isEazy Treasury Hub founding architecture session  
**Tags:** architecture, classification, ai

---

## Context

We need to classify treasury movements into cash flow categories (Operating, Investing, Financing, Intercompany). The question is whether to use deterministic rules, an LLM/AI classifier, or a hybrid.

---

## Decision

**Rules-first architecture.** Deterministic keyword/regex rules are the primary and always-active classification mechanism. AI classification is advisory only and is a Phase 2 addition.

### Architecture

1. **Rules engine** (always on) — evaluates rules in priority order, first match wins
2. **AI suggestions** (Phase 2, opt-in) — advisory only, never auto-applied, requires human confirmation
3. **Manual override** (always available) — human decision always wins

---

## Rationale

### Why Not LLM-First?

- **Auditability:** A CFO needs to know WHY a movement was classified a certain way. "The AI said so" is not auditable. A keyword rule is auditable.
- **Determinism:** Same movement must always produce the same classification. LLMs are non-deterministic.
- **Cost:** Classifying 90,000 movements/year via Claude API has real cost. Rules are free.
- **Latency:** Bulk classification via LLM is slow. Rules classify 1000 movements in milliseconds.
- **Data privacy:** Sending bank transaction descriptions to an external API is a data governance concern.
- **Accuracy for structured domains:** Spanish treasury transaction descriptions are formulaic. Keyword rules achieve >90% accuracy for known patterns.

### Why Keep AI for Phase 2?

- The 5-10% of movements that don't match rules are genuinely ambiguous
- AI can learn from manual overrides to suggest classifications for novel patterns
- The system is designed to accept AI as a layer — it just never auto-applies

---

## Consequences

**Positive:**
- Every classification is fully auditable ("matched rule X: keyword 'NOMINA' in description")
- Classification is deterministic and fast
- No external API dependency for core functionality
- No data privacy risk from sending descriptions externally

**Negative:**
- Initial rule setup requires effort (need to define rules for all common Spanish treasury patterns)
- Novel transaction types won't be classified until a rule is written or AI phase is activated
- Rule maintenance is ongoing (new vendors, new transaction types)

---

## Compliance

No LLM call may be made to classify a movement and auto-apply the result without human confirmation. The rules engine must always run before any AI suggestion layer. Manual overrides must always be preserved during batch reclassification.

---

## Links

- Related Spec: [/docs/specs/08_classification_engine_spec.md](../specs/08_classification_engine_spec.md)
