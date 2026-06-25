import apiClient from "../api/client";

const BASE = "/v1/intelligence/market";

export interface PlatformPost {
  id: string;
  platform: string;
  author: string;
  content: string;
  url: string;
  posted_at: string;
  likes: number;
  reposts: number;
  sentiment: string;
}

export const marketApi = {
  platforms: () =>
    apiClient.get<{ platforms: Record<string, { enabled: boolean; name: string }> }>(`${BASE}/platforms`),

  configPlatform: (platform: string, enabled: boolean, api_key?: string) =>
    apiClient.post(`${BASE}/platforms/config`, { platform, enabled, api_key }),

  search: (query: string, platforms: string[]) =>
    apiClient.post<{ count: number; results: PlatformPost[] }>(`${BASE}/search`, { query, platforms }),

  posts: (params?: { platform?: string; limit?: number }) =>
    apiClient.get<{ count: number; posts: PlatformPost[] }>(`${BASE}/posts`, { params }),

  sentiment: (platform?: string) =>
    apiClient.get<{ total: number; positive: number; neutral: number; negative: number; positive_pct: number }>(
      `${BASE}/sentiment`,
      platform ? { params: { platform } } : {}
    ),
};
