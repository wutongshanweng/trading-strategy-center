import apiClient from "../api/client";

const BASE = "/v1/vstock";

export interface JuryOpinion {
  juror: string;
  school: string;
  verdict: string;
  confidence: number;
  reasoning: string;
}

export interface VStockReport {
  id: string;
  symbol: string;
  timestamp: string;
  jury_vote: string;
  jury_count: number;
  dominant_school: string;
  valuation_score: number;
  risk_level: string;
  scam_score: number;
  opinions: JuryOpinion[];
  summary: string;
}

export const vstockApi = {
  schools: () => apiClient.get<{ schools: string[] }>(`${BASE}/schools`),

  jurors: () => apiClient.get<{ jurors: { name: string; school: string }[] }>(`${BASE}/jurors`),

  analyze: (symbol: string, include_dcf = true, include_scam_check = true) =>
    apiClient.post<{ report: VStockReport; extras: Record<string, unknown> }>(`${BASE}/analyze`, {
      symbol,
      include_dcf,
      include_scam_check,
    }),

  reports: (params?: { symbol?: string; limit?: number }) =>
    apiClient.get<{ count: number; reports: VStockReport[] }>(`${BASE}/reports`, { params }),

  report: (id: string) => apiClient.get<VStockReport>(`${BASE}/report/${id}`),
};
