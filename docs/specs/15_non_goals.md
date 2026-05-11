# Spec 15 — Non-Goals

**Version:** 1.0  
**Status:** Final  
**Date:** 2026-05-11

---

## Purpose

This document defines what isEazy Treasury Hub will NOT build. These are explicit scope boundaries, not "future features." Any request to implement items in this list requires a full scope review and stakeholder sign-off.

These non-goals protect the project from scope creep and keep the platform focused on treasury intelligence.

---

## Category 1: Accounting System Features

**NOT building:**
- Double-entry bookkeeping / journal entries
- Chart of accounts management
- Accounting reconciliation (matching invoices to payments)
- GL posting or GL integration
- Financial statement generation (P&L, Balance Sheet, EBITDA)
- VAT ledgers or tax accounting
- Asset accounting / depreciation schedules
- Cost center accounting
- Accrual accounting logic

**Why:** These are Sage XRT / ERP features. The platform is a treasury visibility tool, not an accounting system. Financial statements come from accounting systems.

---

## Category 2: ERP Integration

**NOT building:**
- SAP, Oracle, or any ERP connector
- Sage XRT integration or replacement
- Purchasing/AP workflow
- Sales/AR workflow
- Inventory integration
- HR/payroll system integration
- Purchase order management

**Why:** ERP systems already exist. Treasury Hub reads bank data independently of ERP.

---

## Category 3: Banking Integration

**NOT building:**
- PSD2 / Open Banking API connections
- Direct bank API feeds
- SWIFT connectivity
- Real-time balance feeds from banking portals
- Payment initiation
- SEPA file generation
- Bank mandate management

**Why:** Phase 1 is explicitly Excel/CSV file import. Automated banking feeds are a future phase and require regulatory compliance work.

---

## Category 4: Invoice Management

**NOT building:**
- Invoice capture or OCR
- Invoice-to-payment matching
- Supplier invoice ledger
- Customer invoice ledger
- Accounts payable workflow
- Accounts receivable aging

**Why:** These are AP/AR functions belonging to accounting systems. Treasury Hub works with cash movements only, not invoices.

---

## Category 5: Multi-Currency

**NOT building (Phase 1):**
- Foreign currency account management
- FX rate feeds or conversions
- Multi-currency reporting
- FX hedging tracking
- Cross-currency cash pooling

**Why:** isEazy Group Phase 1 scope is EUR only. Multi-currency requires significant additional complexity (FX rates, revaluation, translation) that is out of scope.

---

## Category 6: Advanced Authentication & Authorization

**NOT building (Phase 1):**
- SSO / SAML / OAuth integration
- Fine-grained RBAC (role-based access control)
- Multi-tenant architecture
- IP whitelisting
- MFA
- Audit log with user attribution (basic attribution yes, full audit no)
- Data classification and access restrictions per company

**Note:** Architecture must remain COMPATIBLE with adding these later. The absence is a Phase 1 decision, not a permanent architectural constraint.

---

## Category 7: Mobile

**NOT building:**
- Mobile-optimized UI
- Native iOS / Android app
- Progressive Web App (PWA)
- Responsive breakpoints for < 1024px

**Why:** CFO and finance staff use desktops. Mobile adds significant development overhead for no Phase 1 benefit.

---

## Category 8: Advanced AI Features

**NOT building (Phase 1):**
- LLM-powered transaction classification (rules engine only)
- Natural language queries ("show me last month's outflows")
- AI-generated narrative reports
- Anomaly detection
- Predictive alerts
- Automated forecasting (AI Forecast is Phase 2)

**Why:** Rules-first architecture is more auditable and reliable for financial data. AI features require a data foundation that only exists after Phase 1 is operational.

---

## Category 9: Process Automation

**NOT building:**
- Automated payment reminders
- Automated report distribution (email)
- Scheduled report generation
- Workflow approvals (multi-step)
- Treasury policy enforcement

---

## Enforcement Protocol

When a request is made to implement a feature in this list:

1. **Identify** — Is this feature in the non-goals list?
2. **Confirm** — Is this genuinely a non-goal or a misclassification?
3. **Escalate** — If the request is valid and a non-goal should be reconsidered, document it in TODO.md as an open question
4. **Decline** — Do not implement without explicit sign-off

The goal is to ship a focused, excellent treasury intelligence platform — not to rebuild Sage XRT.
