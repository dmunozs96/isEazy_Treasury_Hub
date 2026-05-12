"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  FileSpreadsheet,
  RefreshCw,
  UploadCloud,
  XCircle,
} from "lucide-react";

import { analyticsApi } from "@/lib/api/analytics";
import { companiesApi } from "@/lib/api/companies";
import { importsApi } from "@/lib/api/imports";
import { formatDate } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import type { AccountImportStatus, ImportBatch } from "@/types/api";

const STATUS_STYLE: Record<ImportBatch["status"], string> = {
  PENDING: "bg-slate-100 text-slate-700 border-slate-200",
  PROCESSING: "bg-blue-100 text-blue-800 border-blue-200",
  COMPLETED: "bg-emerald-100 text-emerald-800 border-emerald-200",
  FAILED: "bg-red-100 text-red-700 border-red-200",
  DUPLICATE: "bg-amber-100 text-amber-800 border-amber-200",
};

function StatusBadge({ status }: { status: ImportBatch["status"] }) {
  return (
    <span className={cn("rounded-full border px-2 py-0.5 text-xs font-medium", STATUS_STYLE[status])}>
      {status}
    </span>
  );
}

function ImportStat({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string | number;
  tone?: "neutral" | "good" | "warn" | "bad";
}) {
  const toneClass = {
    neutral: "text-foreground",
    good: "text-emerald-700",
    warn: "text-amber-700",
    bad: "text-red-600",
  }[tone];

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="text-xs font-medium uppercase text-muted-foreground">{label}</div>
      <div className={cn("mt-2 text-2xl font-semibold tabular-nums", toneClass)}>{value}</div>
    </div>
  );
}

function accountLabel(account: AccountImportStatus) {
  return `${account.short_name} - ${account.bank_name} ${account.account_name} (...${account.iban_last4})`;
}

