"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, startOfMonth, subWeeks } from "date-fns";
import { Download, RefreshCw } from "lucide-react";

import { analyticsApi, type CashFlowFilters } from "@/lib/api/analytics";
import { companiesApi } from "@/lib/api/companies";
import { formatAmount } from "@/lib/formatters";
import type { CashFlowGranularity, CashFlowSection, CashFlowStatement } from "@/types/api";

const SECTION_LABELS: Record<CashFlowSection, string> = {
  OPERATING: "Operating Cash Flow",
  INVESTING: "Investing Cash Flow",
  FINANCING: "Financing Cash Flow",
  INTERNAL: "Internal Cash Flow",
  UNCLASSIFIED: "Unclassified",
};

const SECTION_ORDER: CashFlowSection[] = [
  "OPERATING",
  "INVESTING",
  "FINANCING",
  "INTERNAL",
  "UNCLASSIFIED",
];

function amountClass(value: string | number) {
  const n = Number(value);
  if (n > 0) return "text-emerald-700";
  if (n < 0) return "text-red-600";
  return "text-muted-foreground";
}

function NumberCell({ value, strong = false }: { value: string | number; strong?: boolean }) {
  return (
    <td className={`px-3 py-2 text-right tabular-nums whitespace-nowrap ${amountClass(value)} ${strong ? "font-semibold" : ""}`}>
      {formatAmount(value)}
    </td>
  );
}

function EmptyState() {
  return (
    <div className="px-6 py-16 text-center text-sm text-muted-foreground">
      No cash-flow movements found for the selected filters.
    </div>
  );
}

function StatementTable({ statement }: { statement: CashFlowStatement }) {
  const sectionTotals = useMemo(
    () => new Map(statement.sections.map((s) => [s.section, s])),
    [statement.sections],
  );

  if (statement.rows.length === 0) return <EmptyState />;

  return (
    <div className="overflow-auto">
      <table className="w-full border-collapse text-sm">
        <thead className="sticky top-0 z-10 bg-muted/90 backdrop-blur-sm">
          <tr>
            <th className="sticky left-0 z-20 bg-muted/90 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b min-w-64">
              Category
            </th>
            {statement.periods.map((period) => (
              <th
                key={period.key}
                className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b min-w-28"
                title={`${period.start_date} to ${period.end_date}`}
              >
                {period.label}
              </th>
            ))}
            <th className="px-3 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground border-b min-w-28">
              Total
            </th>
          </tr>
        </thead>
        <tbody>
          {SECTION_ORDER.flatMap((section) => {
            const rows = statement.rows.filter((row) => row.section === section);
            const total = sectionTotals.get(section);
            if (rows.length === 0 && !total) return [];

            return [
              <tr key={`${section}-total`} className="border-b bg-muted/50">
                <td className="sticky left-0 bg-muted/50 px-3 py-2 font-semibold text-foreground">
                  {SECTION_LABELS[section]}
                </td>
                {(total?.values ?? statement.periods.map(() => "0")).map((value, idx) => (
                  <NumberCell key={`${section}-total-${idx}`} value={value} strong />
                ))}
                <NumberCell value={total?.total ?? "0"} strong />
              </tr>,
              ...rows.map((row) => (
                <tr key={`${row.section}-${row.category_code}`} className="border-b hover:bg-muted/30">
                  <td className="sticky left-0 bg-background px-3 py-2">
                    <div className="font-medium text-foreground">{row.category_name}</div>
                    <div className="text-xs text-muted-foreground">{row.category_code}</div>
                  </td>
                  {row.values.map((value, idx) => (
                    <NumberCell key={`${row.category_code}-${idx}`} value={value} />
                  ))}
                  <NumberCell value={row.total} strong />
                </tr>
              )),
            ];
          })}
          <tr className="border-t-2 bg-blue-50/80">
            <td className="sticky left-0 bg-blue-50/80 px-3 py-2 font-bold text-foreground">
              NET CASH FLOW
            </td>
            {statement.net_cash_flow.map((value, idx) => (
              <NumberCell key={`net-${idx}`} value={value} strong />
            ))}
            <NumberCell value={statement.net_cash_flow_total} strong />
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default function CashFlowPage() {
  const [granularity, setGranularity] = useState<CashFlowGranularity>("weekly");
  const [dateFrom, setDateFrom] = useState(format(subWeeks(new Date(), 13), "yyyy-MM-dd"));
  const [dateTo, setDateTo] = useState(format(new Date(), "yyyy-MM-dd"));
  const [companyId, setCompanyId] = useState("");
  const [includeIntercompany, setIncludeIntercompany] = useState(false);

  const { data: companies = [] } = useQuery({
    queryKey: ["companies"],
    queryFn: companiesApi.list,
    staleTime: 5 * 60_000,
  });

  const filters = useMemo<CashFlowFilters>(
    () => ({
      granularity,
      date_from: dateFrom,
      date_to: dateTo,
      company_id: companyId || undefined,
      include_intercompany: includeIntercompany,
    }),
    [granularity, dateFrom, dateTo, companyId, includeIntercompany],
  );

  const { data, isLoading, isError, isFetching, refetch } = useQuery({
    queryKey: ["cashflow", filters],
    queryFn: () => analyticsApi.cashflow(filters),
  });

  function handlePreset(next: CashFlowGranularity) {
    setGranularity(next);
    if (next === "monthly") {
      setDateFrom(format(startOfMonth(new Date()), "yyyy-MM-dd"));
      setDateTo(format(new Date(), "yyyy-MM-dd"));
    } else {
      setDateFrom(format(subWeeks(new Date(), 13), "yyyy-MM-dd"));
      setDateTo(format(new Date(), "yyyy-MM-dd"));
    }
  }

  function handleExport() {
    window.open(analyticsApi.cashflowExportUrl(filters), "_blank");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-6 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-foreground">Cash Flow Statement</h1>
            {data && (
              <p className="mt-0.5 text-sm text-muted-foreground">
                {data.date_from} to {data.date_to} · {data.periods.length} period{data.periods.length !== 1 ? "s" : ""}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors hover:bg-muted disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors hover:bg-muted"
            >
              <Download className="h-4 w-4" />
              Export Excel
            </button>
          </div>
        </div>
      </div>

      <div className="border-b px-6 py-3 flex flex-wrap items-center gap-3">
        <div className="inline-flex rounded-md border p-0.5">
          {(["weekly", "monthly"] as const).map((option) => (
            <button
              key={option}
              onClick={() => handlePreset(option)}
              className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
                granularity === option
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {option === "weekly" ? "Weekly" : "Monthly"}
            </button>
          ))}
        </div>

        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="rounded-md border bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <span className="text-sm text-muted-foreground">to</span>
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="rounded-md border bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        />

        <select
          value={companyId}
          onChange={(e) => setCompanyId(e.target.value)}
          className="rounded-md border bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">Consolidated group</option>
          {companies.map((company) => (
            <option key={company.id} value={company.id}>
              {company.short_name}
            </option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={includeIntercompany}
            onChange={(e) => setIncludeIntercompany(e.target.checked)}
            className="h-4 w-4 rounded border-input"
          />
          Include confirmed intercompany
        </label>

        {isFetching && <span className="text-xs text-muted-foreground">Loading...</span>}
      </div>

      <div className="flex-1 overflow-hidden">
        {isError ? (
          <div className="p-8 text-center text-sm text-destructive">
            Could not load the cash-flow statement. Check the API connection.
          </div>
        ) : isLoading ? (
          <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
        ) : data ? (
          <StatementTable statement={data} />
        ) : null}
      </div>
    </div>
  );
}
