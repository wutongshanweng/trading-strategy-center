import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export interface ComboRequest {
  futures_direction: string;
  futures_confidence: number;
  iv_rank: number;
  skew: number;
  spot?: number;
}

export const phase3Api = {
  async mlFeatures() {
    const r = await axios.get(`${API_BASE_URL}/api/phase3/ml/features`);
    return r.data;
  },
  async optionsSurface(forward = 100, n_strikes = 15, n_ttm = 8) {
    const r = await axios.post(`${API_BASE_URL}/api/phase3/options/surface`, {
      forward, n_strikes, n_ttm,
    });
    return r.data;
  },
  async optionsArbitrage(forward = 100) {
    const r = await axios.post(`${API_BASE_URL}/api/phase3/options/arbitrage`, { forward });
    return r.data;
  },
  async optionsCombo(req: ComboRequest) {
    const r = await axios.post(`${API_BASE_URL}/api/phase3/options/combo`, req);
    return r.data;
  },
};
