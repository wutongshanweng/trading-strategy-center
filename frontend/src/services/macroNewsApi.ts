import axios from "axios";

// 走 vite 代理 (/api → localhost:8000), 生产同源
const API = "/api/v1";

export interface NewsItem {
  title: string;
  content: string;
  timestamp: string;
  source: string;
  url?: string;
  products: string[];
  sentiment: string;
  label: string;
  sentiment_score: number;
}

export interface MacroIndicator {
  code: string;
  name: string;
  unit: string;
  value: number | null;
  prev: number | null;
  trend: string;
  change: number | null;
  date: string | null;
  spark: number[];
  available: boolean;
}

export interface CalendarEvent {
  date: string;
  country: string;
  event: string;
  importance: number;
  affects: string[];
}

export interface AlertSignal {
  id: string;
  created_at: string;
  symbol: string;
  product: string;
  product_name: string;
  direction: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  confidence: number;
  star_rating: number;
  reason: string;
  source: string;
  strategy_names: string[];
  factor_names: string[];
  detail: any;
}

export interface SimPosition {
  id: string;
  symbol: string;
  product_name: string;
  direction: string;
  entry_price: number;
  qty: number;
  stop_loss: number;
  take_profit: number;
  multiplier: number;
  open_time: string;
  current_price: number;
  pnl: number;
  pnl_pct: number;
  quote_source: string;
}

export const macroNewsApi = {
  async dashboard() {
    const r = await axios.get(`${API}/macro-news/dashboard`, { timeout: 60000 });
    return r.data;
  },
  async refreshNews(limit = 80) {
    const r = await axios.post(`${API}/macro-news/news/refresh`, {}, { params: { limit }, timeout: 30000 });
    return r.data as { refreshed: number; updated_at: string };
  },
  async news(limit = 80, product?: string) {
    const r = await axios.get(`${API}/macro-news/news`, { params: { limit, product }, timeout: 60000 });
    return r.data as { updated_at: string; count: number; items: NewsItem[] };
  },
  async newsDetail(url: string) {
    const r = await axios.get(`${API}/macro-news/news/detail`, { params: { url }, timeout: 30000 });
    return r.data as { url: string; content: string | null; available: boolean };
  },
  async macro() {
    const r = await axios.get(`${API}/macro-news/macro`, { timeout: 30000 });
    return r.data as { indicators: MacroIndicator[] };
  },
  async calendar(days = 14) {
    const r = await axios.get(`${API}/macro-news/calendar`, { params: { days } });
    return r.data as { days: number; events: CalendarEvent[] };
  },
};

export const alertApi = {
  async list(limit = 20) {
    const r = await axios.get(`${API}/alerts`, { params: { limit }, timeout: 60000 });
    return r.data as { updated_at: string; count: number; signals: AlertSignal[] };
  },
  async detail(id: string) {
    const r = await axios.get(`${API}/alerts/${id}`, { timeout: 30000 });
    return r.data as AlertSignal;
  },
  async refresh() {
    const r = await axios.post(`${API}/alerts/refresh`, {}, { timeout: 120000 });
    return r.data;
  },
};

export const simTradingApi = {
  async positions() {
    const r = await axios.get(`${API}/simulated/positions`, { timeout: 30000 });
    return r.data as { positions: SimPosition[]; total_pnl: number };
  },
  async open(body: {
    symbol: string; direction: string; price: number; qty: number;
    stop_loss?: number; take_profit?: number;
  }) {
    const r = await axios.post(`${API}/simulated/open`, body, { timeout: 30000 });
    return r.data;
  },
  async close(id: string, close_price?: number) {
    const r = await axios.post(`${API}/simulated/close/${id}`, { close_price }, { timeout: 30000 });
    return r.data;
  },
  async history() {
    const r = await axios.get(`${API}/simulated/history`);
    return r.data as { history: any[] };
  },
  async watchlist() {
    const r = await axios.get(`${API}/simulated/watchlist`);
    return r.data as { watchlist: any[] };
  },
  async addWatch(signal: any) {
    const r = await axios.post(`${API}/simulated/watchlist/add`, { signal });
    return r.data;
  },
  async removeWatch(id: string) {
    const r = await axios.post(`${API}/simulated/watchlist/remove`, null, { params: { sig_id: id } });
    return r.data;
  },
  async realtime(symbols: string[]) {
    const r = await axios.get(`${API}/market/realtime`, { params: { symbols: symbols.join(",") }, timeout: 30000 });
    return r.data as Record<string, { price: number | null; change: number; change_pct: number; updated_at: string; source: string }>;
  },
};
