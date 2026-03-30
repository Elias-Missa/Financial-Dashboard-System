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

export async function fetchMLConfig() {
  const { data } = await api.get('/ml/config');
  return data;
}

export async function saveMLConfig(updates) {
  const { data } = await api.put('/ml/config', { updates });
  return data;
}

export async function resetMLConfig(keys) {
  const { data } = await api.post('/ml/config/reset', { updates: keys });
  return data;
}

export async function fetchFeatureInventory() {
  const { data } = await api.get('/ml/features');
  return data;
}

export async function retrainModel() {
  const { data } = await api.post('/ml/retrain');
  return data;
}

export async function fetchRetrainStatus() {
  const { data } = await api.get('/ml/retrain/status');
  return data;
}

export async function fetchModelResults() {
  const { data } = await api.get('/ml/results');
  return data;
}

export async function fetchPresets() {
  const { data } = await api.get('/ml/presets');
  return data;
}

export async function savePreset(name) {
  const { data } = await api.post('/ml/presets', { name });
  return data;
}

export async function loadPreset(name) {
  const { data } = await api.post(`/ml/presets/${encodeURIComponent(name)}/load`);
  return data;
}

export async function deletePreset(name) {
  const { data } = await api.delete(`/ml/presets/${encodeURIComponent(name)}`);
  return data;
}
