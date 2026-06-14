import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE = "/api";

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
});

// Request interceptor — attach auth token if available
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  try {
    const token = localStorage.getItem("auth_token");
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  } catch {
    // localStorage may not be available (SSR)
  }
  return config;
});

// Response interceptor — unwrap errors
client.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail?: string; message?: string }>) => {
    const msg =
      err.response?.data?.detail ||
      err.response?.data?.message ||
      err.message ||
      "Unknown error";
    return Promise.reject(new Error(msg));
  }
);

// ─── Health ───────────────────────────────────────────────────────
export const checkHealth = () => client.get("/health");

// ─── Strategy ─────────────────────────────────────────────────────
export interface Strategy {
  id: string;
  name: string;
  type: string;
  status: "active" | "paused" | "backtest" | "draft";
  signals: string[];
  created_at: string;
  updated_at: string;
  performance?: {
    sharpe: number;
    total_return: number;
    win_rate: number;
    max_drawdown: number;
  };
}

export const listStrategies = (params?: {
  status?: string;
  type?: string;
  page?: number;
  page_size?: number;
}) => client.get<{ strategies: Strategy[]; total: number }>("/strategies", { params });

export const getStrategy = (id: string) => client.get<Strategy>(`/strategies/${id}`);

export const createStrategy = (data: Partial<Strategy>) =>
  client.post<Strategy>("/strategies", data);

export const updateStrategy = (id: string, data: Partial<Strategy>) =>
  client.put<Strategy>(`/strategies/${id}`, data);

export const deleteStrategy = (id: string) => client.delete(`/strategies/${id}`);

// ─── Trading ──────────────────────────────────────────────────────
export interface Position {
  symbol: string;
  direction: "long" | "short";
  volume: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_pct: number;
  open_time: string;
}

export interface Order {
  id: string;
  symbol: string;
  side: "buy" | "sell";
  type: "market" | "limit";
  price: number;
  volume: number;
  filled: number;
  status: "pending" | "filled" | "cancelled" | "rejected";
  created_at: string;
}

export const getPositions = () => client.get<Position[]>("/trading/positions");
export const getOrders = (params?: { status?: string }) =>
  client.get<Order[]>("/trading/orders", { params });
export const placeOrder = (data: {
  symbol: string;
  side: "buy" | "sell";
  type: "market" | "limit";
  price?: number;
  volume: number;
}) => client.post<Order>("/trading/orders", data);
export const cancelOrder = (id: string) => client.delete(`/trading/orders/${id}`);

// ─── Backtest ─────────────────────────────────────────────────────
export interface BacktestResult {
  id: string;
  strategy_id: string;
  symbol: string;
  start_date: string;
  end_date: string;
  total_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  total_trades: number;
  equity_curve: { date: string; value: number }[];
}

export const runBacktest = (data: {
  strategy_id: string;
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital?: number;
}) => client.post<BacktestResult>("/backtest/run", data);

export const getBacktestHistory = (strategy_id?: string) =>
  client.get<BacktestResult[]>("/backtest/history", {
    params: strategy_id ? { strategy_id } : undefined,
  });

// ─── Portfolio ────────────────────────────────────────────────────
export interface PortfolioSummary {
  total_value: number;
  cash: number;
  invested: number;
  daily_pnl: number;
  total_pnl: number;
  positions: Position[];
  allocation: { symbol: string; percent: number }[];
}

export const getPortfolio = () => client.get<PortfolioSummary>("/portfolio");
export const rebalancePortfolio = (targets: { symbol: string; weight: number }[]) =>
  client.post("/portfolio/rebalance", { targets });

// ─── ML Models ────────────────────────────────────────────────────
export interface MLModel {
  id: string;
  name: string;
  type: string;
  status: "idle" | "training" | "ready" | "failed";
  accuracy: number | null;
  last_trained: string | null;
}

export const listMLModels = () => client.get<MLModel[]>("/ml/models");
export const trainModel = (data: { model_type: string; params?: Record<string, unknown> }) =>
  client.post<MLModel>("/ml/train", data);

// ─── Market Data ──────────────────────────────────────────────────
export interface MarketData {
  symbol: string;
  open: number[];
  high: number[];
  low: number[];
  close: number[];
  volume: number[];
  timestamps: string[];
}

export const getMarketData = (symbol: string, period = "1d", limit = 200) =>
  client.get<MarketData>("/data/kline", { params: { symbol, period, limit } });

export const getAvailableSymbols = () =>
  client.get<string[]>("/data/symbols");

// ─── Intelligence / LLM ──────────────────────────────────────────
export interface StrategyRecommendation {
  name: string;
  description: string;
  logic: string;
  expected_performance: string;
}

export const generateStrategy = (prompt: string) =>
  client.post<StrategyRecommendation>("/intelligence/generate-strategy", { prompt });

export const analyzeMarket = () =>
  client.get<{ analysis: string; signals: string[] }>("/intelligence/market-analysis");

// ─── Tournament ───────────────────────────────────────────────────
export interface TournamentEntry {
  rank: number;
  strategy_name: string;
  score: number;
  sharpe: number;
  total_return: number;
  trades: number;
}

export const getTournamentStandings = () =>
  client.get<TournamentEntry[]>("/tournament/standings");

// ─── Alpha Factors ────────────────────────────────────────────────
export const listAlphaFactors = () =>
  client.get<{ id: string; name: string; description: string }[]>("/alpha/factors");

export default client;
