# ADR-002 — Monorepo Structure

**Date:** 2026-05-11  
**Status:** ACCEPTED  
**Deciders:** isEazy Treasury Hub founding architecture session  
**Tags:** architecture, infra

---

## Context

Decide how to organize the codebase: monorepo (all services in one repo) vs polyrepo (separate repos per service).

---

## Decision Drivers

- Small team (1-2 developers)
- Frontend and backend are tightly coupled in this domain
- Shared type definitions between frontend and backend
- Simple Railway deployment
- AI-assisted development benefits from full context access

---

## Options Considered

### Option A: Monorepo with `/frontend`, `/backend`, `/shared` (Selected)

**Pros:**
- Single `git clone` to get everything
- Shared types in `/shared` (even if managed manually in Phase 1)
- Atomic commits across frontend and backend
- Full codebase visible to AI development sessions
- Simple Railway deployment from single repo

**Cons:**
- Slightly more complex CI if added later (need to filter which service to rebuild)

### Option B: Polyrepo (separate repos)

**Pros:**
- Independent versioning
- Separate CI pipelines

**Cons:**
- Cross-repo changes require coordinated PRs
- Harder to share types
- More operational overhead for a 2-person team
- AI session loses context across repos

---

## Decision

**Chosen:** Option A — Monorepo

The simplicity and coherence benefits outweigh the minor CI complexity for a small team with tight coupling between services.

---

## Consequences

**Positive:**
- Single source of truth for the entire system
- Easy cross-service refactoring

**Negative:**
- Must tag releases carefully if frontend and backend versions diverge

---

## Compliance

All code lives in this repository. No separate repos will be created for frontend or backend services.

---

## Links

- Related Spec: [/docs/specs/00_architecture.md](../specs/00_architecture.md)
