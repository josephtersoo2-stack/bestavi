import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart3, PieChart, TrendingUp, Award, AlertCircle, Percent, DollarSign, RefreshCw } from 'lucide-react';
import { API_BASE } from '../config';

export default function AnalyticsTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/analytics/`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const distTotal = (data?.distribution || []).reduce((acc, curr) => acc + curr.count, 0) || 1;

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="glass-card p-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Odds & Betting Intelligence</h3>
            <p className="text-xs text-gray-400">Statistical crash patterns computed directly from PostgreSQL database.</p>
          </div>
        </div>
        <button
          onClick={fetchAnalytics}
          disabled={loading}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-purple-400' : ''}`} />
          <span>Refresh Analytics</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Average Multiplier */}
        <div className="glass-card p-5">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Average Crash Point</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white">{data?.average_multiplier || 0}x</span>
            <span className="text-xs text-gray-500 font-mono">Mean odds</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400">Max observed: <b className="text-amber-400">{data?.max_multiplier || 0}x</b></div>
        </div>

        {/* Sub-2x Percentage */}
        <div className="glass-card p-5">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Sub-2.0x Crash Rate</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-rose-400">{data?.under_2x_percentage || 0}%</span>
            <span className="text-xs text-gray-500 font-mono">&lt; 2.0x rounds</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400">Crash risk before 2.0x threshold</div>
        </div>

        {/* Total Bets */}
        <div className="glass-card p-5">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Total Staking Rounds</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-blue-400">{data?.total_bets || 0}</span>
            <span className="text-xs text-gray-500 font-mono">bets</span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400">Win rate: <b className="text-emerald-400">{data?.win_rate || 0}%</b></div>
        </div>

        {/* Net Profit/Loss */}
        <div className="glass-card p-5">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Net Realized Profit</span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className={`text-2xl font-bold ${(data?.total_profit_loss || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
              {(data?.total_profit_loss || 0) >= 0 ? '+' : ''}₦{(data?.total_profit_loss || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400">Lifetime bot yield</div>
        </div>
      </div>

      {/* Multiplier Distribution Breakdown */}
      <div className="glass-card p-6 space-y-4">
        <h4 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
          <PieChart className="w-4 h-4 text-amber-400" />
          Multiplier Distribution Breakdown
        </h4>
        <p className="text-xs text-gray-400">
          Distribution of crash multipliers across historical rounds recorded in the PostgreSQL database.
        </p>

        <div className="space-y-3 pt-2">
          {(data?.distribution || []).map((bucket, idx) => {
            const pct = Math.round((bucket.count / distTotal) * 100);
            const config = idx === 0
              ? { bar: 'bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.35)]', tag: 'bg-rose-500/15 text-rose-300 border-rose-500/30' }
              : idx === 1
              ? { bar: 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.35)]', tag: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' }
              : idx === 2
              ? { bar: 'bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.35)]', tag: 'bg-purple-500/15 text-purple-300 border-purple-500/30' }
              : idx === 3
              ? { bar: 'bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.35)]', tag: 'bg-amber-500/15 text-amber-300 border-amber-500/30' }
              : { bar: 'bg-pink-500 shadow-[0_0_10px_rgba(236,72,153,0.35)]', tag: 'bg-pink-500/15 text-pink-300 border-pink-500/30' };

            return (
              <div key={idx} className="space-y-1.5 p-2.5 rounded-lg bg-gray-900/50 border border-gray-800 hover:border-gray-700/80 transition-all">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-mono font-bold">{bucket.range}</span>
                    {bucket.label && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded border font-medium uppercase tracking-wider ${config.tag}`}>
                        {bucket.label}
                      </span>
                    )}
                  </div>
                  <span className="text-gray-300 font-mono text-xs">
                    <b className="text-white">{bucket.count.toLocaleString()}</b> rounds <span className="text-gray-400">({pct}%)</span>
                  </span>
                </div>
                <div className="w-full bg-gray-950 rounded-full h-2.5 overflow-hidden p-0.5 border border-gray-800/80">
                  <div
                    className={`${config.bar} h-full rounded-full transition-all duration-700`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
