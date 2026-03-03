import {
  TrendingUp, TrendingDown, Activity, Target,
  BarChart3, ArrowUpRight, ArrowDownRight, Calendar,
} from 'lucide-react';

function StatCard({ label, value, sub, icon: Icon, color = 'slate' }) {
  const colors = {
    green: 'text-emerald-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
    amber: 'text-amber-400',
    slate: 'text-slate-300',
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-start gap-3">
      <div className={`p-2 rounded-lg bg-slate-800 ${colors[color]}`}>
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-slate-500 font-medium truncate">{label}</p>
        <p className={`text-lg font-semibold mt-0.5 ${colors[color]}`}>{value}</p>
        {sub && <p className="text-[11px] text-slate-500 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-slate-800" />
        <div className="flex-1 space-y-2">
          <div className="h-3 bg-slate-800 rounded w-16" />
          <div className="h-5 bg-slate-800 rounded w-24" />
        </div>
      </div>
    </div>
  );
}

export default function MarketStats({ stats, loading }) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} />)}
      </div>
    );
  }

  const isUp = stats.change >= 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3">
      <StatCard
        label="SPY Price"
        value={`$${stats.price}`}
        sub={`${isUp ? '+' : ''}${stats.change} (${isUp ? '+' : ''}${stats.changePct}%)`}
        icon={isUp ? TrendingUp : TrendingDown}
        color={isUp ? 'green' : 'red'}
      />
      <StatCard
        label="VIX"
        value={stats.vix ?? 'N/A'}
        sub="Volatility Index"
        icon={Activity}
        color={stats.vix && stats.vix > 20 ? 'amber' : 'green'}
      />
      <StatCard
        label="200 MA"
        value={`$${stats.ma200}`}
        sub={`${stats.above200ma ? 'Above' : 'Below'} (${stats.dist200ma > 0 ? '+' : ''}${stats.dist200ma}%)`}
        icon={BarChart3}
        color={stats.above200ma ? 'green' : 'red'}
      />
      <StatCard
        label="YTD Return"
        value={`${stats.ytdReturn > 0 ? '+' : ''}${stats.ytdReturn}%`}
        sub={`Since Jan ${new Date().getFullYear()}`}
        icon={stats.ytdReturn >= 0 ? ArrowUpRight : ArrowDownRight}
        color={stats.ytdReturn >= 0 ? 'green' : 'red'}
      />
      <StatCard
        label="52W Range"
        value={`$${stats.low52w} - $${stats.high52w}`}
        sub="Low — High"
        icon={Calendar}
        color="blue"
      />
      {stats.prediction ? (
        <StatCard
          label="ML Prediction"
          value={`$${stats.prediction.predictedPrice}`}
          sub={`${stats.prediction.predictedReturn > 0 ? '+' : ''}${stats.prediction.predictedReturn}% by ${stats.prediction.targetDate}`}
          icon={Target}
          color={stats.prediction.predictedReturn >= 0 ? 'green' : 'red'}
        />
      ) : (
        <StatCard
          label="ML Prediction"
          value="N/A"
          sub="No predictions available"
          icon={Target}
          color="slate"
        />
      )}
    </div>
  );
}
