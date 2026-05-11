"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { analyticsApi } from "@/lib/api/analytics";
import { formatAmount, formatDate } from "@/lib/formatters";
import type {
  AccountImportStatus,
  BalanceReconciliation,
  DataQualityWarning,
  UnclassifiedRateWarning,
  ImportCoverageStatus,
} from "@/types/api";

// ── Period helpers ─────────────────────────────────────────────────────────

const MONTHS_ES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

function buildPeriodOptions(): { label: string; year: number; month: number }[] {
  const now = new Date();
  const options = [];
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    options.push({ label: `${MONTHS_ES[d.getMonth()]} ${d.getFullYear()}`, year: d.getFullYear(), month: d.getMonth() + 1 });
  }
  return options;
}

// ── Status icons / badges ─────────────────────────────────────────────────

function ImportStatusBadge({ status }: { status: ImportCoverageStatus }) {
  if (status === "OK")
    return (
      <span className="inline-flex items-center gap-1 text-emerald-600 font-medium text-sm">
        <CheckCircle2 className="w-4 h-4" /> Completo
      </span>
    );
  if (status === "PARTIAL")
    return (
      <span className="inline-flex items-center gap-1 text-amber-500 font-medium text-sm">
        <AlertTriangle className="w-4 h-4" /> Parcial
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-red-500 font-medium text-sm">
      <XCircle className="w-4 h-4" /> Sin importar
    </span>
  );
}

function ReconStatusBadge({ status }: { status: string }) {
  if (status === "OK")
    return (
      <span className="inline-flex items-center gap-1 text-emerald-600 font-medium text-sm">
        <CheckCircle2 className="w-4 h-4" /> OK
      </span>
    );
  if (status === "WARNING")
    return (
      <span className="inline-flex items-center gap-1 text-amber-500 font-medium text-sm">
        <AlertTriangle className="w-4 h-4" /> Revisar
      </span>
    );
  if (status === "ERROR")
    return (
      <span className="inline-flex items-center gap-1 text-red-500 font-medium text-sm">
        <XCircle className="w-4 h-4" /> Error
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-muted-foreground text-sm">
      <HelpCircle className="w-4 h-4" /> Sin datos
    </span>
  );
}

// ── Collapsible section wrapper ───────────────────────────────────────────

function Section({
  title,
  subtitle,
  badge,
  children,
  defaultOpen = true,
}: {
  title: string;
  subtitle: string;
  badge?: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 bg-muted/30 hover:bg-muted/50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          {open ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
          <div>
            <div className="font-semibold text-foreground">{title}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{subtitle}</div>
          </div>
        </div>
        {badge && <div className="ml-4 shrink-0">{badge}</div>}
      </button>
      {open && <div className="overflow-x-auto">{children}</div>}
    </div>
  );
}

// ── Section A table ───────────────────────────────────────────────────────

function SectionA({ rows }: { rows: AccountImportStatus[] }) {
  const missing = rows.filter((r) => r.status === "MISSING").length;
  const partial = rows.filter((r) => r.status === "PARTIAL").length;

  const badge =
    missing > 0 ? (
      <span className="text-sm text-red-500 font-medium">{missing} sin importar</span>
    ) : partial > 0 ? (
      <span className="text-sm text-amber-500 font-medium">{partial} parciales</span>
    ) : (
      <span className="text-sm text-emerald-600 font-medium">Todas completas</span>
    );

  return (
    <Section title="A — Cobertura de importación" subtitle="¿Se han importado todos los extractos del período seleccionado?" badge={badge}>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/20 text-muted-foreground text-xs uppercase tracking-wide">
            <th className="px-4 py-2 text-left">Empresa</th>
            <th className="px-4 py-2 text-left">Cuenta</th>
            <th className="px-4 py-2 text-left">Banco</th>
            <th className="px-4 py-2 text-left">IBAN</th>
            <th className="px-4 py-2 text-right">Movimientos</th>
            <th className="px-4 py-2 text-left">Primer registro</th>
            <th className="px-4 py-2 text-left">Último registro</th>
            <th className="px-4 py-2 text-left">Último fichero</th>
            <th className="px-4 py-2 text-left">Estado</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.bank_account_id}
              className={cn(
                "border-b border-border last:border-0 hover:bg-muted/20 transition-colors",
                row.status === "MISSING" && "bg-red-50/40 dark:bg-red-950/20",
                row.status === "PARTIAL" && "bg-amber-50/40 dark:bg-amber-950/20"
              )}
            >
              <td className="px-4 py-2.5 font-medium">{row.short_name}</td>
              <td className="px-4 py-2.5 text-muted-foreground">{row.account_name}</td>
              <td className="px-4 py-2.5">{row.bank_name}</td>
              <td className="px-4 py-2.5 font-mono text-xs">···{row.iban_last4}</td>
              <td className="px-4 py-2.5 text-right tabular-nums">
                {row.movement_count > 0 ? row.movement_count.toLocaleString("es-ES") : "—"}
              </td>
              <td className="px-4 py-2.5 tabular-nums text-sm">
                {row.earliest_movement ? formatDate(row.earliest_movement) : "—"}
              </td>
              <td className="px-4 py-2.5 tabular-nums text-sm">
                {row.latest_movement ? formatDate(row.latest_movement) : "—"}
              </td>
              <td className="px-4 py-2.5 tabular-nums text-xs text-muted-foreground">
                {row.last_batch_at ? formatDate(row.last_batch_at) : "—"}
              </td>
              <td className="px-4 py-2.5">
                <ImportStatusBadge status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Section>
  );
}

