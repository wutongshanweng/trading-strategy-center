import apiClient from "../api/client";

const BASE = "/v1/news";

export interface NewsItem {
  id: string;
  source: string;
  title: string;
  summary: string;
  url: string;
  published_at: string;
  sentiment_score: number;
  sentiment_label: string;
  tags: string[];
}

export const newsApi = {
  list: (params?: { limit?: number; source?: string }) =>
    apiClient.get<NewsItem[]>(`${BASE}/`, { params }),

  score: (text: string, title?: string) =>
    apiClient.post<{ sentiment_score: number; sentiment_label: string }>(`${BASE}/score`, { text, title }),

  subscribe: (url: string, name?: string) =>
    apiClient.post(`${BASE}/rss/subscribe`, { url, name }),

  sources: () =>
    apiClient.get<{ sources: { name: string; url: string }[] }>(`${BASE}/rss/sources`),

  fetchRss: (name?: string) =>
    apiClient.post<{ fetched: number }>(`${BASE}/rss/fetch`, { name }),

  unsubscribe: (url: string) =>
    apiClient.delete(`${BASE}/rss/unsubscribe`, { data: { url } }),

  stats: () =>
    apiClient.get<{ total: number; by_source: Record<string, number>; avg_sentiment: number }>(`${BASE}/stats`),
};
