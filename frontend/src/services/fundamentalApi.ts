import axios from "axios";

const API = "/api/v1";

export interface FundamentalScore {
  inventory: number;
  cost: number;
  seasonal: number;
  demand: number;
}

export interface FundamentalDetail {
  inventory?: {
    score: number;
    detail: string;
    data_quality: string;
    current_value: number;
    percentile: number;
    trend: string;
  };
  cost?: {
    score: number;
    detail: string;
    data_quality: string;
    upstream_prices: Record<string, any>;
    total_cost_change: number;
  };
  seasonal?: {
    score: number;
    detail: string;
    data_quality: string;
    current_month: number;
    bullish_months: number[];
    bearish_months: number[];
    win_rate: number;
    avg_return: number;
  };
  demand?: {
    score: number;
    detail: string;
    data_quality: string;
    indicators: Record<string, any>;
    overall_trend: string;
  };
}

export interface FundamentalResult {
  symbol: string;
  product_name: string;
  scores: FundamentalScore;
  combined: number;
  direction: string;
  details: Record<string, string>;
  explanation: string;
  data_quality: string;
}

export const fundamentalApi = {
  async get(symbol: string): Promise<FundamentalResult> {
    const r = await axios.get(`${API}/fundamental/${symbol}`, { timeout: 30000 });
    return r.data;
  },
  async batch(symbols: string[]): Promise<FundamentalResult[]> {
    const r = await axios.post(`${API}/fundamental/batch`, { symbols }, { timeout: 30000 });
    return r.data;
  },
  async detail(symbol: string): Promise<{
    symbol: string;
    product_name: string;
    inventory: FundamentalDetail["inventory"];
    cost: FundamentalDetail["cost"];
    seasonal: FundamentalDetail["seasonal"];
    demand: FundamentalDetail["demand"];
  }> {
    const r = await axios.get(`${API}/fundamental/${symbol}/detail`, { timeout: 30000 });
    return r.data;
  },
  async productMap(): Promise<Record<string, any>> {
    const r = await axios.get(`${API}/fundamental/product-map`, { timeout: 10000 });
    return r.data.products;
  },
};