// ── Section B table ───────────────────────────────────────────────────────

function SectionB({ rows }: { rows: BalanceReconciliation[] }) {
  const errors = rows.filter((r) => r.status === "ERROR").length;
  const warnings = rows.filter((r) => r.status === "WARNING").length;
  const noData = rows.filter((r) => r.status === "NO_DATA").length;

  const badge =
    rows.length === 0 ? (
      <span className="text-sm text-muted-foreground">Sin datos de saldo</span>
    ) : errors > 0 ? (
      <span className="text-sm text-red-500 font-medium">{errors} discrepancia{errors > 1 ? "s" : ""}</span>
    ) : warnings > 0 ? (
      <span className="text-sm text-amber-500 font-medium">{warnings} para revisar</span>
    ) : noData === rows.length ? (
      <span className="text-sm text-muted-foreground">Sin saldos exportados</span>
    ) : (
      <span className="text-sm text-emerald-600 font-medium">Cuadrado</span>
    );

  return (
    <Section title="B — Conciliación de saldos" subtitle="¿El saldo computado coincide con el saldo reportado por el banco?" badge={badge} defaultOpen={errors > 0 || warnings > 0}>
      {rows.length === 0 ? (
        <p className="px-5 py-6 text-sm text-muted-foreground">
          Ningún banco ha exportado columna de saldo en el período seleccionado.
        </p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/20 text-muted-foreground text-xs uppercase tracking-wide">
              <th className="px-4 py-2 text-left">Empresa</th>
              <th className="px-4 py-2 text-left">Cuenta</th>
              <th className="px-4 py-2 text-right">Saldo inicial</th>
              <th className="px-4 py-2 text-right">Saldo cierre (banco)</th>
              <th className="px-4 py-2 text-right">Saldo cierre (calculado)</th>
              <th className="px-4 py-2 text-right">Diferencia</th>
              <th className="px-4 py-2 text-left">Estado</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.bank_account_id}
                className={cn(
                  "border-b border-border last:border-0 hover:bg-muted/20 transition-colors",
                  row.status === "ERROR" && "bg-red-50/40 dark:bg-red-950/20",
                  row.status === "WARNING" && "bg-amber-50/40 dark:bg-amber-950/20"
                )}
              >
                <td className="px-4 py-2.5 font-medium">{row.company_name}</td>
                <td className="px-4 py-2.5 text-muted-foreground">{row.account_name}</td>
                <td className="px-4 py-2.5 text-right tabular-nums">
                  {row.opening_balance != null ? formatAmount(row.opening_balance) : "—"}
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums">
                  {row.closing_balance_bank != null ? formatAmount(row.closing_balance_bank) : "—"}
                </td>
                <td className="px-4 py-2.5 text-right tabular-nums">
                  {row.closing_balance_computed != null ? formatAmount(row.closing_balance_computed) : "—"}
                </td>
                <td
                  className={cn(
                    "px-4 py-2.5 text-right tabular-nums font-medium",
                    row.status === "ERROR" && "text-red-600",
                    row.status === "WARNING" && "text-amber-600"
                  )}
                >
                  {row.delta != null ? formatAmount(row.delta) : "—"}
                </td>
                <td className="px-4 py-2.5">
                  <ReconStatusBadge status={row.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Section>
  );
}

// ── Section C ─────────────────────────────────────────────────────────────

function SectionC({
  holdcoWarnings,
  highUnclassified,
  unresolvedIcCount,
  inTransitTimeoutCount,
}: {
  holdcoWarnings: DataQualityWarning[];
  highUnclassified: UnclassifiedRateWarning[];
  unresolvedIcCount: number;
  inTransitTimeoutCount: number;
}) {
  const totalIssues =
    holdcoWarnings.length + highUnclassified.length + (unresolvedIcCount > 0 ? 1 : 0) + (inTransitTimeoutCount > 0 ? 1 : 0);

  const badge =
    totalIssues === 0 ? (
      <span className="text-sm text-emerald-600 font-medium">Sin incidencias</span>
    ) : (
      <span className="text-sm text-amber-500 font-medium">{totalIssues} incidencia{totalIssues > 1 ? "s" : ""}</span>
    );

  return (
    <Section title="C — Calidad de datos" subtitle="Reglas de negocio que pueden indicar clasificaciones incorrectas o transferencias sin resolver" badge={badge} defaultOpen={totalIssues > 0}>
      <div className="divide-y divide-border">
        {/* IC warnings */}
        {(unresolvedIcCount > 0 || inTransitTimeoutCount > 0) && (
          <div className="px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">Intercompany</p>
            <div className="flex flex-col gap-2">
              {unresolvedIcCount > 0 && (
                <div className="flex items-center justify-between rounded-md border border-red-200 bg-red-50/50 dark:bg-red-950/20 px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-medium">{unresolvedIcCount} transferencia{unresolvedIcCount > 1 ? "s" : ""} intercompany sin resolver</span>
                  </div>
                  <Link href="/intercompany" className="flex items-center gap-1 text-xs text-primary hover:underline">
                    Revisar <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              )}
              {inTransitTimeoutCount > 0 && (
                <div className="flex items-center justify-between rounded-md border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <span className="text-sm font-medium">{inTransitTimeoutCount} en tránsito caducado{inTransitTimeoutCount > 1 ? "s" : ""} (&gt;5 días hábiles)</span>
                  </div>
                  <Link href="/intercompany" className="flex items-center gap-1 text-xs text-primary hover:underline">
                    Revisar <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}

        {/* HoldCo revenue */}
        {holdcoWarnings.length > 0 && (
          <div className="px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">
              Ingresos en HoldCo — posible error de clasificación
            </p>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs uppercase tracking-wide border-b border-border">
                  <th className="pb-2 text-left">Empresa</th>
                  <th className="pb-2 text-left">Cuenta</th>
                  <th className="pb-2 text-left">Fecha</th>
                  <th className="pb-2 text-right">Importe</th>
                  <th className="pb-2 text-left">Descripción</th>
                  <th className="pb-2" />
                </tr>
              </thead>
              <tbody>
                {holdcoWarnings.map((w, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/20">
                    <td className="py-2 pr-4 font-medium">{w.company_name}</td>
                    <td className="py-2 pr-4 text-muted-foreground">{w.account_name ?? "—"}</td>
                    <td className="py-2 pr-4 tabular-nums">{w.movement_date ? formatDate(w.movement_date) : "—"}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-emerald-600">
                      {w.movement_amount != null ? formatAmount(w.movement_amount) : "—"}
                    </td>
                    <td className="py-2 pr-4 max-w-xs truncate text-muted-foreground">{w.description}</td>
                    <td className="py-2">
                      {w.movement_id && (
                        <Link
                          href={`/ledger?movement=${w.movement_id}`}
                          className="flex items-center gap-1 text-xs text-primary hover:underline"
                        >
                          Ver <ExternalLink className="w-3 h-3" />
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* High unclassified */}
        {highUnclassified.length > 0 && (
          <div className="px-5 py-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">
              Tasa de no clasificados &gt;15%
            </p>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs uppercase tracking-wide border-b border-border">
                  <th className="pb-2 text-left">Empresa</th>
                  <th className="pb-2 text-right">Total</th>
                  <th className="pb-2 text-right">Sin clasificar</th>
                  <th className="pb-2 text-right">Tasa</th>
                  <th className="pb-2" />
                </tr>
              </thead>
              <tbody>
                {highUnclassified.map((w, i) => (
                  <tr key={i} className="border-b border-border last:border-0 hover:bg-muted/20">
                    <td className="py-2 pr-4 font-medium">{w.company_name}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">{w.total_movements.toLocaleString("es-ES")}</td>
                    <td className="py-2 pr-4 text-right tabular-nums text-amber-600">{w.unclassified_count.toLocaleString("es-ES")}</td>
                    <td className="py-2 pr-4 text-right tabular-nums font-semibold text-amber-600">
                      {(w.unclassified_rate * 100).toFixed(1)}%
                    </td>
                    <td className="py-2">
                      <Link
                        href="/classification"
                        className="flex items-center gap-1 text-xs text-primary hover:underline"
                      >
                        Clasificar <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalIssues === 0 && (
          <div className="px-5 py-6 flex items-center gap-2 text-sm text-emerald-600">
            <CheckCircle2 className="w-5 h-5" />
            No se han detectado incidencias de calidad en el período seleccionado.
          </div>
        )}
      </div>
    </Section>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [queryKey, setQueryKey] = useState({ year, month });

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["consistency", queryKey.year, queryKey.month],
    queryFn: () => analyticsApi.consistency(queryKey.year, queryKey.month),
  });

  const periodOptions = buildPeriodOptions();

  const selectedPeriod = periodOptions.find((o) => o.year === year && o.month === month) ?? periodOptions[0];

  function runCheck() {
    setQueryKey({ year, month });
  }

  return (
    <div className="p-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Verificación de integridad</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Comprueba que los extractos del período estén completos y que los datos sean consistentes antes de leer los analytics.
          </p>
        </div>
      </div>

      {/* Period selector */}
      <div className="flex items-center gap-3 mb-6 p-4 border border-border rounded-lg bg-muted/20">
        <span className="text-sm font-medium text-foreground">Período:</span>
        <select
          value={`${year}-${month}`}
          onChange={(e) => {
            const [y, m] = e.target.value.split("-").map(Number);
            setYear(y);
            setMonth(m);
          }}
          className="border border-border rounded-md px-3 py-1.5 text-sm bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
        >
          {periodOptions.map((o) => (
            <option key={`${o.year}-${o.month}`} value={`${o.year}-${o.month}`}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={runCheck}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <RefreshCw className={cn("w-3.5 h-3.5", isLoading && "animate-spin")} />
          Verificar
        </button>
        {data && (
          <span className="text-xs text-muted-foreground ml-auto">
            Generado el {formatDate(data.as_of)} · Período: {data.period_label}
          </span>
        )}
      </div>

      {/* States */}
      {isError && (
        <div className="mb-4 flex items-center gap-2 rounded-md border border-red-300 bg-red-50/50 dark:bg-red-950/20 px-4 py-3 text-sm text-red-700 dark:text-red-400">
          <XCircle className="w-4 h-4 shrink-0" />
          No se pudo conectar con el servidor. Comprueba que el backend esté activo.
        </div>
      )}

      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 rounded-lg bg-muted/30 animate-pulse" />
          ))}
        </div>
      )}

      {/* Report */}
      {data && !isLoading && (
        <div className="space-y-4">
          <SectionA rows={data.section_a} />
          <SectionB rows={data.section_b} />
          <SectionC
            holdcoWarnings={data.holdco_revenue_warnings}
            highUnclassified={data.high_unclassified_companies}
            unresolvedIcCount={data.unresolved_ic_count}
            inTransitTimeoutCount={data.in_transit_timeout_count}
          />
        </div>
      )}

      {!data && !isLoading && !isError && (
        <div className="flex flex-col items-center justify-center py-16 text-muted-foreground text-sm">
          <RefreshCw className="w-8 h-8 mb-3 opacity-30" />
          Selecciona un período y pulsa <strong className="ml-1">Verificar</strong> para generar el informe.
        </div>
      )}
    </div>
  );
}
