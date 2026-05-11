import { api } from "./client";
import type { CategoryTaxonomy, Movement, PaginatedResponse } from "@/types/api";

export interface MovementFilters {
  company_id?: string;
  bank_account_id?: string;
  date_from?: string; // YYYY-MM-DD
  date_to?: string;   // YYYY-MM-DD
  category_code?: string;
  amount_min?: number;
  amount_max?: number;
  search?: string;
  page?: number;
  page_size?: number;
  sort?: string;
  order?: "asc" | "desc";
}

function toQueryString(filters: MovementFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export interface CategoryOverride {
  category_code: string;
  subcategory_code?: string;
  override_reason?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const movementsApi = {
  list: (filters: MovementFilters) =>
    api.get<PaginatedResponse<Movement>>(`/api/v1/movements/${toQueryString(filters)}`),

  get: (id: string) => api.get<Movement>(`/api/v1/movements/${id}`),

  overrideCategory: (id: string, body: CategoryOverride) =>
    api.patch<Movement>(`/api/v1/movements/${id}/category`, body),

  exportUrl: (filters: MovementFilters) =>
    `${API_BASE}/api/v1/movements/export${toQueryString(filters)}`,
};

export const categoriesApi = {
  list: () => api.get<CategoryTaxonomy[]>("/api/v1/classifications/categories"),
};
