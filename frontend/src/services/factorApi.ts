import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface ICAnalysisRequest {
  factor_id: string;
  symbol?: string;
  start_date?: string;
  end_date?: string;
  method?: string;
}

export interface LayeredBacktestRequest {
  factor_id: string;
  symbols?: string[];
  start_date?: string;
  end_date?: string;
  n_quantiles?: number;
}

export interface FactorCombineRequest {
  factor_ids: string[];
  symbols?: string[];
  method?: string;
}

export interface MineRequest {
  symbol?: string;
  n_factors?: number;
  population_size?: number;
  generations?: number;
  days?: number;
}

export interface ReportRequest {
  symbols?: string[];
  factor_ids?: string[];
  top_n?: number;
}

export interface NeutralizeRequest {
  values: Record<string, number>;
  industries: Record<string, string>;
  method?: string;
}

export const factorApi = {
  // IC分析
  async icAnalysis(request: ICAnalysisRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/factor/ic-analysis`, request);
    return response.data;
  },

  // 分层回测
  async layeredBacktest(request: LayeredBacktestRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/factor/layered-backtest`, request);
    return response.data;
  },

  // 因子组合
  async factorCombine(request: FactorCombineRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/factor/factor-combine`, request);
    return response.data;
  },

  // 获取因子列表
  async listFactors(category?: string) {
    const params = category ? { category } : {};
    const response = await axios.get(`${API_BASE_URL}/api/factor/factors/list`, { params });
    return response.data;
  },

  // Phase2: 遗传因子挖掘
  async mine(request: MineRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/factor/mine`, request, { timeout: 120000 });
    return response.data;
  },

  // Phase2: 因子健康检测
  async healthCheck(request: ICAnalysisRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/factor/health-check`, request);
    return response.data;
  },

  // Phase2: 全因子研究报告
  async report(request: ReportRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/factor/report`, request, { timeout: 60000 });
    return response.data;
  },

  // Phase2: 行业中性化
  async neutralize(request: NeutralizeRequest) {
    const response = await axios.post(`${API_BASE_URL}/api/factor/neutralize`, request);
    return response.data;
  },
};
