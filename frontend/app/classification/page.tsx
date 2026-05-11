"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, PlusCircle, Trash2, Zap } from "lucide-react";

import { batchClassifyApi, rulesApi, type RuleCreate } from "@/lib/api/classifications";
import { categoriesApi } from "@/lib/api/movements";
import type { BatchClassifyResponse, CashFlowSection, ClassificationRule, MatchType } from "@/types/api";

// ── Helpers ─────────────────────────────────────────────────────────────────

const SECTION_STYLE: Record<CashFlowSection, string> = {
  OPERATING:    "bg-blue-100 text-blue-800",
  INVESTING:    "bg-purple-100 text-purple-800",
  FINANCING:    "bg-orange-100 text-orange-800",
  INTERNAL:     "bg-slate-100 text-slate-700",
  UNCLASSIFIED: "bg-yellow-100 text-yellow-800",
};

const MATCH_TYPE_LABEL: Record<MatchType, string> = {
  KEYWORD:          "Palabra clave",
  REGEX:            "Expresión regular",
  COUNTERPART_NAME: "Nombre contraparte",
  AMOUNT_RANGE:     "Rango de importe",
  COMPOSITE:        "Compuesta",
};

const MATCH_FIELDS = ["description", "counterpart_name", "reference"];

// ── New-rule form ────────────────────────────────────────────────────────────

const EMPTY_FORM: RuleCreate = {
  name: "",
  priority: 100,
  match_type: "KEYWORD",
  match_field: "description",
  match_pattern: "",
  category_code: "",
};

