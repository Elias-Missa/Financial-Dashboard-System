import { useState, useEffect } from 'react';
import { fetchHistorical, fetchPredictions, fetchMarketStats, generatePredictions } from '../api';
import PriceChart from './PriceChart';
import MarketStats from './MarketStats';
import { RefreshCw, AlertCircle, Sparkles, Loader2 } from 'lucide-react';

const RANGES = [
  { label: '1Y', years: 1 },
  { label: '2Y', years: 2 },
  { label: '5Y', years: 5 },
  { label: '10Y', years: 10 },
];

export default function Dashboard() {
  const [historical, setHistorical] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [stats, setStats] = useState(null);
  const [range, setRange] = useState(5);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [range]);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [histRes, predRes, statsRes] = await Promise.all([
        fetchHistorical(range),
        fetchPredictions(),
        fetchMarketStats(),
      ]);
      setHistorical(histRes.data || []);
      setPredictions(predRes.predictions || []);
      setStats(statsRes);
    } catch (err) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">S&P 500 Overview</h2>
          <p className="text-sm text-slate-500 mt-0.5">
            SPY ETF &middot; ML-Powered Predictions
          </p>
        </div>
        <div className="flex items-center gap-2">
          {RANGES.map(({ label, years }) => (
            <button
              key={years}
              onClick={() => setRange(years)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                range === years
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
          <button
            onClick={async () => {
              setGenerating(true);
              setError(null);
              try {
                await generatePredictions();
                await loadData();
              } catch (err) {
                setError(err.response?.data?.detail || 'Failed to generate predictions');
              } finally {
                setGenerating(false);
              }
            }}
            disabled={generating || loading}
            className="ml-2 flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/30 transition-colors disabled:opacity-50"
          >
            {generating ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
            {generating ? 'Generating...' : 'Generate Predictions'}
          </button>
          <button
            onClick={loadData}
            disabled={loading}
            className="p-2 rounded bg-slate-800 text-slate-400 hover:bg-slate-700 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* Stats cards */}
      <MarketStats stats={stats} loading={loading} />

      {/* Chart */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <PriceChart
          historical={historical}
          predictions={predictions}
          loading={loading}
        />
      </div>
    </div>
  );
}
