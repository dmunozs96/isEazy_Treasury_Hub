"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
  type PaginationState,
} from "@tanstack/react-table";
import { format, startOfMonth, endOfMonth, subDays } from "date-fns";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  RefreshCw,
  Search,
  X,
} from "lucide-react";

import { categoriesApi, movementsApi } from "@/lib/api/movements";
import { companiesApi } from "@/lib/api/companies";
import { formatAmount, formatDate, isPositive } from "@/lib/formatters";
import { useFiltersStore } from "@/store/filters";
import type { CashFlowSection, CategoryTaxonomy, Movement } from "@/types/api";

// ── Category badge colours by cash-flow section ────────────────────────────
const SECTION_STYLE: Record<CashFlowSection, string> = {
  OPERATING: "bg-blue-100 text-blue-800 border border-blue-200",
  INVESTING: "bg-purple-100 text-purple-800 border border-purple-200",
  FINANCING: "bg-orange-100 text-orange-800 border border-orange-200",
  INTERNAL: "bg-slate-100 text-slate-700 border border-slate-200",
  UNCLASSIFIED: "bg-yellow-100 text-yellow-800 border border-yellow-200",
};

// ── Inline category cell ────────────────────────────────────────────────────
function CategoryCell({
  movement,
  categories,
  onSave,
}: {
  movement: Movement;
  categories: CategoryTaxonomy[];
  onSave: (id: string, code: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const selectRef = useRef<HTMLSelectElement>(null);
  const cls = movement.classification;

  useEffect(() => {
    if (editing) selectRef.current?.focus();
  }, [editing]);

  if (editing) {
    return (
      <select
        ref={selectRef}
        defaultValue={cls?.category_code ?? ""}
        className="text-xs border rounded px-1 py-0.5 bg-background w-full max-w-[200px]"
        onChange={(e) => {
          if (e.target.value) {
            onSave(movement.id, e.target.value);
          }
          setEditing(false);
        }}
        onBlur={() => setEditing(false)}
      >
        <option value="">— Unclassified —</option>
        {categories.map((c) => (
          <option key={c.code} value={c.code}>
            {c.name}
          </option>
        ))}
      </select>
    );
  }

  const section: CashFlowSection = cls?.cash_flow_section ?? "UNCLASSIFIED";
  const label = cls?.category_name ?? "UNCLASSIFIED";

  return (
    <button
      onClick={() => setEditing(true)}
      title="Click to change category"
      className={`text-xs px-2 py-0.5 rounded-full cursor-pointer whitespace-nowrap ${SECTION_STYLE[section]}`}
    >
      {label}
    </button>
  );
}

// ── Quick date range shortcuts ──────────────────────────────────────────────
const DATE_SHORTCUTS = [
  {
    label: "7d",
    range: () => ({ from: subDays(new Date(), 7), to: new Date() }),
  },
  {
    label: "30d",
    range: () => ({ from: subDays(new Date(), 30), to: new Date() }),
  },
  {
    label: "Month",
    range: () => ({ from: startOfMonth(new Date()), to: endOfMonth(new Date()) }),
  },
];

// ── Column helper ───────────────────────────────────────────────────────────
const colHelper = createColumnHelper<Movement>();

// ── Main page ───────────────────────────────────────────────────────────────
export default function LedgerPage() {
  const queryClient = useQueryClient();
  const {
    dateRange,
    companyIds,
    setDateRange,
    setCompanyIds,
    reset: resetGlobalFilters,
  } = useFiltersStore();

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [categoryCode, setCategoryCode] = useState("");
  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: 0,
    pageSize: 50,
  });

  // Debounce search input (400ms)
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 400);
    return () => clearTimeout(t);
  }, [search]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  }, [debouncedSearch, categoryCode, dateRange, companyIds]);

  // ── Data queries ──────────────────────────────────────────────────────────
  const { data: companies = [] } = useQuery({
    queryKey: ["companies"],
    queryFn: companiesApi.list,
    staleTime: 5 * 60_000,
  });

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: categoriesApi.list,
    staleTime: 10 * 60_000,
  });

  const filters = useMemo(
    () => ({
      date_from: format(dateRange.from, "yyyy-MM-dd"),
      date_to: format(dateRange.to, "yyyy-MM-dd"),
      company_id: companyIds.length === 1 ? companyIds[0] : undefined,
      category_code: categoryCode || undefined,
      search: debouncedSearch || undefined,
      page: pagination.pageIndex + 1,
      page_size: pagination.pageSize,
      sort: "value_date",
      order: "desc" as const,
    }),
    [dateRange, companyIds, categoryCode, debouncedSearch, pagination],
  );

  const {
    data,
    isLoading,
    isError,
    isFetching,
  } = useQuery({
    queryKey: ["movements", filters],
    queryFn: () => movementsApi.list(filters),
    placeholderData: (prev) => prev,
  });

  // ── Category override mutation ────────────────────────────────────────────
  const { mutate: overrideCategory } = useMutation({
    mutationFn: ({ id, code }: { id: string; code: string }) =>
      movementsApi.overrideCategory(id, { category_code: code }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["movements"] }),
  });

  // ── Table columns ─────────────────────────────────────────────────────────
  const columns = useMemo(
    () => [
      colHelper.accessor("value_date", {
        header: "Fecha",
        size: 95,
        cell: ({ getValue }) => (
          <span className="tabular-nums text-sm">{formatDate(getValue())}</span>
        ),
      }),
      colHelper.accessor("company_short_name", {
        header: "Empresa",
        size: 90,
        cell: ({ getValue }) => (
          <span className="text-sm font-medium">{getValue() ?? "—"}</span>
        ),
      }),
      colHelper.accessor("bank_name", {
        header: "Banco",
        size: 110,
        cell: ({ getValue }) => (
          <span className="text-sm text-muted-foreground">{getValue() ?? "—"}</span>
        ),
      }),
      colHelper.accessor("description", {
        header: "Descripción",
        cell: ({ getValue }) => (
          <span
            className="text-sm block max-w-xs truncate"
            title={getValue()}
          >
            {getValue()}
          </span>
        ),
      }),
      colHelper.accessor("amount", {
        header: "Importe",
        size: 120,
        cell: ({ getValue }) => (
          <span
            className={`tabular-nums text-sm font-semibold ${
              isPositive(getValue()) ? "text-emerald-700" : "text-red-600"
            }`}
          >
            {formatAmount(getValue())}
          </span>
        ),
      }),
      colHelper.accessor("classification", {
        header: "Categoría",
        size: 160,
        cell: ({ row }) => (
          <CategoryCell
            movement={row.original}
            categories={categories}
            onSave={(id, code) => overrideCategory({ id, code })}
          />
        ),
      }),
      colHelper.accessor("balance_after", {
        header: "Saldo Post.",
        size: 115,
        cell: ({ getValue }) => {
          const v = getValue();
          return (
            <span className="tabular-nums text-sm text-muted-foreground">
              {v ? formatAmount(v) : "—"}
            </span>
          );
        },
      }),
    ],
    [categories, overrideCategory],
  );

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    pageCount: data?.pages ?? 1,
    state: { pagination },
    onPaginationChange: setPagination,
  });

  // ── Export handler ────────────────────────────────────────────────────────
  function handleExport() {
    window.open(movementsApi.exportUrl(filters), "_blank");
  }

  // ── Reset all filters ─────────────────────────────────────────────────────
  function handleReset() {
    resetGlobalFilters();
    setSearch("");
    setDebouncedSearch("");
    setCategoryCode("");
    setPagination((p) => ({ ...p, pageIndex: 0 }));
  }

  const totalLabel = data
    ? `${data.total.toLocaleString("es-ES")} movimiento${data.total !== 1 ? "s" : ""}`
    : "";

  return (
    <div className="flex flex-col h-full">
      {/* ── Page header ─────────────────────────────────────────────────── */}
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">
            Libro Mayor de Tesorería
          </h1>
          {totalLabel && (
            <p className="text-sm text-muted-foreground mt-0.5">{totalLabel}</p>
          )}
        </div>
        <button
          onClick={handleExport}
          className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-md border hover:bg-muted transition-colors"
        >
          <Download className="h-4 w-4" />
          Exportar Excel
        </button>
      </div>

      {/* ── Filter bar ──────────────────────────────────────────────────── */}
      <div className="px-6 py-3 border-b flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Buscar descripción, referencia…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-7 pr-3 py-1.5 text-sm border rounded-md bg-background w-60 focus:outline-none focus:ring-1 focus:ring-ring"
          />
          {search && (
            <button
              onClick={() => setSearch("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Date range */}
        <div className="flex items-center gap-1">
          <input
            type="date"
            value={format(dateRange.from, "yyyy-MM-dd")}
            onChange={(e) =>
              setDateRange({ from: new Date(e.target.value), to: dateRange.to })
            }
            className="text-sm border rounded-md px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <span className="text-muted-foreground text-sm">→</span>
          <input
            type="date"
            value={format(dateRange.to, "yyyy-MM-dd")}
            onChange={(e) =>
              setDateRange({ from: dateRange.from, to: new Date(e.target.value) })
            }
            className="text-sm border rounded-md px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>

        {/* Quick date shortcuts */}
        <div className="flex items-center gap-1">
          {DATE_SHORTCUTS.map(({ label, range }) => (
            <button
              key={label}
              onClick={() => setDateRange(range())}
              className="text-xs px-2 py-1 rounded border hover:bg-muted transition-colors"
            >
              {label}
            </button>
          ))}
        </div>

        {/* Company filter */}
        {companies.length > 0 && (
          <select
            value={companyIds[0] ?? ""}
            onChange={(e) =>
              setCompanyIds(e.target.value ? [e.target.value] : [])
            }
            className="text-sm border rounded-md px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Todas las empresas</option>
            {companies.map((c) => (
              <option key={c.id} value={c.id}>
                {c.short_name}
              </option>
            ))}
          </select>
        )}

        {/* Category filter */}
        {categories.length > 0 && (
          <select
            value={categoryCode}
            onChange={(e) => setCategoryCode(e.target.value)}
            className="text-sm border rounded-md px-2 py-1.5 bg-background focus:outline-none focus:ring-1 focus:ring-ring"
          >
            <option value="">Todas las categorías</option>
            {categories.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
        )}

        {/* Reset */}
        <button
          onClick={handleReset}
          className="flex items-center gap-1.5 text-sm px-2 py-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Reset
        </button>

        {/* Loading indicator */}
        {isFetching && (
          <span className="text-xs text-muted-foreground">Cargando…</span>
        )}
      </div>

      {/* ── Table ───────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-auto">
        {isError ? (
          <div className="p-8 text-center text-destructive text-sm">
            Error loading movements. Check the API connection.
          </div>
        ) : isLoading ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            Loading…
          </div>
        ) : (
          <table className="w-full text-sm border-collapse">
            <thead className="sticky top-0 bg-muted/80 backdrop-blur-sm">
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id}>
                  {hg.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-3 py-2 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide border-b whitespace-nowrap"
                      style={{ width: header.getSize() }}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-3 py-10 text-center text-muted-foreground"
                  >
                    No hay movimientos para los filtros seleccionados.
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className="border-b hover:bg-muted/40 transition-colors"
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-3 py-2">
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext(),
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* ── Pagination ──────────────────────────────────────────────────── */}
      {data && data.pages > 1 && (
        <div className="px-6 py-3 border-t flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            Página {data.page} de {data.pages} — {totalLabel}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="p-1.5 rounded hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            {/* Page number pills */}
            {Array.from({ length: data.pages }, (_, i) => i + 1)
              .filter(
                (p) =>
                  p === 1 ||
                  p === data.pages ||
                  Math.abs(p - data.page) <= 2,
              )
              .reduce<(number | "…")[]>((acc, p, idx, arr) => {
                if (idx > 0 && p - (arr[idx - 1] as number) > 1)
                  acc.push("…");
                acc.push(p);
                return acc;
              }, [])
              .map((p, idx) =>
                p === "…" ? (
                  <span key={`ellipsis-${idx}`} className="px-1 text-muted-foreground">
                    …
                  </span>
                ) : (
                  <button
                    key={p}
                    onClick={() =>
                      setPagination((prev) => ({
                        ...prev,
                        pageIndex: (p as number) - 1,
                      }))
                    }
                    className={`w-8 h-8 rounded text-sm transition-colors ${
                      p === data.page
                        ? "bg-primary text-primary-foreground font-medium"
                        : "hover:bg-muted"
                    }`}
                  >
                    {p}
                  </button>
                ),
              )}
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="p-1.5 rounded hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
