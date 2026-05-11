"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Line,
  Legend,
  ReferenceLine,
} from "recharts";
import {
  startOfWeek,
  startOfMonth,
  endOfMonth,
  subDays,
  subWeeks,
  format,
} from "date-fns";
import {
  AlertTriangle,
  ArrowRightLeft,
  Clock,
  TrendingDown,
  TrendingUp,
  GitMerge,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { analyticsApi } from "@/lib/api/analytics";
import { formatAmount } from "@/lib/formatters";
import { useFiltersStore } from "@/store/filters";
import type { CompanyCashPosition, WeeklyCashFlow } from "@/types/api";

// ── Compact amount formatter for chart axes ────────────────────────────────
function compactEur(value: number): string {
  if (Math.abs(value) >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M€`;
  if (Math.abs(value) >= 1_000) return `${(value / 1_000).toFixed(0)}k€`;
  return `${value}€`;
}

// ── Quick date-range presets ──────────────────────────────────────────────
const PRESETS = [
  {
    label: "7 días",
    apply: () => ({ from: subDays(new Date(), 7), to: new Date() }),
  },
  {
    label: "30 días",
    apply: () => ({ from: subDays(new Date(), 30), to: new Date() }),
  },
  {
    label: "Mes actual",
    apply: () => ({ from: startOfMonth(new Date()), to: endOfMonth(new Date()) }),
  },
  {
    label: "13 semanas",
    apply: () => ({ from: subWeeks(new Date(), 13), to: new Date() }),
  },
] as const;

// ── KPI card ──────────────────────────────────────────────────────────────
function KpiCard({
  title,
  value,
  subtitle,
  positive,
  icon: Icon,
  href,
}: {
  title: string;
  value: string;
  subtitle: string;
  positive?: boolean;
  icon: React.ComponentType<{ className?: string }>;
  href?: string;
}) {
  const content = (
    <div className="rounded-lg border bg-card p-4 flex flex-col gap-1 hover:shadow-sm transition-shadow">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {title}
        </span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div
        className={cn(
          "text-2xl font-bold font-mono tracking-tight",
          positive === true && "text-emerald-600",
          positive === false && "text-red-500",
          positive === undefined && "text-foreground"
        )}
      >
        {value}
      </div>
      <div className="text-xs text-muted-foreground">{subtitle}</div>
    </div>
  );
  return href ? <Link href={href}>{content}</Link> : content;
}

// ── Cash position bar chart ───────────────────────────────────────────────
function CashPositionChart({ data }: { data: CompanyCashPosition[] }) {
  const chartData = data.map((c) => ({
    name: c.short_name,
    value: c.has_balance_data
      ? parseFloat(c.last_balance ?? "0")
      : parseFloat(c.net_flow),
    isEstimate: !c.has_balance_data,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(160, chartData.length * 44)}>
      <BarChart
        layout="vertical"
        data={chartData}
        margin={{ top: 4, right: 24, bottom: 4, left: 8 }}
      >
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
        <XAxis
          type="number"
          tickFormatter={compactEur}
          tick={{ fontSize: 11, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          dataKey="name"
          type="category"
          width={72}
          tick={{ fontSize: 12, fill: "#1e293b", fontWeight: 500 }}
          axisLine={false}
          tickLine={false}
        />
        <ReferenceLine x={0} stroke="#94a3b8" strokeWidth={1} />
        <Tooltip
          formatter={(val: number, _name, props) => [
            formatAmount(val),
            props.payload.isEstimate ? "Flujo neto (sin saldo)" : "Saldo actual",
          ]}
          contentStyle={{
            fontSize: 12,
            border: "1px solid #e2e8f0",
            borderRadius: 6,
          }}
        />
        <Bar
          dataKey="value"
          radius={[0, 3, 3, 0]}
          fill="#3b82f6"
          // Colour bars red if negative
          label={false}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── 13-week cash flow chart ───────────────────────────────────────────────
function WeeklyCashFlowChart({ data }: { data: WeeklyCashFlow[] }) {
  const chartData = data.map((w) => ({
    label: w.week_label,
    inflow: parseFloat(w.inflow),
    outflow: parseFloat(w.outflow),   // negative numbers
    net: parseFloat(w.net),
  }));

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={chartData} margin={{ top: 4, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 10, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={compactEur}
          tick={{ fontSize: 11, fill: "#64748b" }}
          axisLine={false}
          tickLine={false}
        />
        <ReferenceLine y={0} stroke="#94a3b8" strokeWidth={1} />
        <Tooltip
          formatter={(val: number, name: string) => [
            formatAmount(val),
            name === "inflow" ? "Entradas" : name === "outflow" ? "Salidas" : "Neto",
          ]}
          contentStyle={{
            fontSize: 12,
            border: "1px solid #e2e8f0",
            borderRadius: 6,
          }}
        />
        <Legend
          formatter={(value) =>
            value === "inflow" ? "Entradas" : value === "outflow" ? "Salidas" : "Neto"
          }
          wrapperStyle={{ fontSize: 12 }}
        />
        <Bar dataKey="inflow" fill="#10b981" opacity={0.85} radius={[2, 2, 0, 0]} />
        <Bar dataKey="outflow" fill="#ef4444" opacity={0.85} radius={[2, 2, 0, 0]} />
        <Line
          type="monotone"
          dataKey="net"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ r: 3, fill: "#3b82f6" }}
          activeDot={{ r: 5 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ── Skeleton loader ───────────────────────────────────────────────────────
function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse bg-muted rounded", className)} />;
}

// ── Main page ─────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { dateRange, setDateRange, reset } = useFiltersStore();

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["dashboard"],
    queryFn: analyticsApi.dashboard,
    staleTime: 60 * 1000,
  });

  // Determine current active preset
  const activePreset = (() => {
    const from = dateRange.from.getTime();
    const to = dateRange.to.getTime();
    const now = new Date();
    if (Math.abs(from - subDays(now, 7).getTime()) < 60_000) return "7 días";
    if (Math.abs(from - subDays(now, 30).getTime()) < 60_000) return "30 días";
    if (Math.abs(from - startOfMonth(now).getTime()) < 60_000) return "Mes actual";
    if (Math.abs(from - subWeeks(now, 13).getTime()) < 60_000) return "13 semanas";
    return null;
  })();

  const totalCash = data ? parseFloat(data.total_cash) : 0;
  const netWtd = data ? parseFloat(data.net_flow_wtd) : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Dashboard</h1>
          {data && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Datos a {format(new Date(data.as_of), "dd/MM/yyyy")}
            </p>
          )}
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", isFetching && "animate-spin")} />
          Actualizar
        </button>
      </div>

      {/* Quick date filters */}
      <div className="flex items-center gap-2 flex-wrap">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            onClick={() => setDateRange(p.apply())}
            className={cn(
              "px-3 py-1.5 rounded-md text-xs font-medium border transition-colors",
              activePreset === p.label
                ? "bg-primary text-primary-foreground border-primary"
                : "bg-background text-muted-foreground border-input hover:bg-muted hover:text-foreground"
            )}
          >
            {p.label}
          </button>
        ))}
        <button
          onClick={reset}
          className="px-3 py-1.5 rounded-md text-xs border border-input text-muted-foreground hover:bg-muted transition-colors"
        >
          Reset
        </button>
        <span className="text-xs text-muted-foreground ml-2">
          {format(dateRange.from, "dd/MM/yyyy")} → {format(dateRange.to, "dd/MM/yyyy")}
        </span>
      </div>

      {/* Error state */}
      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          No se pudo cargar el dashboard. Verifica que el backend está corriendo.
        </div>
      )}

      {/* Consistency alert banner */}
      {data && data.unresolved_ic > 0 && (
        <div className="flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50/60 dark:bg-amber-950/20 px-4 py-2.5 text-sm">
          <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>
              Hay <strong>{data.unresolved_ic}</strong> transferencia{data.unresolved_ic > 1 ? "s" : ""} intercompany sin resolver que pueden afectar la posición de caja.
            </span>
          </div>
          <Link href="/settings" className="ml-4 shrink-0 text-xs font-medium text-amber-700 dark:text-amber-400 hover:underline">
            Verificar integridad →
          </Link>
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))
        ) : (
          <>
            <KpiCard
              title="Posición de caja"
              value={data ? formatAmount(totalCash) : "—"}
              subtitle="Consolidado"
              positive={totalCash >= 0}
              icon={totalCash >= 0 ? TrendingUp : TrendingDown}
            />
            <KpiCard
              title="Flujo neto (semana)"
              value={data ? formatAmount(netWtd) : "—"}
              subtitle="Lunes a hoy"
              positive={netWtd >= 0}
              icon={netWtd >= 0 ? TrendingUp : TrendingDown}
            />
            <KpiCard
              title="Intercompany pendiente"
              value={data ? String(data.pending_ic_matches) : "—"}
              subtitle={
                data
                  ? `${data.in_transit_ic} en tránsito · ${data.unresolved_ic} sin resolver`
                  : "—"
              }
              positive={data?.pending_ic_matches === 0}
              icon={GitMerge}
              href="/intercompany"
            />
            <KpiCard
              title="En tránsito / Sin resolver"
              value={data ? String(data.in_transit_ic + data.unresolved_ic) : "—"}
              subtitle="Movimientos IC abiertos"
              positive={(data?.in_transit_ic ?? 1) + (data?.unresolved_ic ?? 1) === 0}
              icon={data?.unresolved_ic ? AlertTriangle : Clock}
              href="/intercompany"
            />
          </>
        )}
      </div>

      {/* Cash position by company + IC alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Cash position chart */}
        <div className="lg:col-span-2 rounded-lg border bg-card p-5">
          <h2 className="text-sm font-semibold text-foreground mb-4">
            Posición de caja por empresa
            {data && data.cash_by_company.some((c) => !c.has_balance_data) && (
              <span className="ml-2 text-xs font-normal text-amber-600">
                * algunas empresas sin saldo — se muestra flujo neto
              </span>
            )}
          </h2>
          {isLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : data?.cash_by_company.length ? (
            <CashPositionChart data={data.cash_by_company} />
          ) : (
            <p className="text-sm text-muted-foreground py-8 text-center">
              Sin datos — importa movimientos para ver la posición de caja.
            </p>
          )}
        </div>

        {/* Intercompany alerts widget */}
        <div className="rounded-lg border bg-card p-5 flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-foreground">
            Alertas intercompany
          </h2>
          {isLoading ? (
            <Skeleton className="h-32 w-full" />
          ) : (
            <>
              {/* Pending proposed */}
              <div
                className={cn(
                  "flex items-center justify-between rounded-md px-3 py-2.5 text-sm",
                  (data?.pending_ic_matches ?? 0) > 0
                    ? "bg-amber-50 border border-amber-200"
                    : "bg-muted"
                )}
              >
                <div className="flex items-center gap-2">
                  <ArrowRightLeft className="h-4 w-4 text-amber-600" />
                  <span>Pendientes de confirmar</span>
                </div>
                <span className="font-mono font-bold text-amber-700">
                  {data?.pending_ic_matches ?? 0}
                </span>
              </div>

              {/* In transit */}
              <div
                className={cn(
                  "flex items-center justify-between rounded-md px-3 py-2.5 text-sm",
                  (data?.in_transit_ic ?? 0) > 0
                    ? "bg-blue-50 border border-blue-200"
                    : "bg-muted"
                )}
              >
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-blue-600" />
                  <span>En tránsito</span>
                </div>
                <span className="font-mono font-bold text-blue-700">
                  {data?.in_transit_ic ?? 0}
                </span>
              </div>

              {/* Unresolved */}
              <div
                className={cn(
                  "flex items-center justify-between rounded-md px-3 py-2.5 text-sm",
                  (data?.unresolved_ic ?? 0) > 0
                    ? "bg-red-50 border border-red-200"
                    : "bg-muted"
                )}
              >
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                  <span>Sin resolver</span>
                </div>
                <span className="font-mono font-bold text-red-600">
                  {data?.unresolved_ic ?? 0}
                </span>
              </div>

              <Link
                href="/intercompany"
                className="mt-auto text-center text-xs text-primary hover:underline font-medium"
              >
                Ir a revisión intercompany →
              </Link>
            </>
          )}
        </div>
      </div>

      {/* 13-week cash flow chart */}
      <div className="rounded-lg border bg-card p-5">
        <h2 className="text-sm font-semibold text-foreground mb-4">
          Flujo de caja — últimas 13 semanas (reales)
        </h2>
        {isLoading ? (
          <Skeleton className="h-60 w-full" />
        ) : data?.weekly_cash_flow.length ? (
          <WeeklyCashFlowChart data={data.weekly_cash_flow} />
        ) : (
          <p className="text-sm text-muted-foreground py-12 text-center">
            Sin datos — importa movimientos para ver el flujo semanal.
          </p>
        )}
        <p className="text-xs text-muted-foreground mt-3">
          Fase 1 — solo actuals. La previsión oficial y la previsión IA se añaden en Fase 2.
        </p>
      </div>
    </div>
  );
}
