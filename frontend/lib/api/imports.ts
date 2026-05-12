import { api } from "./client";
import type { ImportBatch } from "@/types/api";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

export interface ImportFilters {
  company_id?: string;
  bank_account_id?: string;
  limit?: number;
}

function toQueryString(filters: ImportFilters = {}): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export interface CreateImportInput {
  file: File;
  bankAccountId?: string;
  notes?: string;
}

async function createImport(input: CreateImportInput): Promise<ImportBatch> {
  const form = new FormData();
  form.set("file", input.file);
  if (input.bankAccountId) {
    form.set("bank_account_id", input.bankAccountId);
  }
  if (input.notes?.trim()) {
    form.set("notes", input.notes.trim());
  }

  const path = input.bankAccountId ? "/api/v1/imports/" : "/api/v1/imports/auto";
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body: form,
    redirect: "follow",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? body.message ?? res.statusText);
  }

  return res.json() as Promise<ImportBatch>;
}

export const importsApi = {
  list: (filters?: ImportFilters) =>
    api.get<ImportBatch[]>(`/api/v1/imports${toQueryString(filters)}`),
  create: createImport,
};
