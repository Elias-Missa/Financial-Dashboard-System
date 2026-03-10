import { useMemo } from 'react';
import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, ReferenceLine, CartesianGrid,
} from 'recharts';

function formatDate(d) {
  const date = new Date(d);
  return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  const actual = payload.find(p => p.dataKey === 'close');
  const predicted = payload.find(p => p.dataKey === 'predicted');
  const isFuture = predicted?.value != null && (actual?.value == null);

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl text-xs">
      <p className="text-slate-400 font-medium mb-1.5">
        {new Date(label).toLocaleDateString('en-US', {
          month: 'long', day: 'numeric', year: 'numeric',
        })}
        {isFuture && <span className="ml-1.5 text-amber-400">(Forecast)</span>}
      </p>
      {actual && actual.value != null && (
        <p className="text-slate-300">
          <span className="inline-block w-2 h-2 rounded-full bg-slate-400 mr-1.5" />
          Actual: <span className="font-semibold text-white">${actual.value.toFixed(2)}</span>
        </p>
      )}
      {predicted && predicted.value != null && (
        <p className="text-emerald-400 mt-0.5">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 mr-1.5" />
          {isFuture ? 'Forecast' : 'Predicted'}: <span className="font-semibold">${predicted.value.toFixed(2)}</span>
        </p>
      )}
    </div>
  );
}

export default function PriceChart({ historical, predictions, loading }) {
  const chartData = useMemo(() => {
    if (!historical.length) return [];

    const byDate = {};

    for (const d of historical) {
      byDate[d.date] = { date: d.date, close: d.close };
    }

    for (const p of predictions) {
      const key = p.targetDate;
      if (!byDate[key]) {
        byDate[key] = { date: key };
      }
      byDate[key].predicted = p.predictedClose;
      if (p.actualClose) {
        byDate[key].close = byDate[key].close ?? p.actualClose;
      }
    }

    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
  }, [historical, predictions]);

  const today = useMemo(() => {
    if (!historical.length) return null;
    return historical[historical.length - 1]?.date;
  }, [historical]);

  const [yMin, yMax] = useMemo(() => {
    if (!chartData.length) return [0, 100];
    let lo = Infinity, hi = -Infinity;
    for (const d of chartData) {
      if (d.close != null) { lo = Math.min(lo, d.close); hi = Math.max(hi, d.close); }
      if (d.predicted != null) { lo = Math.min(lo, d.predicted); hi = Math.max(hi, d.predicted); }
    }
    const pad = (hi - lo) * 0.05;
    return [Math.floor(lo - pad), Math.ceil(hi + pad)];
  }, [chartData]);

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="flex flex-col items-center gap-2 text-slate-500">
          <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-sm">Loading chart data...</p>
        </div>
      </div>
    );
  }

  if (!chartData.length) {
    return (
      <div className="h-96 flex items-center justify-center text-slate-500 text-sm">
        No chart data available
      </div>
    );
  }

  const tickInterval = Math.max(1, Math.floor(chartData.length / 12));

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-300">
          SPY Price &amp; ML Predictions
        </h3>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-slate-400 rounded" /> Historical
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-400 rounded" /> Predicted
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-400 rounded border-b border-dashed border-emerald-400" /> Forecast
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 10 }}>
          <defs>
            <linearGradient id="fillGray" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#64748b" stopOpacity={0.15} />
              <stop offset="100%" stopColor="#64748b" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="fillGreen" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#34d399" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />

          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke="#475569"
            tick={{ fill: '#64748b', fontSize: 11 }}
            interval={tickInterval}
            axisLine={{ stroke: '#334155' }}
          />
          <YAxis
            domain={[yMin, yMax]}
            stroke="#475569"
            tick={{ fill: '#64748b', fontSize: 11 }}
            tickFormatter={v => `$${v}`}
            axisLine={{ stroke: '#334155' }}
            width={65}
          />

          <Tooltip content={<CustomTooltip />} />

          {today && (
            <ReferenceLine
              x={today}
              stroke="#3b82f6"
              strokeDasharray="4 4"
              strokeOpacity={0.5}
              label={{
                value: 'Today',
                position: 'top',
                fill: '#3b82f6',
                fontSize: 10,
              }}
            />
          )}

          <Area
            type="monotone"
            dataKey="close"
            stroke="#94a3b8"
            strokeWidth={1.5}
            fill="url(#fillGray)"
            dot={false}
            connectNulls={false}
            name="Actual"
          />

          <Line
            type="monotone"
            dataKey="predicted"
            stroke="#34d399"
            strokeWidth={2}
            dot={false}
            connectNulls
            name="Predicted"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
