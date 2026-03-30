import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchModelResults } from '../api';
import { MODEL_UPDATED_EVENT } from '../modelEvents';
import {
  Loader2, TrendingUp, Brain, BarChart3, Calendar, Database,
  ChevronDown, ChevronRight, X,
} from 'lucide-react';

const ML_METRIC_CONFIG = {
  'RMSE': { good: v => v < 0.05, label: 'Root Mean Sq Error', lower: true },
  'MAE': { good: v => v < 0.03, label: 'Mean Absolute Error', lower: true },
  'Spearman IC': { good: v => v > 0.05, label: 'Rank Correlation' },
  'IC p-value': { good: v => v < 0.05, label: 'IC Significance', lower: true },
  'Directional Accuracy': { good: v => v > 55, label: 'Direction Hit Rate' },
};

const STRATEGY_METRIC_CONFIG = {
  'Total Return': { label: 'Total Return' },
  'CAGR': { label: 'Compound Annual Growth' },
  'Volatility': { label: 'Annualized Volatility' },
  'Sharpe Ratio': { label: 'Risk-Adjusted Return' },
  'Sortino Ratio': { label: 'Downside Risk-Adjusted' },
  'Calmar Ratio': { label: 'Return / Max Drawdown' },
  'Max Drawdown': { label: 'Worst Peak-to-Trough' },
  'Win Rate': { label: 'Profitable Periods' },
  'Profit Factor': { label: 'Gains / Losses' },
};

function parsePercent(str) {
  if (typeof str === 'number') return str;
  if (typeof str !== 'string') return null;
  const n = parseFloat(str.replace('%', ''));
  return isNaN(n) ? null : n;
}

function metricColor(key, value) {
  const cfg = ML_METRIC_CONFIG[key];
  if (!cfg) return 'text-slate-200';
  const v = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(v)) return 'text-slate-200';
  return cfg.good(v) ? 'text-emerald-400' : 'text-amber-400';
}

function strategyColor(key, value) {
  const v = parsePercent(value);
  if (v === null) {
    const n = parseFloat(value);
    if (isNaN(n)) return 'text-slate-200';
    if (key === 'Sharpe Ratio' || key === 'Sortino Ratio' || key === 'Calmar Ratio')
      return n > 0.5 ? 'text-emerald-400' : n > 0 ? 'text-amber-400' : 'text-red-400';
    if (key === 'Profit Factor')
      return n > 1 ? 'text-emerald-400' : 'text-red-400';
    return 'text-slate-200';
  }
  if (key === 'Max Drawdown') return v > -10 ? 'text-amber-400' : 'text-red-400';
  if (key === 'Win Rate') return v > 55 ? 'text-emerald-400' : v > 45 ? 'text-amber-400' : 'text-red-400';
  return v > 0 ? 'text-emerald-400' : v < 0 ? 'text-red-400' : 'text-slate-200';
}

function MetricCard({ label, value, sublabel, colorClass }) {
  return (
    <div className="bg-slate-800/50 rounded-lg px-4 py-3">
      <p className="text-[11px] text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-lg font-bold font-mono ${colorClass || 'text-slate-200'}`}>
        {typeof value === 'number' && !String(value).includes('%')
          ? value.toLocaleString(undefined, { maximumFractionDigits: 4 })
          : value}
      </p>
      {sublabel && <p className="text-[10px] text-slate-600 mt-0.5">{sublabel}</p>}
    </div>
  );
}

