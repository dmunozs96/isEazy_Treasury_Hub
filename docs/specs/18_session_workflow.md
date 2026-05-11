# Spec 18 — Session Workflow

**Version:** 1.0  
**Status:** Final  
**Date:** 2026-05-11

---

## Overview

This document defines the standard workflow for every AI-assisted development session on this project. Following this workflow ensures the project remains AI-session-resilient — any session can continue seamlessly from where the previous left off.

---

## Session Start Protocol

Every session MUST begin with:

### Step 1: Load Context

Read the following files IN ORDER:
1. `CLAUDE.md` — project identity and absolute rules
2. `TODO.md` — current work queue, open questions, blockers
3. Latest file in `/docs/handovers/` (sorted by date descending)
4. The relevant spec for the planned work

### Step 2: Confirm Scope

Before writing any code or specs:
- State clearly: "This session will work on: [module/spec/task]"
- Confirm there are no blockers listed in TODO.md for this module
- If open questions in TODO.md are relevant to the planned work: surface them to the user

### Step 3: Review Relevant Spec

If implementing a module:
- Read the full spec for that module
- Confirm the spec is approved (not just "Draft")
- If spec is Draft: complete and present spec for user review FIRST
- Do not implement a module whose spec has not been reviewed

---

## Session Execution Protocol

### One Module Rule

Each session works on ONE bounded context only:
- Import Engine session = ONLY import-related files
- If a bug is found in a different module during this session: log it in TODO.md, don't fix it now

### Spec-First Rule

If the spec for the planned module does not exist:
1. Write the spec first
2. Present it to the user for review
3. Only after approval: begin implementation
4. Never implement ahead of spec

### Documentation-While-Coding

- Update TODO.md immediately when discovering new issues or edge cases
- Add new open questions to TODO.md as they arise
- Do NOT rely on remembering to document at the end

---

## Session End Protocol

Every session MUST end with:

### Step 1: Write Handover Document

Create: `/docs/handovers/YYYY-MM-DD_<module_name>.md`

Use the template from `/docs/templates/HANDOVER_TEMPLATE.md`.

All sections are mandatory. No placeholder text.

### Step 2: Update TODO.md

- Mark completed items as `[x]`
- Add any new items discovered during session
- Update "Last updated" date
- Move completed milestone items to "Completed Work" table

### Step 3: Session Summary Output

Output the standardized session summary (see below).

---

## Standard Session Summary Format

```markdown
## Session Summary — [Date] — [Module Name]

### What Was Done
[Bulleted list of completed work]

### Files Modified
[List with paths]

### Architectural Decisions Made
[Decisions made during this session — link to ADRs if written]

### Open Risks Identified
[New risks discovered]

### Technical Debt Logged
[Any shortcuts taken with justification]

### Pending TODOs Added
[Items added to TODO.md during this session]

### Recommended Next Session
[What should be worked on next, and why]

### Validation Status
- [ ] Unit tests passing
- [ ] Type checks passing
- [ ] Manual smoke test done
- [ ] Spec validated against implementation

### Handover Document
/docs/handovers/[filename].md
```

---

## Spec Approval States

Specs progress through these states:

| State | Meaning | Action Allowed |
|-------|---------|---------------|
| `Draft` | Written but not reviewed | Review and discuss only |
| `Pending User Review` | Presented to user, awaiting sign-off | No implementation |
| `Approved` | User has explicitly approved | Implementation may begin |
| `Implemented` | Implementation complete | Maintenance only |
| `Deprecated` | Superseded by newer spec | Do not use |

---

## ADR Creation Rules

Create an ADR when:
- Choosing between two valid technical approaches
- Making a decision that is hard to reverse
- Deviating from the default tech stack
- Changing a canonical model structure

ADR format: `/docs/adr/ADR-NNN_short_title.md`

Use the template: `/docs/templates/ADR_TEMPLATE.md`

---

## Breaking Rules Protocol

If you believe a rule in this workflow should be broken for a good reason:

1. State the rule you're considering breaking
2. State the reason
3. Ask the user for explicit approval
4. Document the exception in the handover

Never silently break the workflow.
