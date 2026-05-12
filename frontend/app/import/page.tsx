"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Bot,
  CheckCircle2,
  Clock,
  FileSpreadsheet,
  RefreshCw,
  UploadCloud,
  XCircle,
} from "lucide-react";

import { bankAccountsApi } from "@/lib/api/bank-accounts";
import { companiesApi } from "@/lib/api/companies";
import { importsApi } from "@/lib/api/imports";
import { formatDate } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import type { BankAccount, ImportBatch } from "@/types/api";

type QueuedFile = {
  id: string;
  file: File;
  bankAccountId: string;
  status: "READY" | "MISSING_ACCOUNT" | "IMPORTING" | "COMPLETED" | "FAILED";
  confidence: "AUTO" | "SERVER_AUTO" | "MANUAL" | "NONE";
  message?: string;
};

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

const COMPANY_ALIASES: Record<string, string[]> = {
  AUTHOR: ["author", "iseazy", "is easy", "iseazy sl"],
  BPO: ["bpo", "bizpills", "bizpills group"],
  ENGAGE: ["engage"],
  FACTORY: ["factory"],
  LMS: ["lms"],
  SKILLS: ["skills"],
};

const BANK_ALIASES: Record<string, string[]> = {
  ABANCA: ["abanca"],
  "BANCA MARCH": ["banca march", "bancamarch"],
  BANKINTER: ["bankinter"],
  BBVA: ["bbva"],
  CAIXABANK: ["caixa", "caixabank", "la caixa"],
  CAIXA: ["caixa", "caixabank", "la caixa"],
  CAJAMAR: ["cajamar"],
  DEUTSCHE: ["deutsche", "deustche"],
  "DEUTSCHE BANK": ["deutsche", "deustche", "deutsche bank"],
  EUROCAJA: ["eurocaja", "eurocaja rural"],
  IBERCAJA: ["ibercaja"],
  RURALVIA: ["ruralvia", "rural via"],
  SABADELL: ["sabadell"],
  SANTANDER: ["santander"],
};

function accountLast4(account: BankAccount) {
  return account.iban?.replace(/\D/g, "").slice(-4) || account.account_name.replace(/\D/g, "").slice(-4);
}

function accountLabel(account: BankAccount) {
  const company = account.company_short_name ?? "Group";
  const last4 = accountLast4(account);
  return `${company} - ${account.bank_name} ${account.account_name}${last4 ? ` (...${last4})` : ""}`;
}

function normalizeToken(value: string) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function aliasesForCompany(account: BankAccount) {
  const shortName = account.company_short_name ?? "";
  return [shortName, account.company_name ?? "", ...(COMPANY_ALIASES[shortName.toUpperCase()] ?? [])]
    .map(normalizeToken)
    .filter(Boolean);
}

function aliasesForBank(account: BankAccount) {
  const bank = account.bank_name.toUpperCase();
  const aliasKey = Object.keys(BANK_ALIASES).find((key) => bank.includes(key));
  return [account.bank_name, ...(aliasKey ? BANK_ALIASES[aliasKey] : [])]
    .map(normalizeToken)
    .filter(Boolean);
}

function scoreAccountForFile(fileName: string, account: BankAccount) {
  const normalizedFileName = normalizeToken(fileName);
  const fileDigits = fileName.match(/\d{3,4}/g) ?? ([] as string[]);
  const last4 = accountLast4(account);
  const accountDigits = account.account_name.match(/\d{3,4}/g) ?? ([] as string[]);
  const bankHit = aliasesForBank(account).some((token) => normalizedFileName.includes(token));
  const companyHit = aliasesForCompany(account).some((token) => normalizedFileName.includes(token));
  const numberHit = Boolean(
    (last4 && fileDigits.includes(last4)) ||
      accountDigits.some((digits) => fileDigits.includes(digits)),
  );

  let score = 0;
  if (bankHit) score += 40;
  if (companyHit) score += 35;
  if (numberHit) score += 60;

  if (bankHit && numberHit) score += 35;
  if (companyHit && numberHit) score += 25;
  if (bankHit && companyHit) score += 20;

  return score;
}

function guessAccount(fileName: string, accounts: BankAccount[]) {
  const scored = accounts
    .map((account) => ({ account, score: scoreAccountForFile(fileName, account) }))
    .filter((item) => item.score >= 70)
    .sort((a, b) => b.score - a.score);

  return scored[0]?.account ?? null;
}