function NewRuleForm({ onClose }: { onClose: () => void }) {
  const [form, setForm] = useState<RuleCreate>(EMPTY_FORM);
  const queryClient = useQueryClient();

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });

  // Only leaf categories (level 2 + UNCLASSIFIED)
  const leafCategories = categories.filter((c) => c.level === 2 || c.code === "UNCLASSIFIED");

  const create = useMutation({
    mutationFn: () => rulesApi.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rules"] });
      onClose();
    },
  });

  const set = (field: keyof RuleCreate, value: unknown) =>
    setForm((f) => ({ ...f, [field]: value }));

  return (
    <div className="border rounded-lg p-4 bg-muted/30 mb-6">
      <h3 className="font-semibold mb-4 text-sm">Nueva regla de clasificación</h3>
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="col-span-2 sm:col-span-1">
          <label className="text-xs font-medium text-muted-foreground block mb-1">Nombre *</label>
          <input
            className="w-full border rounded px-2 py-1.5 text-sm bg-background"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="Ej: Pago proveedores"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground block mb-1">Prioridad *</label>
          <input
            type="number"
            className="w-full border rounded px-2 py-1.5 text-sm bg-background"
            value={form.priority}
            onChange={(e) => set("priority", Number(e.target.value))}
            min={1}
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground block mb-1">Tipo de match *</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm bg-background"
            value={form.match_type}
            onChange={(e) => set("match_type", e.target.value as MatchType)}
          >
            {(Object.keys(MATCH_TYPE_LABEL) as MatchType[]).map((t) => (
              <option key={t} value={t}>{MATCH_TYPE_LABEL[t]}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground block mb-1">Campo</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm bg-background"
            value={form.match_field}
            onChange={(e) => set("match_field", e.target.value)}
          >
            {MATCH_FIELDS.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground block mb-1">Patrón *</label>
          <input
            className="w-full border rounded px-2 py-1.5 text-sm bg-background font-mono"
            value={form.match_pattern}
            onChange={(e) => set("match_pattern", e.target.value)}
            placeholder="Ej: NOMINA"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground block mb-1">Categoría *</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm bg-background"
            value={form.category_code}
            onChange={(e) => set("category_code", e.target.value)}
          >
            <option value="">— seleccionar —</option>
            {leafCategories.map((c) => (
              <option key={c.code} value={c.code}>{c.code} — {c.name}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="flex gap-2 justify-end">
        <button
          className="px-3 py-1.5 text-sm border rounded hover:bg-muted"
          onClick={onClose}
        >
          Cancelar
        </button>
        <button
          className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:opacity-90 disabled:opacity-50"
          disabled={!form.name || !form.match_pattern || !form.category_code || create.isPending}
          onClick={() => create.mutate()}
        >
          {create.isPending ? "Creando…" : "Crear regla"}
        </button>
      </div>
      {create.isError && (
        <p className="text-xs text-red-600 mt-2">Error al crear la regla. Revisa los campos.</p>
      )}
    </div>
  );
}

// ── Rule row ─────────────────────────────────────────────────────────────────

function RuleRow({ rule, section }: { rule: ClassificationRule; section: CashFlowSection | undefined }) {
  const queryClient = useQueryClient();

  const toggle = useMutation({
    mutationFn: () => rulesApi.update(rule.id, { is_active: !rule.is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rules"] }),
  });

  const deactivate = useMutation({
    mutationFn: () => rulesApi.deactivate(rule.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rules"] }),
  });

  return (
    <tr className={`border-b hover:bg-muted/30 transition-colors ${!rule.is_active ? "opacity-40" : ""}`}>
      <td className="px-3 py-2 text-center tabular-nums text-sm font-medium w-16">{rule.priority}</td>
      <td className="px-3 py-2 text-sm">{rule.name}</td>
      <td className="px-3 py-2 text-xs text-muted-foreground whitespace-nowrap">
        {MATCH_TYPE_LABEL[rule.match_type]}
      </td>
      <td className="px-3 py-2 text-xs font-mono text-muted-foreground max-w-[180px] truncate">
        {rule.match_field}: <span className="text-foreground">{rule.match_pattern}</span>
      </td>
      <td className="px-3 py-2">
        <span className={`text-xs px-2 py-0.5 rounded font-mono ${section ? SECTION_STYLE[section] : "bg-yellow-100 text-yellow-800"}`}>
          {rule.category_code}
        </span>
      </td>
      <td className="px-3 py-2 text-center">
        <button
          onClick={() => toggle.mutate()}
          disabled={toggle.isPending}
          className="text-xs border rounded px-2 py-0.5 hover:bg-muted"
          title={rule.is_active ? "Desactivar" : "Activar"}
        >
          {rule.is_active ? "Activa" : "Inactiva"}
        </button>
      </td>
      <td className="px-3 py-2 text-center">
        <button
          onClick={() => {
            if (confirm(`¿Desactivar permanentemente la regla "${rule.name}"?`)) {
              deactivate.mutate();
            }
          }}
          disabled={deactivate.isPending}
          className="text-muted-foreground hover:text-red-600 transition-colors"
        >
          <Trash2 size={14} />
        </button>
      </td>
    </tr>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ClassificationPage() {
  const [showForm, setShowForm] = useState(false);
  const [batchResult, setBatchResult] = useState<BatchClassifyResponse | null>(null);
  const [showInactive, setShowInactive] = useState(false);

  const { data: rules = [], isLoading } = useQuery({
    queryKey: ["rules"],
    queryFn: () => rulesApi.list(),
  });

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.list(),
  });

  const categorySection = Object.fromEntries(
    categories.map((c) => [c.code, c.cash_flow_section])
  ) as Record<string, CashFlowSection>;

  const batchClassify = useMutation({
    mutationFn: () => batchClassifyApi.run({ force_reclassify: false }),
    onSuccess: (data) => setBatchResult(data),
  });

  const reclassifyAll = useMutation({
    mutationFn: () => batchClassifyApi.run({ force_reclassify: true }),
    onSuccess: (data) => setBatchResult(data),
  });

  const visibleRules = showInactive ? rules : rules.filter((r) => r.is_active);
  const activeCount = rules.filter((r) => r.is_active).length;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Motor de Clasificación</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {activeCount} reglas activas · ordenadas por prioridad (1 = mayor precedencia)
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              if (confirm("¿Reclasificar TODOS los movimientos? Las clasificaciones manuales se preservan.")) {
                setBatchResult(null);
                reclassifyAll.mutate();
              }
            }}
            disabled={reclassifyAll.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border rounded hover:bg-muted"
          >
            <Zap size={14} />
            {reclassifyAll.isPending ? "Procesando…" : "Reclasificar todo"}
          </button>
          <button
            onClick={() => {
              setBatchResult(null);
              batchClassify.mutate();
            }}
            disabled={batchClassify.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded hover:opacity-90"
          >
            <CheckCircle size={14} />
            {batchClassify.isPending ? "Clasificando…" : "Clasificar no clasificados"}
          </button>
        </div>
      </div>

      {/* Batch result banner */}
      {batchResult && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg text-sm">
          <p className="font-medium text-green-800 mb-1">Clasificación completada</p>
          <div className="flex gap-6 text-green-700">
            <span>Procesados: <strong>{batchResult.processed}</strong></span>
            <span>Clasificados: <strong>{batchResult.classified}</strong></span>
            <span>Sin categoría: <strong>{batchResult.unclassified}</strong></span>
            <span>Manuales preservados: <strong>{batchResult.overrides_preserved}</strong></span>
          </div>
        </div>
      )}

      {/* New rule form */}
      {showForm && <NewRuleForm onClose={() => setShowForm(false)} />}

      {/* Rules table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 bg-muted/30 border-b">
          <h2 className="font-semibold text-sm">Reglas de clasificación</h2>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={showInactive}
                onChange={(e) => setShowInactive(e.target.checked)}
                className="rounded"
              />
              Mostrar inactivas
            </label>
            <button
              onClick={() => setShowForm((v) => !v)}
              className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 border rounded hover:bg-muted"
            >
              <PlusCircle size={13} />
              Nueva regla
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="py-12 text-center text-muted-foreground text-sm">Cargando reglas…</div>
        ) : visibleRules.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground text-sm">
            No hay reglas. Ejecuta el script de seed o crea una regla manualmente.
          </div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b bg-muted/20 text-xs font-medium text-muted-foreground">
                <th className="px-3 py-2 text-center w-16">Prio.</th>
                <th className="px-3 py-2">Nombre</th>
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2">Patrón</th>
                <th className="px-3 py-2">Categoría</th>
                <th className="px-3 py-2 text-center">Estado</th>
                <th className="px-3 py-2 text-center w-10"></th>
              </tr>
            </thead>
            <tbody>
              {visibleRules.map((rule) => (
                <RuleRow
                  key={rule.id}
                  rule={rule}
                  section={categorySection[rule.category_code]}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Taxonomy reference */}
      <details className="mt-6 border rounded-lg overflow-hidden">
        <summary className="px-4 py-3 bg-muted/30 cursor-pointer font-semibold text-sm select-none">
          Taxonomía de categorías ({categories.filter((c) => c.level === 2 || c.code === "UNCLASSIFIED").length} categorías)
        </summary>
        <div className="p-4">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs font-medium text-muted-foreground border-b">
                <th className="pb-2 text-left pr-4">Código</th>
                <th className="pb-2 text-left pr-4">Nombre</th>
                <th className="pb-2 text-left">Descripción</th>
              </tr>
            </thead>
            <tbody>
              {categories
                .filter((c) => c.level === 2 || c.code === "UNCLASSIFIED")
                .map((cat) => (
                  <tr key={cat.code} className="border-b hover:bg-muted/20">
                    <td className="py-2 pr-4">
                      <span className={`text-xs px-2 py-0.5 rounded font-mono ${SECTION_STYLE[cat.cash_flow_section]}`}>
                        {cat.code}
                      </span>
                    </td>
                    <td className="py-2 pr-4 font-medium">{cat.name}</td>
                    <td className="py-2 text-muted-foreground text-xs">{cat.description}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
