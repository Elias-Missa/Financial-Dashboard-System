import { useState, useEffect } from 'react';
import { fetchStrategies, runBacktest } from '../api';
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine,
} from 'recharts';
import { Play, Loader2, AlertCircle } from 'lucide-react';

function MetricsTable({ metrics }) {
  if (!metrics) return null;
  const entries = Object.entries(metrics).filter(
    ([k]) => !['Strategy Type'].includes(k)
  );

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
      {entries.map(([key, val]) => (
        <div key={key} className="bg-slate-800/50 rounded-lg p-3">
          <p className="text-[11px] text-slate-500 font-medium">{key}</p>
          <p className="text-sm font-semibold text-slate-200 mt-0.5">{val}</p>
        </div>
      ))}
    </div>
  );
}

function EquityCurveChart({ data }) {
  if (!data?.length) return null;

  return (
    <div className="mt-4">
      <h4 className="text-sm font-semibold text-slate-300 mb-3">Equity Curve</h4>
      <ResponsiveContainer width="100%" height={350}>
        <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#64748b', fontSize: 10 }}
            stroke="#475569"
            interval={Math.max(1, Math.floor(data.length / 10))}
            tickFormatter={d => {
              const dt = new Date(d);
              return dt.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
            }}
          />
          <YAxis
            tick={{ fill: '#64748b', fontSize: 10 }}
            stroke="#475569"
            tickFormatter={v => v.toFixed(2)}
            width={60}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            labelStyle={{ color: '#94a3b8' }}
            formatter={(v, name) => [v.toFixed(4), name === 'equity' ? 'Equity' : name]}
            labelFormatter={d => new Date(d).toLocaleDateString()}
          />
          <ReferenceLine y={1} stroke="#475569" strokeDasharray="3 3" />
          <Line
            type="monotone"
            dataKey="equity"
            stroke="#3b82f6"
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function Backtest() {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('strategy1');
  const [ticker, setTicker] = useState('SPY');
  const [startDate, setStartDate] = useState('2015-01-01');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStrategies()
      .then(res => {
        setStrategies(res.strategies || []);
        if (res.strategies?.length > 0 && !res.strategies.find(s => s.name === selectedStrategy)) {
          setSelectedStrategy(res.strategies[0].name);
        }
      })
      .catch(() => {});
  }, []);

  async function handleRun() {
    setLoading(true);
    setError(null);
    setResults(null);
    try {
      const res = await runBacktest({
        ticker,
        strategy: selectedStrategy,
        start_date: startDate || null,
        end_date: endDate || null,
      });
      setResults(res);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Backtest failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Strategy Backtester</h2>
        <p className="text-sm text-slate-500 mt-0.5">
          Test trading strategies against historical data
        </p>
      </div>

      {/* Controls */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Ticker</label>
            <input
              type="text"
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="SPY"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Strategy</label>
            <select
              value={selectedStrategy}
              onChange={e => setSelectedStrategy(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
            >
              {strategies.map(s => (
                <option key={s.name} value={s.name}>
                  {s.displayName} ({s.type})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Start Date</label>
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">End Date</label>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="Today"
            />
          </div>
          <button
            onClick={handleRun}
            disabled={loading}
            className="flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-600/50 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          >
            {loading ? (
              <><Loader2 size={16} className="animate-spin" /> Running...</>
            ) : (
              <><Play size={16} /> Run Backtest</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-5 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">
              Results: {results.ticker} &mdash;{' '}
              {strategies.find(s => s.name === results.strategy)?.displayName || results.strategy}
            </h3>
          </div>

          <MetricsTable metrics={results.metrics} />
          <EquityCurveChart data={results.equityCurve} />
        </div>
      )}
    </div>
  );
}
