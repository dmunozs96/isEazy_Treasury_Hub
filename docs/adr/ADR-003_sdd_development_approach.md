# ADR-003 — Spec-Driven Development (SDD) Approach

**Date:** 2026-05-11  
**Status:** ACCEPTED  
**Deciders:** isEazy Treasury Hub founding architecture session  
**Tags:** architecture, process

---

## Context

We are building a treasury intelligence platform with AI-assisted development sessions. Each AI session has no memory of previous sessions. Financial systems require high correctness, auditability, and clear domain boundaries. We need a development methodology that ensures quality across sessions.

---

## Decision

**Spec-Driven Development (SDD):** All work begins with a specification. No implementation begins without an approved spec. Every session ends with a handover document.

### Core Rules

1. **Spec before code** — Every module starts with a written spec
2. **One session = one module** — No cross-context mixing in a single session
3. **Mandatory handovers** — Every session produces a handover document
4. **File-persisted state** — No reliance on conversational memory; all decisions in files
5. **Architecture before features** — Foundation before functionality

### Rationale

- AI sessions have no memory: files must carry all state
- Financial systems require explicit domain boundaries: bounded contexts prevent corruption
- Treasury data is operationally critical: correctness must be provable, not assumed
- Small team: explicit specs prevent re-working decisions already made

---

## Consequences

**Positive:**
- Any session can continue seamlessly from handover
- Specs serve as living documentation
- Architecture decisions are auditable
- Onboarding new developers is simple (read the specs)

**Negative:**
- More upfront time investment in Phase 0
- Slower initial progress (by design — correctness over speed)

---

## Compliance

If a session begins without reading the latest handover and TODO.md, it is non-compliant with SDD.
If implementation begins without an approved spec, it is non-compliant with SDD.
Non-compliance must be flagged immediately and corrected.
