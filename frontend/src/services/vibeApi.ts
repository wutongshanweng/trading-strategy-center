import apiClient from "../api/client";

const BASE = "/v1/vibe";

export interface FactorInfo {
  name: string;
  category: string;
  category_cn: string;
  description: string;
  ic: number;
  ir: number;
  risk_adj_return: number;
}

export interface BacktestResult {
  id: string;
  symbol: string;
  strategy: string;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  trades: number;
  final_capital: number;
}

export const vibeApi = {
  factors: (params?: { category?: string; limit?: number }) =>
    apiClient.get<{ count: number; factors: FactorInfo[]; source?: string; total?: number }>(`${BASE}/factors`, { params }),

  factorCategories: () =>
    apiClient.get<{ categories: string[] }>(`${BASE}/factors/categories`),

  backtest: (req: { symbol: string; strategy: string; start_date: string; end_date: string; initial_capital: number }) =>
    apiClient.post<{ result: BacktestResult }>(`${BASE}/backtest`, req),

  backtests: (params?: { symbol?: string; limit?: number }) =>
    apiClient.get<{ count: number; backtests: BacktestResult[] }>(`${BASE}/backtests`, { params }),

  research: (query: string, symbol?: string, data_range = "1y") =>
    apiClient.post<{ query: string; symbol: string; findings: string[]; signals: string[]; confidence: number }>(
      `${BASE}/research`,
      { query, symbol, data_range }
    ),

  swarmStatus: () =>
    apiClient.get<{ agents: { name: string; status: string; tasks: number }[]; total_agents: number }>(`${BASE}/swarm/status`),

  datasources: () =>
    apiClient.get<{ datasources: { name: string; type: string; region: string; status: string }[] }>(`${BASE}/datasources`),
};
