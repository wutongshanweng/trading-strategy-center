import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export const mlOptsApi = {
  async analyze(symbol: string, horizon = 5) {
    const r = await axios.post(`${API_BASE_URL}/api/v1/ml-options/analyze`,
      { symbol, horizon }, { timeout: 120000 });
    return r.data;
  },
};

export const feedbackApi = {
  async history(limit = 20) {
    const r = await axios.get(`${API_BASE_URL}/api/v1/feedback/history`, { params: { limit } });
    return r.data;
  },
  async rankings(min_trades = 0) {
    const r = await axios.get(`${API_BASE_URL}/api/v1/feedback/rankings`, { params: { min_trades } });
    return r.data;
  },
  async process(results: any) {
    const r = await axios.post(`${API_BASE_URL}/api/v1/feedback/process`, results);
    return r.data;
  },
};

export const llmAgentApi = {
  async providers() {
    const r = await axios.get(`${API_BASE_URL}/api/v1/llm/providers`);
    return r.data;
  },
  async advise(question: string, context: Record<string, any> = {}) {
    const r = await axios.post(`${API_BASE_URL}/api/v1/llm/strategy/advise`,
      { question, context }, { timeout: 60000 });
    return r.data;
  },
  async draft(description: string) {
    const r = await axios.post(`${API_BASE_URL}/api/v1/llm/strategy/draft`,
      { description }, { timeout: 60000 });
    return r.data;
  },
};
