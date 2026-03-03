import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
});

export async function fetchHistorical(years = 5) {
  const { data } = await api.get(`/market/historical?years=${years}`);
  return data;
}

export async function fetchPredictions() {
  const { data } = await api.get('/market/predictions');
  return data;
}

export async function fetchMarketStats() {
  const { data } = await api.get('/market/stats');
  return data;
}

export async function fetchStrategies() {
  const { data } = await api.get('/backtest/strategies');
  return data;
}

export async function runBacktest(params) {
  const { data } = await api.post('/backtest/run', params);
  return data;
}

export async function sendChatMessage(message, history) {
  const { data } = await api.post('/chatbot/message', { message, history });
  return data;
}

export async function generatePredictions() {
  const { data } = await api.post('/ml/generate-predictions');
  return data;
}
