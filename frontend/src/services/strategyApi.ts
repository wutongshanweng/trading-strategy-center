import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export const strategyApi = {
  async catalogGrouped() {
    const r = await axios.get(`${API_BASE_URL}/api/v1/strategies/catalog/grouped`);
    return r.data;
  },
  async catalog(params: { regime?: string; strategy_type?: string; symbol?: string } = {}) {
    const r = await axios.get(`${API_BASE_URL}/api/v1/strategies/catalog`, { params });
    return r.data;
  },
};
