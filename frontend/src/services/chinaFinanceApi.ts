import apiClient from "../api/client";

const BASE = "/v1/china-finance";

export interface SkillInfo {
  name: string;
  category: string;
  description: string;
  params: string[];
}

export const chinaFinanceApi = {
  skills: (category?: string) =>
    apiClient.get<{ count: number; skills: SkillInfo[] }>(
      `${BASE}/skills`,
      category ? { params: { category } } : {}
    ),

  skillCategories: () =>
    apiClient.get<{ categories: string[] }>(`${BASE}/skills/categories`),

  runSkill: (skill: string, params: Record<string, unknown> = {}) =>
    apiClient.post<{ skill: string; result: Record<string, unknown> }>(`${BASE}/skills/run`, { skill, params }),

  financialData: (symbol: string, data_type = "basic") =>
    apiClient.get(`${BASE}/data/${symbol}`, { params: { data_type } }),

  dataAdapters: () =>
    apiClient.get<{ adapters: { name: string; note: string }[] }>(`${BASE}/data/adapters`),

  dashboard: () =>
    apiClient.get<{ data_status: Record<string, string>; skills_count: number; categories: string[] }>(`${BASE}/dashboard`),
};
