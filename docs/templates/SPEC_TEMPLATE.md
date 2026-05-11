# Spec NN — [Module Name]

**Version:** 1.0  
**Status:** Draft | Pending User Review | Approved | Implemented | Deprecated  
**Date:** YYYY-MM-DD  
**Author:** [Session identifier]

---

## 1. Responsibility

[One paragraph: what this module does and what it owns. What does it NOT do? Max 5 sentences.]

---

## 2. Bounded Context

**Owns:**
- [Model A]
- [Model B]

**Consumes:**
- [What inputs does it receive, from where]

**Emits:**
- [What outputs does it produce, to where]

**Does NOT:**
- [Explicit list of things this module deliberately does not do]

---

## 3. Architecture

[Diagram or description of internal structure. Include data flow if complex.]

```
[Input] → [Step 1] → [Step 2] → [Output]
```

---

## 4. Key Rules / Business Logic

[The non-obvious rules and invariants that make this module correct. These are the things that MUST be tested.]

1. Rule: [statement]
   - Rationale: [why]
2. Rule: [statement]

---

## 5. Data Models

[Reference to canonical models or define them here if module-specific]

See `/docs/specs/03_canonical_models.md` for: [ModelA, ModelB]

---

## 6. API Endpoints

[All endpoints this module exposes]

```
VERB  /api/v1/[resource]
  Request: { ... }
  Response: { ... }
  Errors: [list error cases]
```

---

## 7. Edge Cases

| Case | Handling |
|------|---------|
| [Case] | [How it is handled] |

---

## 8. Acceptance Criteria

All must be true for this spec to be considered implemented:

- [ ] 
- [ ] 
- [ ] 

---

## 9. Test Strategy

[What must be tested, at what level (unit / integration / e2e)]

- Unit: [what]
- Integration: [what]
- Manual: [what]

---

## 10. Open Questions

[Questions requiring user input before implementation can begin]

| # | Question | Priority | Owner |
|---|----------|----------|-------|
| 1 | | | |
