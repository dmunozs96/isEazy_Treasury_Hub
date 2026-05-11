"use client";

import { useCallback, useEffect, useState } from "react";
import { GitMerge, RefreshCw, AlertTriangle, Clock, CheckCircle2, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  intercompanyScanApi,
  intercomparySummaryApi,
  matchesApi,
} from "@/lib/api/intercompany";
import type {
  CompanyPairSummary,
  IntercompanyMatch,
  IntercomparySummary,
  MatchStatus,
  ScanResponse,
} from "@/types/api";

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------

const STATUS_STYLES: Record<MatchStatus, string> = {
  IN_TRANSIT: "bg-yellow-100 text-yellow-800 border border-yellow-200",
  PROPOSED:   "bg-blue-100 text-blue-800 border border-blue-200",
  CONFIRMED:  "bg-green-100 text-green-800 border border-green-200",
  REJECTED:   "bg-red-100 text-red-800 border border-red-200",
  UNRESOLVED: "bg-orange-100 text-orange-800 border border-orange-200",
};

const STATUS_LABELS: Record<MatchStatus, string> = {
  IN_TRANSIT: "En tránsito",
  PROPOSED:   "Propuesto",
  CONFIRMED:  "Confirmado",
  REJECTED:   "Rechazado",
  UNRESOLVED: "Sin resolver",
};