export default function ModelResults({ onClose, inline = false }) {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [mlOpen, setMlOpen] = useState(true);
  const [stratOpen, setStratOpen] = useState(true);
  const mountedRef = useRef(true);

  const loadResults = useCallback(async ({ showLoader = true } = {}) => {
    if (showLoader && mountedRef.current) setLoading(true);
    try {
      const res = await fetchModelResults();
      if (mountedRef.current) setResults(res.results);
    } catch (_) {
      // Keep existing UI state on transient fetch errors.
    } finally {
      if (showLoader && mountedRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    loadResults();
    const onModelUpdated = () => { loadResults({ showLoader: false }); };
    window.addEventListener(MODEL_UPDATED_EVENT, onModelUpdated);
    return () => {
      mountedRef.current = false;
      window.removeEventListener(MODEL_UPDATED_EVENT, onModelUpdated);
    };
  }, [loadResults]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-blue-400" size={24} />
      </div>
    );
  }

  if (!results) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="mx-auto text-slate-600 mb-3" size={40} />
        <p className="text-slate-400 text-sm">No model results yet.</p>
        <p className="text-slate-600 text-xs mt-1">Retrain a model to see performance metrics here.</p>
      </div>
    );
  }

  const { run_info, metrics } = results;
  const ml = metrics?.ml || {};
  const strat = metrics?.strategy || {};

  const wrapper = inline
    ? 'space-y-4'
    : 'fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4';

  const panel = inline
    ? 'space-y-4'
    : 'bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] overflow-y-auto p-6 space-y-5';

  const content = (
    <div className={inline ? panel : panel}>
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart3 size={20} className="text-blue-400" />
            Model Results
          </h3>
          {run_info && (
            <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <Brain size={12} />
                {run_info.model_type}
              </span>
              <span className="flex items-center gap-1">
                <Calendar size={12} />
                {new Date(run_info.timestamp).toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <Database size={12} />
                {run_info.train_samples?.toLocaleString()} train / {run_info.test_samples?.toLocaleString()} test
              </span>
              <span>{run_info.n_features} features</span>
            </div>
          )}
        </div>
        {!inline && onClose && (
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors">
            <X size={18} />
          </button>
        )}
      </div>

      {/* ML Performance */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
        <button
          onClick={() => setMlOpen(!mlOpen)}
          className="w-full flex items-center justify-between px-5 py-3 hover:bg-slate-800/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            {mlOpen ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
            <Brain size={16} className="text-blue-400" />
            <h4 className="text-sm font-semibold text-slate-300">ML Performance</h4>
          </div>
        </button>
        {mlOpen && (
          <div className="px-5 pb-4 border-t border-slate-800 pt-3">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
              {Object.entries(ml).map(([key, val]) => (
                <MetricCard
                  key={key}
                  label={key}
                  value={key === 'Directional Accuracy' ? `${val}%` : val}
                  sublabel={ML_METRIC_CONFIG[key]?.label}
                  colorClass={metricColor(key, val)}
                />
              ))}
            </div>
            {Object.keys(ml).length === 0 && (
              <p className="text-slate-500 text-sm text-center py-4">No ML metrics available for this run.</p>
            )}
          </div>
        )}
      </div>

      {/* Strategy Performance */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
        <button
          onClick={() => setStratOpen(!stratOpen)}
          className="w-full flex items-center justify-between px-5 py-3 hover:bg-slate-800/30 transition-colors"
        >
          <div className="flex items-center gap-2">
            {stratOpen ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
            <TrendingUp size={16} className="text-emerald-400" />
            <h4 className="text-sm font-semibold text-slate-300">Strategy Performance (Long/Flat)</h4>
          </div>
        </button>
        {stratOpen && (
          <div className="px-5 pb-4 border-t border-slate-800 pt-3">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {Object.entries(strat).map(([key, val]) => (
                <MetricCard
                  key={key}
                  label={key}
                  value={val}
                  sublabel={STRATEGY_METRIC_CONFIG[key]?.label}
                  colorClass={strategyColor(key, val)}
                />
              ))}
            </div>
            {Object.keys(strat).length === 0 && (
              <p className="text-slate-500 text-sm text-center py-4">No strategy metrics available for this run.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );

  if (inline) return content;

  return (
    <div className={wrapper} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()}>
        {content}
      </div>
    </div>
  );
}
