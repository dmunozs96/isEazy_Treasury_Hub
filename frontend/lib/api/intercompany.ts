import { api } from "./client";
import type {
  ForeignEntity,
  IntercompanyMatch,
  IntercomparySummary,
  ScanResponse,
} from "@/types/api";

export interface MatchFilters {
  status?: string;
  company_id?: string;
  date_from?: string;
  date_to?: string;
}

function buildQuery(filters: MatchFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.company_id) params.set("company_id", filters.company_id);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const matchesApi = {
  list: (filters: MatchFilters = {}) =>
    api.get<IntercompanyMatch[]>(`/api/v1/intercompany/matches${buildQuery(filters)}`),

  get: (id: string) =>
    api.get<IntercompanyMatch>(`/api/v1/intercompany/matches/${id}`),

  confirm: (id: string, notes?: string) =>
    api.post<IntercompanyMatch>(`/api/v1/intercompany/matches/${id}/confirm`, { notes }),

  reject: (id: string, reason: string) =>
    api.post<IntercompanyMatch>(`/api/v1/intercompany/matches/${id}/reject`, { reason }),

  createManual: (movement_out_id: string, movement_in_id: string, notes?: string) =>
    api.post<IntercompanyMatch>("/api/v1/intercompany/matches/manual", {
      movement_out_id,
      movement_in_id,
      notes,
    }),
};

export const intercompanyScanApi = {
  run: () => api.post<ScanResponse>("/api/v1/intercompany/scan", {}),
};

export const intercomparySummaryApi = {
  get: () => api.get<IntercomparySummary>("/api/v1/intercompany/summary"),
};

export const foreignEntitiesApi = {
  list: () => api.get<ForeignEntity[]>("/api/v1/intercompany/foreign-entities"),

  create: (body: { name: string; country: string; known_ibans?: string[]; keyword_patterns?: string[] }) =>
    api.post<ForeignEntity>("/api/v1/intercompany/foreign-entities", body),
};