function StatusBadge({ status }: { status: MatchStatus }) {
  return (
    <span className={cn("inline-flex items-center px-2 py-0.5 rounded text-xs font-medium", STATUS_STYLES[status])}>
      {STATUS_LABELS[status]}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Amount formatting
// ---------------------------------------------------------------------------

function fmt(amount: string | null | undefined): string {
  if (!amount) return "—";
  const n = parseFloat(amount);
  return new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR" }).format(n);
}

function fmtDate(d: string | null | undefined): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit", year: "numeric" });
}

// ---------------------------------------------------------------------------
// Match card (expand/collapse to show both legs)
// ---------------------------------------------------------------------------

function MatchCard({
  match,
  onConfirm,
  onReject,
  loading,
}: {
  match: IntercompanyMatch;
  onConfirm: (id: string) => void;
  onReject: (id: string) => void;
  loading: string | null;
}) {
  const [expanded, setExpanded] = useState(false);
  const isLoading = loading === match.id;
  const canAct = match.status === "PROPOSED" && match.movement_in_id !== null;
  const isInTransit = match.status === "IN_TRANSIT";
  const isUnresolved = match.status === "UNRESOLVED";

  return (
    <div
      className={cn(
        "border rounded-lg bg-card transition-colors",
        isUnresolved && "border-orange-300 bg-orange-50/40",
        isInTransit && "border-yellow-300",
        match.status === "CONFIRMED" && "border-green-200 bg-green-50/30",
      )}
    >
      {/* Header row */}
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm text-foreground">
              {match.company_from_name ?? "—"} → {match.company_to_name ?? "?"}
            </span>
            <StatusBadge status={match.status} />
            {match.match_method === "MANUAL" && (
              <span className="text-xs text-muted-foreground border rounded px-1.5 py-0.5">Manual</span>
            )}
          </div>
          <div className="mt-0.5 text-xs text-muted-foreground">
            {fmtDate(match.match_date)}
            {match.score !== null && (
              <span className="ml-2 text-muted-foreground/70">
                Score: {(parseFloat(match.score) * 100).toFixed(0)}%
              </span>
            )}
            {isInTransit && match.transit_expires_at && (
              <span className="ml-2 text-yellow-700">
                Expira: {fmtDate(match.transit_expires_at)}
              </span>
            )}
          </div>
        </div>

        <div className="text-right flex-shrink-0">
          <div className="text-sm font-semibold tabular-nums">{fmt(match.amount)}</div>
        </div>

        <div className="flex-shrink-0">
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t px-4 py-3 space-y-3">
          {/* Movement legs */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            {/* Out leg */}
            <div className="rounded-md border bg-red-50/50 p-2.5 space-y-1">
              <div className="font-semibold text-red-700 uppercase tracking-wide text-[10px]">Salida</div>
              {match.movement_out ? (
                <>
                  <div className="font-medium">{match.movement_out.company_short_name}</div>
                  <div className="text-muted-foreground truncate">{match.movement_out.description}</div>
                  <div className="font-mono text-red-600">{fmt(match.movement_out.amount)}</div>
                  <div className="text-muted-foreground">{fmtDate(match.movement_out.value_date)}</div>
                  {match.movement_out.counterpart_iban && (
                    <div className="text-muted-foreground/70 font-mono text-[10px] truncate">
                      {match.movement_out.counterpart_iban}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-muted-foreground italic">No disponible</div>
              )}
            </div>

            {/* In leg */}
            <div className="rounded-md border bg-green-50/50 p-2.5 space-y-1">
              <div className="font-semibold text-green-700 uppercase tracking-wide text-[10px]">Entrada</div>
              {match.movement_in ? (
                <>
                  <div className="font-medium">{match.movement_in.company_short_name}</div>
                  <div className="text-muted-foreground truncate">{match.movement_in.description}</div>
                  <div className="font-mono text-green-600">{fmt(match.movement_in.amount)}</div>
                  <div className="text-muted-foreground">{fmtDate(match.movement_in.value_date)}</div>
                  {match.movement_in.counterpart_iban && (
                    <div className="text-muted-foreground/70 font-mono text-[10px] truncate">
                      {match.movement_in.counterpart_iban}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-muted-foreground italic text-xs">
                  {isInTransit ? "Segundo apunte aún no importado" : "No disponible"}
                </div>
              )}
            </div>
          </div>

          {/* Notes / rejection reason */}
          {match.rejection_reason && (
            <div className="text-xs text-red-700 bg-red-50 rounded px-2 py-1.5">
              Motivo de rechazo: {match.rejection_reason}
            </div>
          )}
          {match.notes && (
            <div className="text-xs text-muted-foreground bg-muted rounded px-2 py-1.5">
              Notas: {match.notes}
            </div>
          )}
          {match.confirmed_by && (
            <div className="text-xs text-green-700">
              Confirmado por {match.confirmed_by} el {fmtDate(match.confirmed_at)}
            </div>
          )}

          {/* Action buttons */}
          {canAct && (
            <div className="flex gap-2 pt-1">
              <button
                onClick={(e) => { e.stopPropagation(); onConfirm(match.id); }}
                disabled={isLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                Confirmar
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); onReject(match.id); }}
                disabled={isLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-700 text-xs font-medium rounded hover:bg-red-200 disabled:opacity-50 transition-colors border border-red-200"
              >
                <XCircle className="h-3.5 w-3.5" />
                Rechazar
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Balance matrix table
// ---------------------------------------------------------------------------

function BalanceMatrix({ pairs }: { pairs: CompanyPairSummary[] }) {
  if (!pairs.length) {
    return (
      <p className="text-sm text-muted-foreground py-4 text-center">
        No hay transferencias intercompany confirmadas.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b text-left">
            <th className="py-2 pr-4 font-medium text-muted-foreground">Origen</th>
            <th className="py-2 pr-4 font-medium text-muted-foreground">Destino</th>
            <th className="py-2 pr-4 font-medium text-muted-foreground text-right">Salidas</th>
            <th className="py-2 pr-4 font-medium text-muted-foreground text-right">Entradas</th>
            <th className="py-2 font-medium text-muted-foreground text-right">Neto</th>
          </tr>
        </thead>
        <tbody>
          {pairs.map((p) => {
            const net = parseFloat(p.net);
            return (
              <tr key={`${p.company_from_id}-${p.company_to_id}`} className="border-b last:border-0 hover:bg-muted/30">
                <td className="py-2 pr-4 font-medium">{p.company_from_name ?? p.company_from_id}</td>
                <td className="py-2 pr-4 text-muted-foreground">{p.company_to_name ?? p.company_to_id}</td>
                <td className="py-2 pr-4 text-right tabular-nums text-red-600">{fmt(p.total_out)}</td>
                <td className="py-2 pr-4 text-right tabular-nums text-green-600">{fmt(p.total_in)}</td>
                <td className={cn("py-2 text-right tabular-nums font-semibold", net < 0 ? "text-red-600" : "text-green-600")}>
                  {fmt(p.net)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reject dialog (simple prompt)
// ---------------------------------------------------------------------------

function RejectDialog({
  matchId,
  onClose,
  onConfirm,
}: {
  matchId: string;
  onClose: () => void;
  onConfirm: (reason: string) => void;
}) {
  const [reason, setReason] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-card border rounded-xl shadow-xl p-6 w-full max-w-sm space-y-4">
        <h3 className="font-semibold text-foreground">Rechazar coincidencia</h3>
        <p className="text-sm text-muted-foreground">
          Indica el motivo del rechazo. No se volverá a proponer automáticamente este par.
        </p>
        <textarea
          className="w-full border rounded-md px-3 py-2 text-sm bg-background resize-none h-20 focus:outline-none focus:ring-2 focus:ring-primary/30"
          placeholder="Motivo de rechazo..."
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          autoFocus
        />
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-sm rounded border hover:bg-muted"
          >
            Cancelar
          </button>
          <button
            onClick={() => onConfirm(reason)}
            disabled={!reason.trim()}
            className="px-4 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
          >
            Rechazar
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

const STATUS_FILTER_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Todos" },
  { value: "PROPOSED", label: "Pendientes" },
  { value: "IN_TRANSIT", label: "En tránsito" },
  { value: "UNRESOLVED", label: "Sin resolver" },
  { value: "CONFIRMED", label: "Confirmados" },
  { value: "REJECTED", label: "Rechazados" },
];

export default function IntercompanyPage() {
  const [matches, setMatches] = useState<IntercompanyMatch[]>([]);
  const [summary, setSummary] = useState<IntercomparySummary | null>(null);
  const [statusFilter, setStatusFilter] = useState("PROPOSED");
  const [loadingMatches, setLoadingMatches] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rejectTarget, setRejectTarget] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"matches" | "matrix">("matches");

  const loadMatches = useCallback(async () => {
    setLoadingMatches(true);
    setError(null);
    try {
      const data = await matchesApi.list(statusFilter ? { status: statusFilter } : {});
      setMatches(data);
    } catch {
      setError("Error cargando coincidencias. Asegúrate de que el backend esté activo.");
    } finally {
      setLoadingMatches(false);
    }
  }, [statusFilter]);

  const loadSummary = useCallback(async () => {
    setLoadingSummary(true);
    try {
      const data = await intercomparySummaryApi.get();
      setSummary(data);
    } catch {
      // Summary is optional, don't block UI
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  useEffect(() => {
    loadMatches();
  }, [loadMatches]);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const handleScan = async () => {
    setScanning(true);
    setScanResult(null);
    try {
      const result = await intercompanyScanApi.run();
      setScanResult(result);
      await loadMatches();
      await loadSummary();
    } catch {
      setError("Error ejecutando el escaneado.");
    } finally {
      setScanning(false);
    }
  };

  const handleConfirm = async (matchId: string) => {
    setActionLoading(matchId);
    try {
      await matchesApi.confirm(matchId);
      await loadMatches();
      await loadSummary();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al confirmar");
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (reason: string) => {
    if (!rejectTarget) return;
    setActionLoading(rejectTarget);
    setRejectTarget(null);
    try {
      await matchesApi.reject(rejectTarget, reason);
      await loadMatches();
      await loadSummary();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al rechazar");
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-5 border-b flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <GitMerge className="h-5 w-5 text-primary" />
            <h1 className="text-xl font-semibold text-foreground">Intercompany</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">
            Revisión y confirmación de transferencias entre entidades del grupo
          </p>
        </div>

        <button
          onClick={handleScan}
          disabled={scanning}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <RefreshCw className={cn("h-4 w-4", scanning && "animate-spin")} />
          {scanning ? "Escaneando…" : "Escanear"}
        </button>
      </div>

      {/* Scan result banner */}
      {scanResult && (
        <div className="mx-6 mt-4 px-4 py-3 rounded-lg bg-blue-50 border border-blue-200 text-sm text-blue-800">
          Escaneo completado —{" "}
          <span className="font-medium">{scanResult.new_proposed} nuevas propuestas</span>,{" "}
          {scanResult.new_transit} en tránsito,{" "}
          {scanResult.escalated} escalados a sin resolver.
          <button onClick={() => setScanResult(null)} className="ml-3 text-blue-500 hover:text-blue-700 text-xs underline">
            Cerrar
          </button>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="mx-6 mt-4 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600 text-xs underline">
            Cerrar
          </button>
        </div>
      )}

      {/* Status summary chips */}
      {summary && (
        <div className="px-6 pt-4 flex items-center gap-3 flex-wrap">
          {summary.pending_proposed > 0 && (
            <div className="flex items-center gap-1.5 text-xs bg-blue-50 border border-blue-200 text-blue-800 rounded-full px-3 py-1">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {summary.pending_proposed} pendientes de revisión
            </div>
          )}
          {summary.in_transit > 0 && (
            <div className="flex items-center gap-1.5 text-xs bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-full px-3 py-1">
              <Clock className="h-3.5 w-3.5" />
              {summary.in_transit} en tránsito
            </div>
          )}
          {summary.unresolved > 0 && (
            <div className="flex items-center gap-1.5 text-xs bg-orange-50 border border-orange-200 text-orange-800 rounded-full px-3 py-1">
              <AlertTriangle className="h-3.5 w-3.5" />
              {summary.unresolved} sin resolver — requieren investigación
            </div>
          )}
          {!summary.pending_proposed && !summary.in_transit && !summary.unresolved && (
            <div className="text-xs text-muted-foreground">Sin alertas pendientes</div>
          )}
        </div>
      )}

      {/* Tabs */}
      <div className="px-6 pt-4 flex gap-1 border-b">
        {(["matches", "matrix"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              activeTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {tab === "matches" ? "Coincidencias" : "Matriz de saldos"}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {activeTab === "matches" && (
          <div className="space-y-4">
            {/* Status filter */}
            <div className="flex items-center gap-2 flex-wrap">
              {STATUS_FILTER_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setStatusFilter(opt.value)}
                  className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium border transition-colors",
                    statusFilter === opt.value
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-card text-muted-foreground border-border hover:bg-muted"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* Match list */}
            {loadingMatches ? (
              <div className="py-12 text-center text-muted-foreground text-sm">Cargando…</div>
            ) : matches.length === 0 ? (
              <div className="py-12 text-center">
                <GitMerge className="mx-auto h-10 w-10 text-muted-foreground/40 mb-3" />
                <p className="text-sm text-muted-foreground">No hay coincidencias para este filtro.</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Usa &quot;Escanear&quot; para detectar nuevas transferencias intercompany.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {matches.map((m) => (
                  <MatchCard
                    key={m.id}
                    match={m}
                    onConfirm={handleConfirm}
                    onReject={(id) => setRejectTarget(id)}
                    loading={actionLoading}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "matrix" && (
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Saldos netos entre entidades del grupo basados en transferencias confirmadas.
            </p>
            {loadingSummary ? (
              <div className="py-8 text-center text-muted-foreground text-sm">Cargando…</div>
            ) : (
              <BalanceMatrix pairs={summary?.pairs ?? []} />
            )}
          </div>
        )}
      </div>

      {/* Reject dialog */}
      {rejectTarget && (
        <RejectDialog
          matchId={rejectTarget}
          onClose={() => setRejectTarget(null)}
          onConfirm={handleReject}
        />
      )}
    </div>
  );
}
