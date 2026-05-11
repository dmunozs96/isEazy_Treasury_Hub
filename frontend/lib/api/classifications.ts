import { api } from "./client";
import type { BatchClassifyResponse, ClassificationRule, MatchType } from "@/types/api";

export interface RuleCreate {
  name: string;
  priority: number;
  match_type: MatchType;
  match_field: string;
  match_pattern: string;
  category_code: string;
  subcategory_code?: string;
}

export interface RuleUpdate {
  name?: string;
  priority?: number;
  is_active?: boolean;
  match_type?: MatchType;
  match_field?: string;
  match_pattern?: string;
  category_code?: string;
}

export interface BatchClassifyRequest {
  movement_ids?: string[] | null;
  force_reclassify?: boolean;
}

export const rulesApi = {
  list: () => api.get<ClassificationRule[]>("/api/v1/classifications/rules"),

  create: (body: RuleCreate) =>
    api.post<ClassificationRule>("/api/v1/classifications/rules", body),

  update: (id: string, body: RuleUpdate) =>
    api.put<ClassificationRule>(`/api/v1/classifications/rules/${id}`, body),

  deactivate: (id: string) =>
    api.delete<void>(`/api/v1/classifications/rules/${id}`),
};

export const batchClassifyApi = {
  run: (body: BatchClassifyRequest = {}) =>
    api.post<BatchClassifyResponse>("/api/v1/classifications/batch", body),
};
