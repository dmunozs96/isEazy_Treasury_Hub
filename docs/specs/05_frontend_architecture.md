# Spec 05 — Frontend Architecture

**Version:** 1.0  
**Status:** Draft  
**Date:** 2026-05-11

---

## 1. Technology Stack

| Concern | Technology | Rationale |
|---------|-----------|-----------|
| Framework | Next.js 14 (App Router) | Server components, file-based routing, strong TypeScript |
| Language | TypeScript (strict mode) | Type safety for financial data |
| Styling | TailwindCSS | Utility-first, design system compliant |
| Components | shadcn/ui | Accessible, customizable, Tailwind-compatible |
| Data tables | TanStack Table v8 | Virtualized, sortable, filterable, finance-grade tables |
| Charts | Recharts | Composable charts for financial visualization |
| State | Zustand | Simple, predictable global state |
| Server state | TanStack Query (React Query) | Cache, invalidation, loading states for API data |
| Forms | React Hook Form + Zod | Validation-first, type-safe forms |
| Icons | Lucide React | Consistent icon set |

---

## 2. Application Structure

```
/frontend
├── app/
│   ├── layout.tsx          — root layout (nav, theme)
│   ├── page.tsx            — redirect to /dashboard
│   ├── dashboard/
│   │   └── page.tsx        — cash position dashboard
│   ├── ledger/
│   │   ├── page.tsx        — treasury ledger table
│   │   └── [id]/page.tsx   — movement detail
│   ├── import/
│   │   └── page.tsx        — file import workflow
│   ├── forecast/
│   │   └── page.tsx        — 13-week forecast view
│   ├── debt/
│   │   └── page.tsx        — debt calendar
│   ├── intercompany/
│   │   └── page.tsx        — intercompany matching
│   └── settings/
│       └── page.tsx        — company setup, account registry
├── components/
│   ├── ui/                 — shadcn/ui base components
│   ├── layout/             — header, sidebar, page wrapper
│   ├── dashboard/          — dashboard-specific widgets
│   ├── ledger/             — ledger table and filters
│   ├── import/             — file upload, import status
│   ├── forecast/           — forecast chart, comparison table
│   ├── debt/               — debt timeline, calendar
│   ├── intercompany/       — match review UI
│   └── shared/             — date pickers, amount inputs, company selectors
├── lib/
│   ├── api/                — typed API client (fetch wrappers)
│   ├── formatters/         — currency, date, amount formatters
│   ├── validators/         — Zod schemas for forms
│   └── utils/              — shared utilities
├── store/
│   ├── filters.ts          — global filter state (date range, company, etc.)
│   ├── ui.ts               — sidebar state, modal state
│   └── user.ts             — session/user state
├── types/
│   └── api.ts              — TypeScript types matching backend Pydantic schemas
└── public/
    └── templates/          — downloadable Excel templates
```

---

## 3. Design System

### Colors (Finance-Grade Palette)

```
Primary:      Slate (950/900/800 for dark backgrounds)
Accent:       Blue (600/500 for interactive elements)
Positive:     Emerald (600) — inflows, positive variance
Negative:     Red (500) — outflows, negative variance, alerts
Warning:      Amber (500) — pending states, alerts
Neutral:      Gray (various) — text, borders
```

### Typography

- Font: Inter (system-optimized, finance-grade readability)
- Monospace: JetBrains Mono (for amounts, IBANs, reference codes)
- Amount display: always right-aligned, monospace, 2 decimal places

### Layout

- Desktop-first: minimum 1280px supported width
- Sidebar navigation (collapsible)
- Dense data tables as primary UI element
- Cards for aggregate metrics (KPI widgets)

---

## 4. State Management

### Zustand Stores

**FiltersStore** — global date/company/account filter state
```typescript
interface FiltersStore {
  dateRange: { from: Date; to: Date }
  companyIds: string[]
  bankAccountIds: string[]
  setDateRange: (range: DateRange) => void
  setCompanyIds: (ids: string[]) => void
  reset: () => void
}
```

**UIStore** — sidebar, modals, loading overlays
```typescript
interface UIStore {
  sidebarCollapsed: boolean
  activeModal: string | null
  toggleSidebar: () => void
  openModal: (id: string) => void
  closeModal: () => void
}
```

### TanStack Query

- All API data via React Query with typed query keys
- Stale time: 30 seconds for ledger data, 5 minutes for reference data
- Optimistic updates for classification overrides and intercompany confirmations

---

## 5. API Client

Typed API client wrapping `fetch`:

```typescript
// lib/api/movements.ts
export async function getMovements(params: MovementQueryParams): 
  Promise<PaginatedResponse<Movement>> { ... }

export async function overrideClassification(
  movementId: string, 
  body: ClassificationOverride
): Promise<MovementClassification> { ... }
```

All API types generated from or kept in sync with backend Pydantic schemas (manual sync in Phase 1; automated in Phase 2).

---

## 6. Key UI Patterns

### Treasury Ledger Table

- TanStack Table with server-side pagination and sorting
- Columns: Date | Company | Bank | Amount | Description | Category | Status
- Inline category override (click-to-edit)
- Bulk selection for mass re-classification
- Sticky header, horizontally scrollable on narrow viewports
- Export button triggers Excel download

### Dashboard Widgets

- KPI cards: Total Cash, Weekly Net Flow, 13-week runway
- Cash position by company (stacked bar or treemap)
- 13-week cash flow chart (Recharts AreaChart with 3 layers)
- Debt maturity timeline
- Intercompany alerts (pending confirmations)

### Import Flow

- Drag-and-drop file upload
- Bank account selector (pre-mapped from account registry)
- Import progress (polling status endpoint)
- Error summary after import (with downloadable error report)

### Forecast View

- Line chart: Actuals vs Official Forecast vs AI Forecast
- Period selector: weekly / monthly view
- Variance table: by category, by week
- Export to Excel

---

## 7. Excel Export

All export operations go through a dedicated API endpoint that returns:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="..."` 

Frontend triggers download via anchor tag with `href` to the export URL.

---

## 8. Error Handling

- API errors display toast notifications (shadcn/ui `useToast`)
- 4xx: user-facing message from API error schema
- 5xx: generic "Something went wrong, please try again"
- Import failures: dedicated error summary component with row-by-row detail
- Network errors: retry button

---

## 9. Accessibility

- WCAG AA compliance target (shadcn/ui provides baseline accessibility)
- All tables keyboard-navigable
- All forms have proper labels
- Color is never the only indicator (icons + color)

---

## 10. Build and Development

```bash
# Development
npm run dev          # Next.js dev server on :3000

# Type checking
npm run type-check

# Linting
npm run lint

# Production build
npm run build
```

Environment variables:
```
BACKEND_URL=http://localhost:8000
# Optional direct-browser mode:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```
