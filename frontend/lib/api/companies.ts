import { api } from "./client";
import type { Company } from "@/types/api";

export const companiesApi = {
  list: () => api.get<Company[]>("/api/v1/companies/"),
  get: (id: string) => api.get<Company>(`/api/v1/companies/${id}`),
};
