"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format, subWeeks } from "date-fns";
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Download, RefreshCw, TrendingDown, TrendingUp, Wand2 } from "lucide-react";

import { analyticsApi, type CashFlowFilters } from "@/lib/api/analytics";
import { companiesApi } from "@/lib/api/companies";
import { formatAmount } from "@/lib/formatters";
import { cn } from "@/lib/utils";

function compactEur(value: number): string {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M EUR`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(0)}k EUR`;
  return `${value} EUR`;
}

function toNumber(value: string | number | null | undefined) {
  return Number(value ?? 0);
}

function MetricCard({
  label,
  value,
  subtitle,
  positive,
}: {
  label: string;
  value: string;
  subtitle: string;
  positive?: boolean;
}) {
  const Icon = positive === false ? TrendingDown : TrendingUp;
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-medium uppercase text-muted-foreground">{label}</span>
        <Icon className={cn("h-4 w-4", positive === false ? "text-red-500" : "text-emerald-600")} />
      </div>
      <div
        className={cn(
          "mt-2 text-2xl font-semibold tabular-nums",
          positive === false ? "text-red-600" : "text-foreground",
        )}
      >
        {value}
      </div>
      <div className="mt-1 text-xs text-muted-foreground">{subtitle}</div>
    </div>
  );
}

