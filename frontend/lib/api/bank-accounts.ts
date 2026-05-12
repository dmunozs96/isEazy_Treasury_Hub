import { api } from "./client";
import type { BankAccount } from "@/types/api";

export interface BankAccountFilters {
  company_id?: string;
  active_only?: boolean;
}

function toQueryString(filters: BankAccountFilters = {}): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const bankAccountsApi = {
  list: (filters?: BankAccountFilters) =>
    api.get<BankAccount[]>(`/api/v1/bank-accounts${toQueryString(filters)}`),
};