export default function ImportPage() {
  const queryClient = useQueryClient();
  const now = new Date();
  const [companyId, setCompanyId] = useState("");
  const [bankAccountId, setBankAccountId] = useState("");
  const [notes, setNotes] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const { data: companies = [] } = useQuery({
    queryKey: ["companies"],
    queryFn: companiesApi.list,
    staleTime: 5 * 60_000,
  });

  const { data: consistency, isLoading: isLoadingAccounts } = useQuery({
    queryKey: ["consistency", now.getFullYear(), now.getMonth() + 1],
    queryFn: () => analyticsApi.consistency(now.getFullYear(), now.getMonth() + 1),
    staleTime: 60_000,
  });

  const accounts = useMemo(() => consistency?.section_a ?? [], [consistency]);
  const filteredAccounts = useMemo(() => {
    if (!companyId) return accounts;
    const company = companies.find((item) => item.id === companyId);
    return accounts.filter((account) => account.short_name === company?.short_name);
  }, [accounts, companies, companyId]);

  const importFilters = useMemo(
    () => ({
      company_id: companyId || undefined,
      bank_account_id: bankAccountId || undefined,
      limit: 50,
    }),
    [companyId, bankAccountId],
  );

  const {
    data: batches = [],
    isLoading: isLoadingBatches,
    isError,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["imports", importFilters],
    queryFn: () => importsApi.list(importFilters),
  });

  const createMutation = useMutation({
    mutationFn: importsApi.create,
    onSuccess: (batch) => {
      setMessage(`${batch.filename} imported: ${batch.imported_count} movements, ${batch.error_count} errors.`);
      setFile(null);
      setNotes("");
      queryClient.invalidateQueries({ queryKey: ["imports"] });
      queryClient.invalidateQueries({ queryKey: ["movements"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["cashflow"] });
      queryClient.invalidateQueries({ queryKey: ["consistency"] });
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : "Import failed.");
    },
  });

  const completed = batches.filter((batch) => batch.status === "COMPLETED").length;
  const failed = batches.filter((batch) => batch.status === "FAILED").length;
  const duplicate = batches.filter((batch) => batch.status === "DUPLICATE").length;
  const importedRows = batches.reduce((sum, batch) => sum + batch.imported_count, 0);

  function handleSubmit() {
    if (!file || !bankAccountId) {
      setMessage("Select a bank account and a statement file first.");
      return;
    }
    createMutation.mutate({ file, bankAccountId, notes });
  }

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-6 py-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-foreground">Bank Statement Import</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Upload XLS, XLSX or CSV files into the treasury ledger.
            </p>
          </div>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm transition-colors hover:bg-muted disabled:opacity-50"
          >
            <RefreshCw className={cn("h-4 w-4", isFetching && "animate-spin")} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid gap-6 p-6 xl:grid-cols-[420px_1fr]">
        <section className="space-y-4">
          <div className="rounded-lg border bg-card p-5">
            <div className="mb-4 flex items-center gap-2">
              <UploadCloud className="h-5 w-5 text-primary" />
              <h2 className="text-sm font-semibold text-foreground">New import</h2>
            </div>

            <div className="space-y-3">
              <select
                value={companyId}
                onChange={(event) => {
                  setCompanyId(event.target.value);
                  setBankAccountId("");
                }}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              >
                <option value="">All companies</option>
                {companies.map((company) => (
                  <option key={company.id} value={company.id}>
                    {company.short_name}
                  </option>
                ))}
              </select>

              <select
                value={bankAccountId}
                onChange={(event) => setBankAccountId(event.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                disabled={isLoadingAccounts}
              >
                <option value="">{isLoadingAccounts ? "Loading accounts..." : "Select bank account"}</option>
                {filteredAccounts.map((account) => (
                  <option key={account.bank_account_id} value={account.bank_account_id}>
                    {accountLabel(account)}
                  </option>
                ))}
              </select>

              <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/30 px-4 py-6 text-center transition-colors hover:bg-muted/50">
                <FileSpreadsheet className="mb-3 h-8 w-8 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">
                  {file ? file.name : "Choose statement file"}
                </span>
                <span className="mt-1 text-xs text-muted-foreground">XLS, XLSX, CSV up to 50 MB</span>
                <input
                  type="file"
                  accept=".xls,.xlsx,.csv"
                  className="sr-only"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
              </label>

              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Notes for audit trail"
                className="min-h-20 w-full resize-none rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              />

              <button
                onClick={handleSubmit}
                disabled={createMutation.isPending}
                className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
              >
                <UploadCloud className="h-4 w-4" />
                {createMutation.isPending ? "Importing..." : "Import file"}
              </button>

              {message && (
                <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                  {message}
                </div>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <ImportStat label="Completed" value={completed} tone="good" />
            <ImportStat label="Failed" value={failed} tone={failed ? "bad" : "neutral"} />
            <ImportStat label="Duplicates" value={duplicate} tone={duplicate ? "warn" : "neutral"} />
            <ImportStat label="Rows loaded" value={importedRows.toLocaleString("en-US")} />
          </div>
        </section>

        <section className="min-w-0 rounded-lg border bg-card">
          <div className="flex items-center justify-between border-b px-4 py-3">
            <h2 className="text-sm font-semibold text-foreground">Import history</h2>
            {isFetching && <span className="text-xs text-muted-foreground">Loading...</span>}
          </div>

          {isError ? (
            <div className="p-8 text-center text-sm text-destructive">
              Could not load import history. Check the API connection.
            </div>
          ) : isLoadingBatches ? (
            <div className="p-8 text-center text-sm text-muted-foreground">Loading...</div>
          ) : batches.length === 0 ? (
            <div className="p-12 text-center">
              <FileSpreadsheet className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-3 text-sm text-muted-foreground">No imports match the selected filters.</p>
            </div>
          ) : (
            <div className="overflow-auto">
              <table className="w-full border-collapse text-sm">
                <thead className="bg-muted/80">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase text-muted-foreground">File</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase text-muted-foreground">Status</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase text-muted-foreground">Rows</th>
                    <th className="px-3 py-2 text-right text-xs font-semibold uppercase text-muted-foreground">Errors</th>
                    <th className="px-3 py-2 text-left text-xs font-semibold uppercase text-muted-foreground">Imported</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map((batch) => (
                    <tr key={batch.id} className="border-t hover:bg-muted/30">
                      <td className="max-w-sm px-3 py-2">
                        <div className="truncate font-medium text-foreground" title={batch.filename}>
                          {batch.filename}
                        </div>
                        <div className="text-xs text-muted-foreground">{batch.file_format}</div>
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          {batch.status === "COMPLETED" ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          ) : batch.status === "FAILED" ? (
                            <XCircle className="h-4 w-4 text-red-500" />
                          ) : batch.status === "DUPLICATE" ? (
                            <AlertCircle className="h-4 w-4 text-amber-600" />
                          ) : (
                            <Clock className="h-4 w-4 text-muted-foreground" />
                          )}
                          <StatusBadge status={batch.status} />
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right tabular-nums">
                        {(batch.imported_count || batch.row_count || 0).toLocaleString("en-US")}
                      </td>
                      <td className={cn("px-3 py-2 text-right tabular-nums", batch.error_count > 0 && "text-red-600 font-medium")}>
                        {batch.error_count}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">{formatDate(batch.imported_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