export default function ForecastPage() {
  const [companyId, setCompanyId] = useState("");
  const [includeIntercompany, setIncludeIntercompany] = useState(false);
  const [scenario, setScenario] = useState<"base" | "downside" | "upside">("base");

  const dateFrom = format(subWeeks(new Date(), 13), "yyyy-MM-dd");
  const dateTo = format(new Date(), "yyyy-MM-dd");

  const { data: companies = [] } = useQuery({
    queryKey: ["companies"],
    queryFn: companiesApi.list,
    staleTime: 5 * 60_000,
  });

  const filters = useMemo<CashFlowFilters>(
    () => ({
      granularity: "weekly",
      date_from: dateFrom,
      date_to: dateTo,
      company_id: companyId || undefined,
      include_intercompany: includeIntercompany,
    }),
    [companyId, dateFrom, dateTo, includeIntercompany],
  );

  const {
    data: statement,
    isLoading,
    isError,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["forecast-cashflow", filters],
    queryFn: () => analyticsApi.cashflow(filters),
  });

  const chartData = useMemo(() => {
    if (!statement) return [];
    const actuals = statement.periods.map((period, index) => ({
      label: period.label,
      actual: toNumber(statement.net_cash_flow[index]),
      projected: null as number | null,
      balance: null as number | null,
    }));

    const netValues = actuals.map((row) => row.actual);
    const recent = netValues.slice(-6);
    const avg = recent.length ? recent.reduce((sum, value) => sum + value, 0) / recent.length : 0;
    const factor = scenario === "downside" ? 0.75 : scenario === "upside" ? 1.2 : 1;
    let running = netValues.reduce((sum, value) => sum + value, 0);

    const projected = Array.from({ length: 13 }, (_, index) => {
      const projectedNet = avg * factor;
      running += projectedNet;
      return {
        label: `F+${index + 1}`,
        actual: null as number | null,
        projected: projectedNet,
        balance: running,
      };
    });

    return [...actuals, ...projected];
  }, [scenario, statement]);

  const totalActual = toNumber(statement?.net_cash_flow_total);
  const projectedTotal = chartData.reduce((sum, row) => sum + (row.projected ?? 0), 0);
  const projectedClosing = chartData.length ? chartData[chartData.length - 1].balance ?? totalActual : totalActual;
  const worstWeek = chartData.reduce<number | null>((min, row) => {
    const value = row.actual ?? row.projected;
    if (value === null) return min;
    return min === null ? value : Math.min(min, value);
  }, null);

  function handleExport() {
    window.open(analyticsApi.cashflowExportUrl(filters), "_blank");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-foreground">13-Week Forecast</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Actual cash flow plus a rolling baseline projection.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors hover:bg-muted disabled:opacity-50"
            >
              <RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />
              Refresh
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors hover:bg-muted"
            >
              <Download className="h-4 w-4" />
              Export actuals
            </button>
          </div>
        </div>
      </div>

      <div className="border-b px-6 py-3">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={companyId}
            onChange={(event) => setCompanyId(event.target.value)}
            className="rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Consolidated group</option>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>
                {company.short_name}
              </option>
            ))}
          </select>

          <div className="inline-flex rounded-md border p-0.5">
            {(["base", "downside", "upside"] as const).map((option) => (
              <button
                key={option}
                onClick={() => setScenario(option)}
                className={cn(
                  "rounded px-3 py-1.5 text-sm font-medium capitalize transition-colors",
                  scenario === option
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {option}
              </button>
            ))}
          </div>

          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={includeIntercompany}
              onChange={(event) => setIncludeIntercompany(event.target.checked)}
              className="h-4 w-4 rounded border-input"
            />
            Include intercompany
          </label>

          {isFetching && <span className="text-xs text-muted-foreground">Loading...</span>}
        </div>
      </div>

      <div className="space-y-6 overflow-auto p-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <MetricCard
            label="Actual net"
            value={formatAmount(totalActual)}
            subtitle="Trailing 13 weeks"
            positive={totalActual >= 0}
          />
          <MetricCard
            label="Forecast net"
            value={formatAmount(projectedTotal)}
            subtitle={`${scenario} scenario`}
            positive={projectedTotal >= 0}
          />
          <MetricCard
            label="Projected close"
            value={formatAmount(projectedClosing)}
            subtitle="Actual cumulative plus projection"
            positive={projectedClosing >= 0}
          />
          <MetricCard
            label="Lowest week"
            value={formatAmount(worstWeek ?? 0)}
            subtitle="Actual and projected"
            positive={(worstWeek ?? 0) >= 0}
          />
        </div>

        <section className="rounded-lg border bg-card p-5">
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Weekly cash flow outlook</h2>
              <p className="mt-0.5 text-xs text-muted-foreground">
                Solid bars are actuals; projected bars use the recent weekly average.
              </p>
            </div>
            <Wand2 className="h-5 w-5 text-muted-foreground" />
          </div>

          {isError ? (
            <div className="p-8 text-center text-sm text-destructive">
              Could not load forecast inputs. Check the API connection.
            </div>
          ) : isLoading ? (
            <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
          ) : chartData.length === 0 ? (
            <div className="p-12 text-center text-sm text-muted-foreground">
              No cash-flow data found for the selected filters.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={360}>
              <ComposedChart data={chartData} margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={compactEur} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <ReferenceLine y={0} stroke="#94a3b8" />
                <Tooltip
                  formatter={(value: number, name: string) => [
                    formatAmount(value),
                    name === "actual" ? "Actual net" : name === "projected" ? "Projected net" : "Projected close",
                  ]}
                  contentStyle={{ fontSize: 12, border: "1px solid #e2e8f0", borderRadius: 6 }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="actual" name="Actual net" fill="#2563eb" radius={[2, 2, 0, 0]} />
                <Bar dataKey="projected" name="Projected net" fill="#14b8a6" radius={[2, 2, 0, 0]} />
                <Area
                  type="monotone"
                  dataKey="balance"
                  name="Projected close"
                  fill="#dbeafe"
                  stroke="#1d4ed8"
                  fillOpacity={0.35}
                  connectNulls
                />
                <Line type="monotone" dataKey="balance" name="Projected close line" stroke="#1d4ed8" dot={false} connectNulls />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </section>

        {statement && (
          <section className="rounded-lg border bg-card">
            <div className="border-b px-4 py-3">
              <h2 className="text-sm font-semibold text-foreground">Actual cash-flow sections</h2>
            </div>
            <div className="overflow-auto">
              <table className="w-full border-collapse text-sm">
                <thead className="bg-muted/80">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase text-muted-foreground">Section</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase text-muted-foreground">Total</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase text-muted-foreground">Avg / week</th>
                  </tr>
                </thead>
                <tbody>
                  {statement.sections.map((section) => {
                    const total = toNumber(section.total);
                    const average = statement.periods.length ? total / statement.periods.length : 0;
                    return (
                      <tr key={section.section} className="border-t hover:bg-muted/30">
                        <td className="px-3 py-2 font-medium">{section.section}</td>
                        <td className={cn("px-3 py-2 text-right tabular-nums", total < 0 ? "text-red-600" : "text-emerald-700")}>
                          {formatAmount(total)}
                        </td>
                        <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                          {formatAmount(average)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
