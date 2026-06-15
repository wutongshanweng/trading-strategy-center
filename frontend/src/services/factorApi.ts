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
  }
};