export default function ImportPage() {
  const queryClient = useQueryClient();
  const [companyId, setCompanyId] = useState("");
  const [notes, setNotes] = useState("");
  const [queuedFiles, setQueuedFiles] = useState<QueuedFile[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const { data: companies = [] } = useQuery({
    queryKey: ["companies"],
    queryFn: companiesApi.list,
    staleTime: 5 * 60_000,
  });

  const { data: accounts = [], isLoading: isLoadingAccounts } = useQuery({
    queryKey: ["bank-accounts"],
    queryFn: () => bankAccountsApi.list({ active_only: true }),
    staleTime: 60_000,
  });

  const filteredAccounts = useMemo(() => {
    if (!companyId) return accounts;
    return accounts.filter((account) => account.company_id === companyId);
  }, [accounts, companyId]);

  const importFilters = useMemo(
    () => ({
      company_id: companyId || undefined,
      limit: 50,
    }),
    [companyId],
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
    mutationFn: async (files: QueuedFile[]) => {
      const results: ImportBatch[] = [];
      let failures = 0;
      for (const item of files) {
        setQueuedFiles((current) =>
          current.map((queued) =>
            queued.id === item.id ? { ...queued, status: "IMPORTING", message: "Importing..." } : queued,
          ),
        );

        try {
          const batch = await importsApi.create({
            file: item.file,
            bankAccountId: item.bankAccountId || undefined,
            notes,
          });
          results.push(batch);
          setQueuedFiles((current) =>
            current.map((queued) =>
              queued.id === item.id
                ? {
                    ...queued,
                    status: batch.status === "FAILED" ? "FAILED" : "COMPLETED",
                    message: `${batch.imported_count} rows, ${batch.error_count} errors`,
                  }
                : queued,
            ),
          );
        } catch (error) {
          failures += 1;
          setQueuedFiles((current) =>
            current.map((queued) =>
              queued.id === item.id
                ? {
                    ...queued,
                    status: "FAILED",
                    message: error instanceof Error ? error.message : "Import failed",
                  }
                : queued,
            ),
          );
        }
      }
      return { results, failures };
    },
    onSuccess: ({ results, failures }) => {
      const importedCount = results.reduce((sum, batch) => sum + batch.imported_count, 0);
      const errorCount = results.reduce((sum, batch) => sum + batch.error_count, 0);
      setMessage(
        `${results.length + failures} files processed: ${importedCount} movements, ${errorCount} row errors, ${failures} failed uploads.`,
      );
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
  const readyFiles = queuedFiles.filter((item) => item.status === "READY" || item.status === "MISSING_ACCOUNT");
  const missingAccountCount = queuedFiles.filter((item) => item.status === "MISSING_ACCOUNT").length;
  const autoAssignedCount = queuedFiles.filter((item) => item.confidence === "AUTO" || item.confidence === "SERVER_AUTO").length;

  function handleFilesSelected(fileList: FileList | null) {
    const files = Array.from(fileList ?? []);
    if (files.length === 0) return;

    const nextFiles = files.map((selectedFile) => {
      const guessedAccount = guessAccount(selectedFile.name, accounts);
      return {
        id: `${selectedFile.name}-${selectedFile.size}-${selectedFile.lastModified}`,
        file: selectedFile,
        bankAccountId: guessedAccount?.id ?? "",
        status: guessedAccount ? "READY" : "MISSING_ACCOUNT",
        confidence: guessedAccount ? "AUTO" : "SERVER_AUTO",
        message: guessedAccount ? `Matched ${accountLabel(guessedAccount)}` : "Will auto-detect during import",
      } satisfies QueuedFile;
    });

    setQueuedFiles(nextFiles);
    const matched = nextFiles.filter((item) => item.bankAccountId).length;
    setMessage(
      `${nextFiles.length} files queued. ${matched} matched in the browser; the rest will be auto-detected by the import service.`,
    );
  }

  function updateQueuedAccount(id: string, nextAccountId: string) {
    setQueuedFiles((current) =>
      current.map((item) =>
        item.id === id
          ? {
              ...item,
              bankAccountId: nextAccountId,
              status: nextAccountId ? "READY" : "MISSING_ACCOUNT",
              confidence: nextAccountId ? "MANUAL" : "NONE",
              message: undefined,
            }
          : item,
      ),
    );
  }

  function handleSubmit() {
    if (queuedFiles.length === 0) {
      setMessage("Select one or more statement files first.");
      return;
    }
    const filesToImport = queuedFiles.filter((item) => item.status === "READY" || item.status === "MISSING_ACCOUNT");
    if (filesToImport.length === 0) {
      setMessage("There are no ready files to import.");
      return;
    }
    createMutation.mutate(filesToImport);
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

              {queuedFiles.length > 0 && (
                <div className="grid grid-cols-3 gap-2 rounded-lg border bg-muted/30 p-3 text-center text-xs">
                  <div>
                    <div className="font-semibold text-emerald-700">{autoAssignedCount}</div>
                    <div className="text-muted-foreground">Auto matched</div>
                  </div>
                  <div>
                    <div className={cn("font-semibold", missingAccountCount ? "text-blue-700" : "text-emerald-700")}>
                      {missingAccountCount}
                    </div>
                    <div className="text-muted-foreground">Server detect</div>
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">{readyFiles.length}</div>
                    <div className="text-muted-foreground">Ready</div>
                  </div>
                </div>
              )}

              <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-muted/30 px-4 py-6 text-center transition-colors hover:bg-muted/50">
                <FileSpreadsheet className="mb-3 h-8 w-8 text-muted-foreground" />
                <span className="text-sm font-medium text-foreground">
                  {queuedFiles.length > 0 ? `${queuedFiles.length} files selected` : "Choose statement files"}
                </span>
                <span className="mt-1 text-xs text-muted-foreground">
                  Select all XLS, XLSX or CSV files together
                </span>
                <input
                  type="file"
                  accept=".xls,.xlsx,.csv"
                  multiple
                  className="sr-only"
                  onChange={(event) => handleFilesSelected(event.target.files)}
                />
              </label>

              {queuedFiles.length > 0 && (
                <div className="max-h-72 overflow-auto rounded-lg border">
                  <table className="w-full border-collapse text-xs">
                    <thead className="sticky top-0 bg-muted/90">
                      <tr>
                        <th className="px-2 py-2 text-left font-semibold uppercase text-muted-foreground">
                          File
                        </th>
                        <th className="px-2 py-2 text-left font-semibold uppercase text-muted-foreground">
                          Account
                        </th>
                        <th className="px-2 py-2 text-left font-semibold uppercase text-muted-foreground">
                          State
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {queuedFiles.map((item) => (
                        <tr key={item.id} className="border-t">
                          <td className="max-w-48 px-2 py-2">
                            <div className="truncate font-medium" title={item.file.name}>
                              {item.file.name}
                            </div>
                            <div className="text-muted-foreground">
                              {(item.file.size / 1024 / 1024).toFixed(1)} MB
                            </div>
                          </td>
                          <td className="px-2 py-2">
                            <select
                              value={item.bankAccountId}
                              onChange={(event) => updateQueuedAccount(item.id, event.target.value)}
                              disabled={createMutation.isPending}
                              className="w-56 rounded border bg-background px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
                            >
                              <option value="">Assign account</option>
                              {accounts.map((account) => (
                                <option key={account.id} value={account.id}>
                                  {accountLabel(account)}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="px-2 py-2">
                            <span
                              className={cn(
                                "rounded-full border px-2 py-0.5 font-medium",
                                item.status === "COMPLETED" && "border-emerald-200 bg-emerald-100 text-emerald-800",
                                item.status === "FAILED" && "border-red-200 bg-red-100 text-red-700",
                                item.status === "IMPORTING" && "border-blue-200 bg-blue-100 text-blue-800",
                                item.status === "MISSING_ACCOUNT" && "border-blue-200 bg-blue-100 text-blue-800",
                                item.status === "READY" && "border-slate-200 bg-slate-100 text-slate-700",
                              )}
                            >
                              {item.status === "MISSING_ACCOUNT" ? "AUTO DETECT" : item.status.replace("_", " ")}
                            </span>
                            {(item.confidence === "AUTO" || item.confidence === "SERVER_AUTO") && (
                              <div className="mt-1 flex items-center gap-1 text-emerald-700">
                                <Bot className="h-3 w-3" />
                                {item.confidence === "AUTO" ? "Auto assigned" : "Auto detect"}
                              </div>
                            )}
                            {item.message && (
                              <div className="mt-1 max-w-40 truncate text-muted-foreground" title={item.message}>
                                {item.message}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

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
                {createMutation.isPending
                  ? "Importing batch..."
                  : queuedFiles.length > 0
                    ? `Import ${readyFiles.length || queuedFiles.length} file${(readyFiles.length || queuedFiles.length) === 1 ? "" : "s"}`
                    : "Import files"}
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
