import { api } from "./client";
import type { CashFlowGranularity, CashFlowStatement, ConsistencyReport, DashboardSummary } from "@/types/api";

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

export interface CashFlowFilters {
  granularity: CashFlowGranularity;
  date_from: string;
  date_to: string;
  company_id?: string;
  include_intercompany?: boolean;
}

function toQueryString(filters: CashFlowFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  return `?${params.toString()}`;
}

export const analyticsApi = {
  dashboard: () => api.get<DashboardSummary>("/api/v1/analytics/dashboard"),
  consistency: (year: number, month: number) =>
    api.get<ConsistencyReport>(`/api/v1/analytics/consistency?year=${year}&month=${month}`),
  cashflow: (filters: CashFlowFilters) =>
    api.get<CashFlowStatement>(`/api/v1/analytics/cashflow${toQueryString(filters)}`),
  cashflowExportUrl: (filters: CashFlowFilters) =>
    `${API_BASE}/api/v1/analytics/cashflow/export${toQueryString(filters)}`,
};
