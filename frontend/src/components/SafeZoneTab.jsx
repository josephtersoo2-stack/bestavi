import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  ShieldCheck, 
  Target, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  Calendar, 
  Filter, 
  RefreshCw, 
  Download, 
  ArrowUpDown, 
  CheckCircle2, 
  XCircle, 
  Flame, 
  History, 
  Search, 
  Zap, 
  Sliders,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Layers,
  Grid,
  ShieldAlert,
  Info,
  Clock,
  ArrowRight,
  AlertCircle
} from 'lucide-react';
import { API_BASE } from '../config';

// 20-Step Loss Cluster Spectrum Definitions
const LOSS_STREAK_DEFINITIONS = [
  // Tier 1: 1 - 5 (Standard Martingale Zone)
  { streak: '1', label: '1 Loss Only', note: 'Single isolated dip', step: 'Step 1 Recovery', risk: 'Safe', color: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-950/20', bar: 'bg-emerald-400' },
  { streak: '2', label: '2 In a Roll', note: 'Step 2 recovery', step: 'Step 2 Recovery', risk: 'Safe', color: 'text-teal-400', border: 'border-teal-500/30', bg: 'bg-teal-950/20', bar: 'bg-teal-400' },
  { streak: '3', label: '3 In a Roll', note: 'Step 3 recovery', step: 'Step 3 Recovery', risk: 'Moderate', color: 'text-blue-400', border: 'border-blue-500/30', bg: 'bg-blue-950/20', bar: 'bg-blue-400' },
  { streak: '4', label: '4 In a Roll', note: 'Step 4 pressure run', step: 'Step 4 Warning', risk: 'Elevated', color: 'text-indigo-400', border: 'border-indigo-500/30', bg: 'bg-indigo-950/20', bar: 'bg-indigo-400' },
  { streak: '5', label: '5 In a Roll', note: '5-step Martingale boundary', step: 'Step 5 Limit', risk: 'Threshold', color: 'text-amber-400', border: 'border-amber-500/40', bg: 'bg-amber-950/25', bar: 'bg-amber-400' },

  // Tier 2: 6 - 10 (Martingale Breach & Danger Zone)
  { streak: '6', label: '6 In a Roll', note: 'Step 6 Martingale breach', step: 'Step 6 Breach', risk: 'Danger', color: 'text-orange-400', border: 'border-orange-500/40', bg: 'bg-orange-950/25', bar: 'bg-orange-400' },
  { streak: '7', label: '7 In a Roll', note: 'Step 7 severe drawdown', step: 'Step 7 Breach', risk: 'Danger', color: 'text-orange-500', border: 'border-orange-600/40', bg: 'bg-orange-950/25', bar: 'bg-orange-500' },
  { streak: '8', label: '8 In a Roll', note: 'Step 8 heavy drawdown', step: 'Step 8 Breach', risk: 'Critical', color: 'text-rose-400', border: 'border-rose-500/40', bg: 'bg-rose-950/25', bar: 'bg-rose-500' },
  { streak: '9', label: '9 In a Roll', note: 'Step 9 critical cluster', step: 'Step 9 Critical', risk: 'Critical', color: 'text-rose-500', border: 'border-rose-600/40', bg: 'bg-rose-950/30', bar: 'bg-rose-600' },
  { streak: '10', label: '10 In a Roll', note: 'Step 10 double-tier breach', step: 'Step 10 Extreme', risk: 'Severe', color: 'text-red-400', border: 'border-red-500/50', bg: 'bg-red-950/30', bar: 'bg-red-500' },

  // Tier 3: 11 - 15 (Deep Drawdown Zone)
  { streak: '11', label: '11 In a Roll', note: 'Step 11 extreme run', step: 'Step 11 Run', risk: 'Extreme', color: 'text-purple-400', border: 'border-purple-500/40', bg: 'bg-purple-950/25', bar: 'bg-purple-400' },
  { streak: '12', label: '12 In a Roll', note: 'Step 12 capital hazard', step: 'Step 12 Hazard', risk: 'Extreme', color: 'text-fuchsia-400', border: 'border-fuchsia-500/40', bg: 'bg-fuchsia-950/25', bar: 'bg-fuchsia-400' },
  { streak: '13', label: '13 In a Roll', note: 'Step 13 ultra rare run', step: 'Step 13 Outlier', risk: 'Extreme', color: 'text-pink-400', border: 'border-pink-500/40', bg: 'bg-pink-950/25', bar: 'bg-pink-400' },
  { streak: '14', label: '14 In a Roll', note: 'Step 14 black swan run', step: 'Step 14 Outlier', risk: 'Extreme', color: 'text-rose-400', border: 'border-rose-500/40', bg: 'bg-rose-950/25', bar: 'bg-rose-400' },
  { streak: '15', label: '15 In a Roll', note: 'Step 15 deep anomaly', step: 'Step 15 Anomaly', risk: 'Outlier', color: 'text-red-500', border: 'border-red-600/50', bg: 'bg-red-950/35', bar: 'bg-red-600' },

  // Tier 4: 16 - 20+ (Black Swan Outliers)
  { streak: '16', label: '16 In a Roll', note: 'Step 16 catastrophic run', step: 'Step 16 Rare', risk: 'Outlier', color: 'text-red-400', border: 'border-red-600/50', bg: 'bg-red-950/35', bar: 'bg-red-500' },
  { streak: '17', label: '17 In a Roll', note: 'Step 17 statistical anomaly', step: 'Step 17 Rare', risk: 'Outlier', color: 'text-rose-400', border: 'border-rose-600/50', bg: 'bg-rose-950/35', bar: 'bg-rose-500' },
  { streak: '18', label: '18 In a Roll', note: 'Step 18 near-zero odds', step: 'Step 18 Rare', risk: 'Outlier', color: 'text-purple-400', border: 'border-purple-600/50', bg: 'bg-purple-950/35', bar: 'bg-purple-500' },
  { streak: '19', label: '19 In a Roll', note: 'Step 19 historic outlier', step: 'Step 19 Extreme', risk: 'Outlier', color: 'text-violet-400', border: 'border-violet-600/50', bg: 'bg-violet-950/35', bar: 'bg-violet-500' },
  { streak: '20', label: '20 In a Roll', note: 'Step 20 max monitored', step: 'Step 20 Max', risk: 'Extreme', color: 'text-amber-500', border: 'border-amber-600/50', bg: 'bg-amber-950/35', bar: 'bg-amber-500' },
  { streak: '21+', label: '21+ In a Roll', note: 'Outlier beyond 20', step: '21+ Beyond', risk: 'Black Swan', color: 'text-red-600', border: 'border-red-700/60', bg: 'bg-red-950/45', bar: 'bg-red-600' },
];

const CLUSTER_TIERS = [
  {
    id: 1,
    title: '1 - 5 in a Roll',
    category: 'Martingale Core',
    range: [0, 5],
    accentColor: 'emerald',
  },
  {
    id: 2,
    title: '6 - 10 in a Roll',
    category: 'Breach Zone',
    range: [5, 10],
    accentColor: 'orange',
  },
  {
    id: 3,
    title: '11 - 15 in a Roll',
    category: 'Deep Drawdown',
    range: [10, 15],
    accentColor: 'purple',
  },
  {
    id: 4,
    title: '16 - 20+ in a Roll',
    category: 'Black Swan Outliers',
    range: [15, 21],
    accentColor: 'rose',
  },
];

export default function SafeZoneTab() {
  const [targetOdds, setTargetOdds] = useState('1.50');
  const [inputOdds, setInputOdds] = useState('1.50');
  const [datePreset, setDatePreset] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [order, setOrder] = useState('desc'); // 'desc' = latest first, 'asc' = serial #1 first
  const [limit, setLimit] = useState(200);
  const [searchFilter, setSearchFilter] = useState('');
  const [clusterTier, setClusterTier] = useState(1); // 1 = 1-5, 2 = 6-10, 3 = 11-15, 4 = 16-20+
  const [showAllClusters, setShowAllClusters] = useState(false);
  const [expandedDate, setExpandedDate] = useState(null);
  const [incidentFilter, setIncidentFilter] = useState('5plus'); // '5plus' | '4plus'

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  // Preset target multipliers
  const quickOddsPresets = ['1.20', '1.30', '1.40', '1.50', '1.60', '1.75', '2.00'];

  const fetchSafeZoneData = async (customOdds = null) => {
    setLoading(true);
    setErrorMsg(null);
    const oddsToUse = customOdds || targetOdds;

    try {
      let url = `${API_BASE}/analytics/safezone/?target_odds=${oddsToUse}&order=${order}&limit=${limit}`;

      // Date filtering
      const today = new Date();
      if (datePreset === 'today') {
        const todayStr = today.toISOString().split('T')[0];
        url += `&start_date=${todayStr}&end_date=${todayStr}`;
      } else if (datePreset === 'yesterday') {
        const yest = new Date(today);
        yest.setDate(yest.getDate() - 1);
        const yestStr = yest.toISOString().split('T')[0];
        url += `&start_date=${yestStr}&end_date=${yestStr}`;
      } else if (datePreset === 'last_7') {
        const past = new Date(today);
        past.setDate(past.getDate() - 7);
        const pastStr = past.toISOString().split('T')[0];
        url += `&start_date=${pastStr}`;
      } else if (datePreset === 'custom') {
        if (startDate) url += `&start_date=${startDate}`;
        if (endDate) url += `&end_date=${endDate}`;
      }

      const res = await axios.get(url);
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch SafeZone analytics:', err);
      setErrorMsg(err.response?.data?.message || err.message || 'Error loading analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSafeZoneData();
  }, [targetOdds, datePreset, startDate, endDate, order, limit]);

  const handleApplyOdds = (val) => {
    const parsed = parseFloat(val);
    if (!isNaN(parsed) && parsed >= 1.01) {
      const formatted = parsed.toFixed(2);
      setTargetOdds(formatted);
      setInputOdds(formatted);
    }
  };

  const handleInputOddsSubmit = (e) => {
    e.preventDefault();
    handleApplyOdds(inputOdds);
  };

  // Export filtered serial ledger to CSV
  const handleExportCSV = () => {
    if (!data?.serial_rounds || data.serial_rounds.length === 0) return;

    const headers = ['Serial #', 'Date', 'Time', 'Crash Multiplier', 'SafeZone Status', 'Loss Streak At Roll', 'Win Streak At Roll'];
    const rows = data.serial_rounds.map(r => [
      r.serial_number,
      r.date,
      r.time,
      `${r.multiplier}x`,
      r.is_safezone ? 'SAFEZONE WIN' : 'LOSSZONE LOSS',
      r.loss_streak_at_round,
      r.win_streak_at_round
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + 
      [headers.join(','), ...rows.map(e => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `safezone_${targetOdds}x_rounds_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filtered serial rounds for local search
  const filteredSerialRounds = useMemo(() => {
    if (!data?.serial_rounds) return [];
    if (!searchFilter.trim()) return data.serial_rounds;

    const q = searchFilter.toLowerCase().trim();
    return data.serial_rounds.filter(r => 
      r.serial_number.toString().includes(q) ||
      r.multiplier.toString().includes(q) ||
      r.time.includes(q) ||
      r.date.includes(q) ||
      (r.is_safezone ? 'win safezone' : 'loss deficit').includes(q)
    );
  }, [data?.serial_rounds, searchFilter]);

  const summary = data?.summary || {
    total_rounds: 0,
    safezone_wins: 0,
    safezone_win_rate: 0,
    losszone_losses: 0,
    losszone_loss_rate: 0,
    max_loss_streak: 0,
    max_win_streak: 0,
    avg_loss_streak: 0,
    current_streak_type: 'NONE',
    current_streak_count: 0,
    total_loss_clusters: 0,
    loss_streak_frequency: { '1': 0, '2': 0, '3': 0, '4': 0, '5': 0 }
  };

  const streakFreq = summary.loss_streak_frequency || {};
  const totalLossClusters = summary.total_loss_clusters || 
    Object.entries(streakFreq)
      .filter(([k]) => k !== '5+')
      .reduce((sum, [_, count]) => sum + (Number(count) || 0), 0) || 1;

  const getTierOccurrences = (range) => {
    return LOSS_STREAK_DEFINITIONS.slice(range[0], range[1]).reduce((sum, item) => {
      return sum + (Number(streakFreq[item.streak]) || 0);
    }, 0);
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Configuration Card */}
      <div className="glass-card p-6 border-emerald-500/20 shadow-xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Title & Description */}
          <div className="flex items-start gap-4">
            <div className="p-3.5 bg-gradient-to-tr from-emerald-600 to-teal-500 rounded-2xl text-white shadow-lg shadow-emerald-500/20">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-extrabold text-white tracking-tight">SafeZone 1.50x & Daily Loss Streak Auditor</h3>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  Target: {targetOdds}x
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1 max-w-2xl leading-relaxed">
                Daily accounting of games paying in your SafeZone (<span className="text-emerald-400 font-semibold">≥ {targetOdds}x</span>) vs LossZone (<span className="text-rose-400 font-semibold">&lt; {targetOdds}x</span>). Track max consecutive losses at a roll to ensure 5-step Martingale safety.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2.5 self-end lg:self-center">
            <button
              onClick={handleExportCSV}
              disabled={!data?.serial_rounds?.length}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-gray-900 hover:bg-gray-800 text-gray-200 border border-gray-700 transition-all shadow-sm disabled:opacity-50"
              title="Download serial ledger CSV"
            >
              <Download className="w-4 h-4 text-emerald-400" />
              <span className="hidden sm:inline">Export CSV</span>
            </button>

            <button
              onClick={() => fetchSafeZoneData()}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/30 transition-all"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Filter Controls Bar */}
        <div className="mt-6 pt-5 border-t border-gray-800/80 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
          {/* Target Odds Selector */}
          <div className="md:col-span-6 space-y-2">
            <label className="text-[11px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5 text-emerald-400" />
              SafeZone Target Odds Threshold:
            </label>
            <div className="flex flex-wrap items-center gap-1.5">
              {quickOddsPresets.map(preset => (
                <button
                  key={preset}
                  onClick={() => handleApplyOdds(preset)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                    targetOdds === preset
                      ? 'bg-emerald-500 text-gray-950 shadow-md shadow-emerald-500/20 font-extrabold'
                      : 'bg-gray-900/90 text-gray-300 hover:bg-gray-800 border border-gray-800'
                  }`}
                >
                  {preset}x
                </button>
              ))}

              {/* Custom odds input */}
              <form onSubmit={handleInputOddsSubmit} className="flex items-center gap-1 ml-1">
                <input
                  type="number"
                  step="0.01"
                  min="1.01"
                  max="100.0"
                  value={inputOdds}
                  onChange={(e) => setInputOdds(e.target.value)}
                  placeholder="Custom"
                  className="w-20 px-2 py-1.5 bg-gray-950 border border-gray-700 rounded-lg text-xs text-white font-mono text-center focus:border-emerald-500"
                />
                <button
                  type="submit"
                  className="px-2.5 py-1.5 bg-gray-800 hover:bg-gray-700 text-[11px] font-bold text-emerald-400 rounded-lg border border-gray-700"
                >
                  Set
                </button>
              </form>
            </div>
          </div>

          {/* Date Range Selector */}
          <div className="md:col-span-6 space-y-2">
            <label className="text-[11px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-blue-400" />
              Date Filter Preset:
            </label>
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { id: 'all', label: 'All Time' },
                { id: 'today', label: 'Today' },
                { id: 'yesterday', label: 'Yesterday' },
                { id: 'last_7', label: 'Last 7 Days' },
                { id: 'custom', label: 'Custom' }
              ].map(p => (
                <button
                  key={p.id}
                  onClick={() => setDatePreset(p.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    datePreset === p.id
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                      : 'bg-gray-900/90 text-gray-300 hover:bg-gray-800 border border-gray-800'
                  }`}
                >
                  {p.label}
                </button>
              ))}

              {datePreset === 'custom' && (
                <div className="flex items-center gap-1.5 mt-2 sm:mt-0">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="px-2 py-1 bg-gray-950 border border-gray-700 rounded text-xs text-gray-300"
                  />
                  <span className="text-gray-500 text-xs">to</span>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="px-2 py-1 bg-gray-950 border border-gray-700 rounded text-xs text-gray-300"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
          <p className="text-xs text-rose-300">{errorMsg}</p>
        </div>
      )}

      {/* 2. Top Strategic KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: SafeZone Hit Rate */}
        <div className="glass-card p-5 border-emerald-500/30 hover:border-emerald-500/50">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">SafeZone Games Paid</span>
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-400">{summary.safezone_wins}</span>
            <span className="text-sm font-bold text-emerald-300/80 font-mono">/ {summary.total_rounds}</span>
            <span className="text-xs font-bold text-emerald-400 ml-auto font-mono bg-emerald-500/10 px-2 py-0.5 rounded-full">
              {summary.safezone_win_rate}%
            </span>
          </div>
          <div className="mt-2.5 w-full bg-gray-950 rounded-full h-1.5 overflow-hidden">
            <div 
              className="bg-emerald-400 h-full rounded-full transition-all duration-700"
              style={{ width: `${summary.safezone_win_rate}%` }}
            />
          </div>
          <p className="mt-2 text-[11px] text-gray-400">
            Rounds paying <b className="text-emerald-300">≥ {targetOdds}x</b> (Profit target hit)
          </p>
        </div>

        {/* Card 2: LossZone Deficit */}
        <div className="glass-card p-5 border-rose-500/30 hover:border-rose-500/50">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">LossZone Deficit</span>
            <div className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400">
              <XCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-black text-rose-400">{summary.losszone_losses}</span>
            <span className="text-sm font-bold text-rose-300/80 font-mono">/ {summary.total_rounds}</span>
            <span className="text-xs font-bold text-rose-400 ml-auto font-mono bg-rose-500/10 px-2 py-0.5 rounded-full">
              {summary.losszone_loss_rate}%
            </span>
          </div>
          <div className="mt-2.5 w-full bg-gray-950 rounded-full h-1.5 overflow-hidden">
            <div 
              className="bg-rose-500 h-full rounded-full transition-all duration-700"
              style={{ width: `${summary.losszone_loss_rate}%` }}
            />
          </div>
          <p className="mt-2 text-[11px] text-gray-400">
            Rounds crashing <b className="text-rose-400">&lt; {targetOdds}x</b> (Loss before target)
          </p>
        </div>

        {/* Card 3: Max Consecutive Losses at a Roll */}
        <div className={`glass-card p-5 ${
          summary.max_loss_streak >= 5 
            ? 'border-rose-500 shadow-rose-500/20 bg-rose-950/20' 
            : summary.max_loss_streak >= 4
            ? 'border-amber-500/50 bg-amber-950/10'
            : 'border-emerald-500/30'
        }`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Worst Loss Streak At a Roll</span>
            <div className={`p-1.5 rounded-lg ${
              summary.max_loss_streak >= 5 ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
            }`}>
              <Flame className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className={`text-3xl font-black ${
              summary.max_loss_streak >= 5 ? 'text-rose-400' : summary.max_loss_streak >= 4 ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              {summary.max_loss_streak}
            </span>
            <span className="text-xs text-gray-400 font-mono">consecutive losses</span>
          </div>
          <div className="mt-2 text-[11px]">
            {summary.max_loss_streak >= 5 ? (
              <span className="text-rose-400 font-bold flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Exceeded 5-step Martingale limit!
              </span>
            ) : summary.max_loss_streak === 4 ? (
              <span className="text-amber-400 font-bold">
                ⚠️ Step 4 reached (Near 5-step limit)
              </span>
            ) : (
              <span className="text-emerald-400 font-bold">
                ✅ 100% Safe within 5-step Martingale
              </span>
            )}
          </div>
        </div>

        {/* Card 4: Current Active Streak & Clusters */}
        <div className="glass-card p-5 border-blue-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Roll Streak</span>
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400">
              <History className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-white">
              {summary.current_streak_type === 'SAFEZONE' ? (
                <span className="text-emerald-400">+{summary.current_streak_count} WINS</span>
              ) : summary.current_streak_type === 'LOSS' ? (
                <span className="text-rose-400">-{summary.current_streak_count} LOSSES</span>
              ) : (
                'NONE'
              )}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-gray-400 flex items-center justify-between">
            <span>Avg loss cluster: <b className="text-white">{summary.avg_loss_streak}</b></span>
            <span>Max win run: <b className="text-emerald-400">+{summary.max_win_streak}</b></span>
          </div>
        </div>
      </div>

      {/* 3. Loss Streak "At a Roll" Frequency Meter (1 to 20+) */}
      <div className="glass-card p-6 space-y-4">
        {/* Top Header Row */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                <Flame className="w-4 h-4 text-amber-400" />
                Consecutive Losses "At a Roll" Cluster Meter
              </h4>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">
                1 to 20+ Monitored
              </span>
              {!showAllClusters && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                  clusterTier === 1 
                    ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' 
                    : clusterTier === 2 
                    ? 'bg-orange-500/15 text-orange-300 border-orange-500/30' 
                    : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                }`}>
                  Viewing {CLUSTER_TIERS[clusterTier - 1]?.title}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-0.5">
              Exact count of times losses stacked consecutively before recovering into a SafeZone win (Martingale Risk Spectrum).
            </p>
          </div>

          <div className="flex items-center gap-2 self-start lg:self-auto">
            <span className="text-xs font-mono text-gray-300 bg-gray-900/90 px-3 py-1.5 rounded-xl border border-gray-800 flex items-center gap-1.5 shadow-sm">
              <span className="text-gray-400">Total Losing Sequences:</span>
              <b className="text-white font-bold">{totalLossClusters}</b>
            </span>
          </div>
        </div>

        {/* Interactive 20-Point Micro-Heatmap Spectrum Ribbon */}
        <div className="p-3 bg-gray-950/80 rounded-xl border border-gray-800/80 space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="font-mono text-gray-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span className="font-bold">20-Step Loss Frequency Spectrum</span>
            </span>
            <span className="text-[10px] text-gray-500 hidden sm:inline">
              Click any node to jump directly to its 5-step bracket
            </span>
          </div>

          <div className="grid grid-cols-7 sm:grid-cols-21 gap-1">
            {LOSS_STREAK_DEFINITIONS.map((item, idx) => {
              const count = Number(streakFreq[item.streak]) || 0;
              const hasHits = count > 0;
              const tierIndex = Math.min(4, Math.floor(idx / 5) + 1);
              const isSelectedTier = !showAllClusters && clusterTier === tierIndex;

              return (
                <button
                  key={item.streak}
                  type="button"
                  onClick={() => {
                    setClusterTier(tierIndex);
                    setShowAllClusters(false);
                  }}
                  title={`${item.streak} in a roll: ${count} occurrences (${item.note})`}
                  className={`group relative flex flex-col items-center justify-center py-1.5 px-0.5 rounded-lg border transition-all ${
                    isSelectedTier 
                      ? 'border-cyan-400 bg-cyan-950/50 ring-1 ring-cyan-500/50 shadow-sm shadow-cyan-500/20' 
                      : hasHits 
                      ? 'border-gray-700 bg-gray-900/90 hover:border-gray-500' 
                      : 'border-gray-900 bg-gray-950/60 opacity-40 hover:opacity-75'
                  }`}
                >
                  <span className={`text-[10px] font-mono font-extrabold ${
                    hasHits ? item.color : 'text-gray-500'
                  }`}>
                    {item.streak}
                  </span>
                  <div className={`w-1.5 h-1.5 rounded-full mt-0.5 ${
                    hasHits ? (idx >= 4 ? 'bg-rose-500 live-pulse' : 'bg-emerald-400') : 'bg-gray-800'
                  }`} />
                  {hasHits ? (
                    <span className="text-[9px] font-mono text-gray-200 font-bold mt-0.5">
                      {count}
                    </span>
                  ) : (
                    <span className="text-[8px] font-mono text-gray-600 mt-0.5">
                      -
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Navigation & Bracket Selection Controls Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-1">
          {/* Segmented Range Buttons / Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0 scrollbar-none">
            {CLUSTER_TIERS.map(tier => {
              const occurrences = getTierOccurrences(tier.range);
              const isActive = !showAllClusters && clusterTier === tier.id;
              return (
                <button
                  key={tier.id}
                  onClick={() => {
                    setClusterTier(tier.id);
                    setShowAllClusters(false);
                  }}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-600/30 ring-1 ring-cyan-400/50'
                      : 'bg-gray-900/90 text-gray-300 hover:bg-gray-800 hover:text-white border border-gray-800'
                  }`}
                >
                  <span>{tier.title}</span>
                  <span className={`px-1.5 py-0.5 rounded-md text-[10px] font-mono font-bold ${
                    occurrences > 0 
                      ? (tier.id === 1 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/25 text-rose-300 border border-rose-500/40')
                      : 'bg-gray-800 text-gray-500'
                  }`}>
                    {occurrences} hits
                  </span>
                </button>
              );
            })}
          </div>

          {/* Controls: Dropdown + Arrows + View Mode */}
          <div className="flex items-center gap-2 self-end md:self-auto flex-wrap">
            {/* Quick Dropdown */}
            <div className="relative">
              <select
                value={showAllClusters ? 'all' : clusterTier}
                onChange={(e) => {
                  if (e.target.value === 'all') {
                    setShowAllClusters(true);
                  } else {
                    setShowAllClusters(false);
                    setClusterTier(Number(e.target.value));
                  }
                }}
                aria-label="Select Loss Streak Bracket"
                className="appearance-none px-3 py-2 pr-8 bg-gray-950 border border-gray-800 hover:border-gray-700 rounded-xl text-xs font-semibold text-gray-200 focus:outline-none focus:border-cyan-500 cursor-pointer shadow-sm"
              >
                {CLUSTER_TIERS.map(t => (
                  <option key={t.id} value={t.id}>
                    Tier {t.id}: {t.title} ({getTierOccurrences(t.range)} hits)
                  </option>
                ))}
                <option value="all">View All 20 Tiers (Grid)</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            {/* Prev / Next Page Buttons */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  setShowAllClusters(false);
                  setClusterTier(prev => Math.max(1, prev - 1));
                }}
                disabled={showAllClusters || clusterTier === 1}
                title="Previous 5 Loss Streaks"
                aria-label="Previous 5 Loss Streaks"
                className="p-2 rounded-xl bg-gray-900 border border-gray-800 hover:bg-gray-800 text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => {
                  setShowAllClusters(false);
                  setClusterTier(prev => Math.min(CLUSTER_TIERS.length, prev + 1));
                }}
                disabled={showAllClusters || clusterTier === CLUSTER_TIERS.length}
                title="Next 5 Loss Streaks"
                aria-label="Next 5 Loss Streaks"
                className="p-2 rounded-xl bg-gray-900 border border-gray-800 hover:bg-gray-800 text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {/* Toggle All Grid View */}
            <button
              onClick={() => setShowAllClusters(prev => !prev)}
              title={showAllClusters ? "Switch back to 5-at-a-time" : "Expand all 20 tiers"}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all border ${
                showAllClusters
                  ? 'bg-cyan-600 text-white border-cyan-500 shadow-md shadow-cyan-600/30'
                  : 'bg-gray-900 text-gray-300 hover:bg-gray-800 hover:text-white border-gray-800'
              }`}
            >
              {showAllClusters ? <Layers className="w-3.5 h-3.5" /> : <Grid className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">{showAllClusters ? '5 at a Time' : 'View All 20'}</span>
            </button>
          </div>
        </div>

        {/* Dynamic Cards Grid */}
        {(() => {
          const activeTier = CLUSTER_TIERS.find(t => t.id === clusterTier) || CLUSTER_TIERS[0];
          const displayedItems = showAllClusters 
            ? LOSS_STREAK_DEFINITIONS 
            : LOSS_STREAK_DEFINITIONS.slice(activeTier.range[0], activeTier.range[1]);
          const currentTierHits = getTierOccurrences(activeTier.range);

          return (
            <div className="space-y-3 pt-1">
              <div className={`grid gap-3 ${
                showAllClusters 
                  ? 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7' 
                  : displayedItems.length === 6 
                  ? 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6' 
                  : 'grid-cols-2 sm:grid-cols-5'
              }`}>
                {displayedItems.map(item => {
                  const count = Number(streakFreq[item.streak]) || 0;
                  const pct = totalLossClusters > 0 
                    ? ((count / totalLossClusters) * 100).toFixed(count > 0 && count < totalLossClusters * 0.01 ? 1 : 0)
                    : 0;

                  return (
                    <div 
                      key={item.streak} 
                      className={`p-3.5 rounded-xl border ${item.border} ${item.bg} flex flex-col justify-between space-y-2 transition-all hover:border-gray-500/60 shadow-sm`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-gray-300">{item.label}</span>
                        <span className={`text-[10px] font-mono ${count > 0 ? 'text-gray-300 font-bold' : 'text-gray-600'}`}>
                          {pct}%
                        </span>
                      </div>

                      <div className="flex items-baseline justify-between gap-1">
                        <div className="flex items-baseline gap-1.5">
                          <span className={`text-2xl font-black ${item.color}`}>
                            {count}
                          </span>
                          <span className="text-[10px] text-gray-400">times</span>
                        </div>
                        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border ${
                          count > 0 
                            ? 'bg-gray-900/90 text-gray-300 border-gray-700' 
                            : 'bg-gray-950/60 text-gray-600 border-gray-900'
                        }`}>
                          {item.step}
                        </span>
                      </div>

                      <div className="w-full bg-gray-950 rounded-full h-1 overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${item.bar}`} 
                          style={{ width: `${Math.min(100, Math.max(count > 0 ? 3 : 0, Number(pct)))}%` }} 
                        />
                      </div>

                      <div className="flex items-center justify-between text-[9px] text-gray-400 pt-0.5">
                        <span className="truncate" title={item.note}>{item.note}</span>
                        <span className={`font-mono px-1 py-0.2 rounded text-[8px] ${
                          count === 0 
                            ? 'text-gray-600' 
                            : item.risk === 'Safe' 
                            ? 'text-emerald-400' 
                            : item.risk === 'Moderate' 
                            ? 'text-blue-400' 
                            : item.risk === 'Elevated' 
                            ? 'text-indigo-400' 
                            : 'text-rose-400 font-bold'
                        }`}>
                          {count === 0 ? 'Zero Hits' : item.risk}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Zero Occurrence Reassurance Banner if tier is empty */}
              {!showAllClusters && currentTierHits === 0 && (
                <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex items-center gap-3 text-xs text-emerald-300 animate-in fade-in duration-200">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <div>
                    <span className="font-bold">100% Resilience in {activeTier.title}: </span>
                    <span className="text-emerald-200/90">
                      Zero losing streaks in this range have been recorded. No consecutive crash sequence has ever challenged your capital into this drawdown tier in this dataset.
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* 4. Daily SafeZone & LossZone Breakdown Ledger */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h4 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
              <Calendar className="w-4 h-4 text-emerald-400" />
              Daily SafeZone Performance Ledger
            </h4>
            <p className="text-xs text-gray-400 mt-0.5">
              Day-by-day record of games paying ≥ {targetOdds}x vs &lt; {targetOdds}x and peak consecutive losses at a roll.
            </p>
          </div>
          <span className="text-xs text-gray-400 font-mono">
            {data?.daily_breakdown?.length || 0} active days recorded
          </span>
        </div>

        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-950/80 text-gray-400 font-mono uppercase text-[10px] tracking-wider border-b border-gray-800">
              <tr>
                <th className="py-3 px-4">Date (Click to Inspect)</th>
                <th className="py-3 px-4 text-center">Total Games</th>
                <th className="py-3 px-4 text-center">SafeZone Paid (≥ {targetOdds}x)</th>
                <th className="py-3 px-4 text-center">LossZone Deficit (&lt; {targetOdds}x)</th>
                <th className="py-3 px-4">Daily Win Rate</th>
                <th className="py-3 px-4 text-center">Max Losses At Roll</th>
                <th className="py-3 px-4 text-right">Daily Peak Odds</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-mono">
              {(data?.daily_breakdown || []).map((row, idx) => {
                const isExpanded = expandedDate === row.date;
                const allIncidents = row.streak_incidents || [];
                const incidents5Plus = allIncidents.filter(inc => inc.streak_length >= 5);
                const incidents4Plus = allIncidents.filter(inc => inc.streak_length >= 4);
                const incidents3Plus = allIncidents.filter(inc => inc.streak_length >= 3);

                // Auto-fallback if filtering for 5+ but there are only 4-loss or 3-loss streaks on this day
                let effectiveFilter = incidentFilter;
                if (incidentFilter === '5plus' && incidents5Plus.length === 0) {
                  if (incidents4Plus.length > 0) effectiveFilter = '4plus';
                  else if (incidents3Plus.length > 0) effectiveFilter = '3plus';
                }

                const displayIncidents = effectiveFilter === '5plus' 
                  ? incidents5Plus 
                  : effectiveFilter === '4plus' 
                  ? incidents4Plus 
                  : incidents3Plus;

                // Determine today vs yesterday for the occurrences label ("1 time today or 2 times today etc.")
                const localToday = new Date();
                const pad = (n) => String(n).padStart(2, '0');
                const todayStr = `${localToday.getFullYear()}-${pad(localToday.getMonth() + 1)}-${pad(localToday.getDate())}`;
                const yest = new Date(localToday);
                yest.setDate(yest.getDate() - 1);
                const yestStr = `${yest.getFullYear()}-${pad(yest.getMonth() + 1)}-${pad(yest.getDate())}`;

                const occurrences = row.max_loss_streak_occurrences ?? (
                  allIncidents.filter(inc => inc.streak_length === row.max_loss_streak).length || 1
                );

                let timesLabel = '';
                if (row.max_loss_streak > 0) {
                  const timesWord = occurrences === 1 ? '1 time' : `${occurrences} times`;
                  if (row.date === todayStr) {
                    timesLabel = ` ${timesWord} today`;
                  } else if (row.date === yestStr) {
                    timesLabel = ` ${timesWord} yesterday`;
                  } else {
                    timesLabel = ` ${timesWord}`;
                  }
                }

                return (
                  <React.Fragment key={row.date || idx}>
                    <tr 
                      onClick={() => setExpandedDate(isExpanded ? null : row.date)}
                      className={`cursor-pointer transition-all border-b border-gray-800/60 ${
                        isExpanded 
                          ? 'bg-rose-950/20 border-l-4 border-l-rose-500 hover:bg-rose-950/30' 
                          : 'hover:bg-gray-800/40'
                      }`}
                      title="Click row to inspect all consecutive loss streak incidents for this date"
                    >
                      <td className="py-3.5 px-4 font-bold text-white flex items-center gap-2">
                        <span className={`p-1 rounded-md transition-transform ${isExpanded ? 'bg-rose-500/20 text-rose-300' : 'bg-gray-900 text-gray-500'}`}>
                          {isExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                        </span>
                        <Calendar className="w-3.5 h-3.5 text-gray-500" />
                        <span className="font-mono">{row.date}</span>
                        {row.count_5plus_streaks > 0 && (
                          <span className="ml-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1">
                            <Flame className="w-2.5 h-2.5 text-rose-400" />
                            {row.count_5plus_streaks} (5+)
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-center text-gray-300 font-bold">
                        {row.total_rounds}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {row.safezone_wins} ({row.win_rate}%)
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          {row.losszone_losses} ({row.loss_rate}%)
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="w-28 space-y-1">
                          <div className="flex justify-between text-[10px]">
                            <span className="text-emerald-400 font-bold">{row.win_rate}%</span>
                          </div>
                          <div className="w-full bg-gray-950 rounded-full h-1.5 overflow-hidden">
                            <div 
                              className="bg-emerald-400 h-full rounded-full" 
                              style={{ width: `${row.win_rate}%` }} 
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <div className="inline-flex items-center gap-1.5">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                            row.max_loss_streak >= 5 
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' 
                              : row.max_loss_streak >= 3 
                              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' 
                              : 'bg-emerald-500/10 text-emerald-400'
                          }`}>
                            {row.max_loss_streak} losses in a roll{timesLabel}
                          </span>
                          <span className="text-[10px] font-mono text-gray-400 underline decoration-dotted">
                            {isExpanded ? 'Hide' : 'Inspect'}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-right font-bold text-amber-400">
                        {row.peak_multiplier}x
                      </td>
                    </tr>

                    {/* Expandable Loss Streak Incidents Breakdown Drawer */}
                    {isExpanded && (
                      <tr className="bg-gray-950/95 border-b-2 border-rose-500/40">
                        <td colSpan="7" className="p-4 sm:p-6 space-y-4">
                          {/* Drawer Header & Controls */}
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-800">
                            <div>
                              <div className="flex items-center gap-2">
                                <h5 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
                                  <Flame className="w-4 h-4 text-rose-500" />
                                  Loss Streak Incidents on {row.date}
                                </h5>
                                <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30">
                                  Max: {row.max_loss_streak} in a roll{timesLabel}
                                </span>
                              </div>
                              <p className="text-xs text-gray-400 mt-1">
                                Every consecutive losing run (&lt; {targetOdds}x) listed separately in chronological order with exact odds and timestamps.
                              </p>
                            </div>

                            {/* Filter Switcher */}
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setIncidentFilter('5plus'); }}
                                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                                  effectiveFilter === '5plus'
                                    ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/30'
                                    : 'bg-gray-900 text-gray-400 hover:text-white border border-gray-800'
                                }`}
                              >
                                <Flame className="w-3.5 h-3.5" />
                                5+ in a Roll ({incidents5Plus.length})
                              </button>

                              <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); setIncidentFilter('4plus'); }}
                                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                                  effectiveFilter === '4plus'
                                    ? 'bg-amber-600 text-white shadow-lg shadow-amber-600/30'
                                    : 'bg-gray-900 text-gray-400 hover:text-white border border-gray-800'
                                }`}
                              >
                                <Zap className="w-3.5 h-3.5" />
                                All 4+ in a Roll ({incidents4Plus.length})
                              </button>

                              {incidents3Plus.length > incidents4Plus.length && (
                                <button
                                  type="button"
                                  onClick={(e) => { e.stopPropagation(); setIncidentFilter('3plus'); }}
                                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${
                                    effectiveFilter === '3plus'
                                      ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                                      : 'bg-gray-900 text-gray-400 hover:text-white border border-gray-800'
                                  }`}
                                >
                                  <Layers className="w-3.5 h-3.5" />
                                  All 3+ in a Roll ({incidents3Plus.length})
                                </button>
                              )}
                            </div>
                          </div>

                          {/* Reassuring Banner if 0 5+ Loss Streaks Occurred */}
                          {incidents5Plus.length === 0 && row.max_loss_streak < 5 && (
                            <div className="p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-xl flex items-center gap-3 text-xs text-emerald-300 font-mono">
                              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                              <span>
                                <strong>Zero 5+ Loss Streaks Recorded!</strong> On this date, the maximum loss streak was safely contained at <strong>{row.max_loss_streak}</strong> consecutive losses. Displaying the <strong>{incidents4Plus.length}</strong> incident(s) of 4-in-a-row losses below:
                              </span>
                            </div>
                          )}

                          {/* Separate Incident Cards */}
                          {displayIncidents.length > 0 ? (
                            <div className="space-y-4">
                              {displayIncidents.map((incident) => (
                                <div
                                  key={incident.incident_id}
                                  className="p-4 rounded-xl bg-gray-900/90 border border-gray-800/90 hover:border-gray-700 transition-all space-y-3.5 shadow-xl"
                                >
                                  {/* Incident Header */}
                                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-gray-800">
                                    <div className="flex items-center gap-2.5">
                                      <span className="px-2.5 py-1 rounded-md text-xs font-black tracking-wider uppercase bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm">
                                        Incident #{incident.incident_id}
                                      </span>
                                      <span className="text-sm font-extrabold text-white flex items-center gap-1.5 font-mono">
                                        <Flame className="w-4 h-4 text-rose-500" />
                                        {incident.streak_length} Losses in a Roll
                                      </span>
                                      <span className="text-[11px] font-mono text-gray-400 bg-gray-950 px-2 py-0.5 rounded border border-gray-800">
                                        Rounds #{incident.rounds[0]?.serial_number} → #{incident.rounds[incident.rounds.length - 1]?.serial_number}
                                      </span>
                                    </div>

                                    <div className="flex items-center gap-2 text-xs font-mono text-gray-400 bg-gray-950/80 px-3 py-1 rounded-lg border border-gray-800">
                                      <Clock className="w-3.5 h-3.5 text-amber-400" />
                                      <span>
                                        Time Window: <strong className="text-white">{incident.start_time}</strong> → <strong className="text-white">{incident.end_time}</strong>
                                      </span>
                                    </div>
                                  </div>

                                  {/* Serial Chain of Odds & Timestamps */}
                                  <div>
                                    <div className="text-[10px] font-mono text-gray-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                                      <Zap className="w-3 h-3 text-purple-400" />
                                      <span>Serial Sequence of Loss Odds & Timestamps:</span>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                                      {incident.rounds.map((rnd, rIdx) => (
                                        <React.Fragment key={rnd.id || rIdx}>
                                          <div className="flex flex-col items-center bg-gray-950 border border-rose-500/30 rounded-xl p-2.5 min-w-[95px] text-center shadow-md">
                                            <span className="text-[10px] font-mono font-bold text-rose-400 uppercase tracking-tight">
                                              Roll {rnd.step}
                                            </span>
                                            <span className={`text-lg font-black font-mono my-0.5 ${
                                              parseFloat(rnd.multiplier) < 1.20 ? 'text-rose-400' : 'text-amber-400'
                                            }`}>
                                              {parseFloat(rnd.multiplier).toFixed(2)}x
                                            </span>
                                            <div className="flex items-center gap-1 text-[10px] font-mono text-gray-400">
                                              <Clock className="w-2.5 h-2.5 text-gray-500" />
                                              <span>{rnd.time}</span>
                                            </div>
                                            <span className="text-[9px] font-mono text-gray-500 mt-0.5">
                                              Round #{rnd.serial_number}
                                            </span>
                                          </div>

                                          {rIdx < incident.rounds.length - 1 && (
                                            <ArrowRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
                                          )}
                                        </React.Fragment>
                                      ))}

                                      {/* Streak Recovery Badge */}
                                      {incident.broken_by && (
                                        <>
                                          <div className="flex items-center text-emerald-400 px-1 font-bold">
                                            <ArrowRight className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                                          </div>
                                          <div className="flex flex-col items-center bg-emerald-950/40 border border-emerald-500/40 rounded-xl p-2.5 min-w-[105px] text-center shadow-md">
                                            <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-tight flex items-center gap-1">
                                              <CheckCircle2 className="w-3 h-3" /> Streak Broken
                                            </span>
                                            <span className="text-lg font-black font-mono my-0.5 text-emerald-300">
                                              {parseFloat(incident.broken_by.multiplier).toFixed(2)}x
                                            </span>
                                            <div className="flex items-center gap-1 text-[10px] font-mono text-gray-400">
                                              <Clock className="w-2.5 h-2.5 text-gray-500" />
                                              <span>{incident.broken_by.time}</span>
                                            </div>
                                            <span className="text-[9px] font-mono text-emerald-400/80 mt-0.5">
                                              Round #{incident.broken_by.serial_number}
                                            </span>
                                          </div>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="p-6 text-center text-gray-500 text-xs font-mono bg-gray-900/50 rounded-xl border border-gray-800">
                              No {effectiveFilter === '5plus' ? '5+ consecutive loss' : 'loss'} incidents recorded for this day.
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
              {(!data?.daily_breakdown || data.daily_breakdown.length === 0) && (
                <tr>
                  <td colSpan="7" className="py-8 text-center text-gray-500 text-xs font-mono">
                    No rounds recorded for the selected filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. Serial Sequential Round Ledger ("and it should be serially") */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" />
              Serial Sequential Round Ledger
            </h4>
            <p className="text-xs text-gray-400 mt-0.5">
              Exact chronological rounds tracking serial sequence, crash multiplier, and consecutive loss streak counter at each roll.
            </p>
          </div>

          {/* Ledger Toolbar */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Search Filter */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search serial / odds..."
                className="pl-8 pr-3 py-1.5 bg-gray-950 border border-gray-800 rounded-lg text-xs text-white placeholder-gray-500 w-44 focus:border-purple-500"
              />
            </div>

            {/* Order Toggle */}
            <button
              onClick={() => setOrder(order === 'desc' ? 'asc' : 'desc')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gray-900 hover:bg-gray-800 text-gray-300 border border-gray-800 transition-all"
              title="Toggle serial sequence order"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-purple-400" />
              <span>{order === 'desc' ? 'Latest First' : 'Serial #1 First'}</span>
            </button>

            {/* Limit Selector */}
            <select
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="px-2.5 py-1.5 bg-gray-950 border border-gray-800 rounded-lg text-xs text-gray-300 font-mono"
            >
              <option value="50">50 Rounds</option>
              <option value="100">100 Rounds</option>
              <option value="200">200 Rounds</option>
              <option value="500">500 Rounds</option>
              <option value="0">All Rounds</option>
            </select>
          </div>
        </div>

        {/* Serial Ledger Table */}
        <div className="overflow-x-auto rounded-xl border border-gray-800 max-h-[550px] overflow-y-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-gray-950 sticky top-0 z-10 text-gray-400 font-mono uppercase text-[10px] tracking-wider border-b border-gray-800">
              <tr>
                <th className="py-3 px-4">Serial #</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4 text-center">Crash Odds</th>
                <th className="py-3 px-4 text-center">SafeZone Status</th>
                <th className="py-3 px-4 text-center">Streak Status At This Roll</th>
                <th className="py-3 px-4 text-right">Round ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-mono">
              {filteredSerialRounds.map((round) => {
                const isSafe = round.is_safezone;
                const m = round.multiplier;
                const badgeClass = m >= 10.0 ? 'badge-gold' : m >= 2.0 ? 'badge-purple' : m >= 1.5 ? 'badge-blue' : 'bg-gray-800 text-gray-300 border border-gray-700';

                return (
                  <tr 
                    key={round.serial_number}
                    className={`hover:bg-gray-800/40 transition-colors ${
                      round.loss_streak_at_round >= 3 ? 'bg-rose-950/15' : ''
                    }`}
                  >
                    {/* Serial # */}
                    <td className="py-3 px-4 font-bold text-gray-300">
                      <span className="text-purple-400">#{round.serial_number}</span>
                    </td>

                    {/* Timestamp */}
                    <td className="py-3 px-4 text-gray-400 text-[11px]">
                      <span className="text-white font-semibold">{round.time}</span>
                      <span className="text-gray-500 ml-2">({round.date})</span>
                    </td>

                    {/* Crash Odds */}
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-bold ${badgeClass}`}>
                        {m.toFixed(2)}x
                      </span>
                    </td>

                    {/* SafeZone Status */}
                    <td className="py-3 px-4 text-center">
                      {isSafe ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          <CheckCircle2 className="w-3 h-3" /> Paid (≥ {targetOdds}x)
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30">
                          <XCircle className="w-3 h-3" /> Lost (&lt; {targetOdds}x)
                        </span>
                      )}
                    </td>

                    {/* Streak Status at This Roll */}
                    <td className="py-3 px-4 text-center">
                      {isSafe ? (
                        <span className="text-emerald-400 text-[11px] font-semibold">
                          Win #{round.win_streak_at_round}
                        </span>
                      ) : (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold text-[11px] ${
                          round.loss_streak_at_round >= 5 
                            ? 'bg-rose-600 text-white font-extrabold shadow-sm' 
                            : round.loss_streak_at_round >= 3 
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' 
                            : 'bg-gray-800 text-rose-400 border border-gray-700'
                        }`}>
                          {round.loss_streak_at_round >= 3 && <Flame className="w-3 h-3 text-rose-400 animate-pulse" />}
                          Loss #{round.loss_streak_at_round} at a roll
                        </span>
                      )}
                    </td>

                    {/* DB ID */}
                    <td className="py-3 px-4 text-right text-gray-500 text-[11px]">
                      ID:{round.id}
                    </td>
                  </tr>
                );
              })}

              {filteredSerialRounds.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-gray-500 text-xs font-mono">
                    No sequential rounds match current query.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Ledger Footer */}
        <div className="flex items-center justify-between text-xs text-gray-400 pt-2 font-mono">
          <span>Showing {filteredSerialRounds.length} of {data?.total_serial_count || 0} rounds</span>
          <span>Ordered by Serial #{order === 'desc' ? 'Descending (Newest)' : 'Ascending (Chronological)'}</span>
        </div>
      </div>
    </div>
  );
}
