import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  Rocket, 
  Wallet, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Terminal, 
  Copy, 
  Trash2,
  Zap,
  Activity,
  ShieldCheck,
  Clock,
  Calendar,
  XCircle,
  RefreshCw,
  Wifi,
  WifiOff,
  BellRing,
  ChevronDown,
  ChevronUp,
  Eye,
  AlertOctagon
} from 'lucide-react';

export default function DashboardTab({ 
  status, 
  logs, 
  onPrepare, 
  onStart, 
  onPause, 
  onStop, 
  onSchedule,
  onCancelSchedule,
  onClearLogs,
  loadingAction 
}) {
  const logEndRef = useRef(null);
  const [copied, setCopied] = useState(false);
  
  // Scheduler state
  const [scheduleMode, setScheduleMode] = useState('delay'); // 'delay' | 'time'
  const [delayMinutes, setDelayMinutes] = useState(30);
  const [specificTime, setSpecificTime] = useState('');
  const [autoStopMinutes, setAutoStopMinutes] = useState(0);
  const [autoStake, setAutoStake] = useState(true);
  const [countdownText, setCountdownText] = useState('');
  const [showSchedulerCard, setShowSchedulerCard] = useState(false);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Live countdown timer for active background schedule
  useEffect(() => {
    if (!status?.schedule?.active || !status?.schedule?.start_time) {
      setCountdownText('');
      return;
    }

    const target = new Date(status.schedule.start_time).getTime();
    const updateCountdown = () => {
      const now = Date.now();
      const diff = Math.max(0, Math.floor((target - now) / 1000));
      if (diff <= 0) {
        setCountdownText('Triggering Auto-Start now...');
        return;
      }
      const hrs = Math.floor(diff / 3600);
      const mins = Math.floor((diff % 3600) / 60);
      const secs = diff % 60;
      if (hrs > 0) {
        setCountdownText(`${hrs}h ${mins}m ${secs}s`);
      } else {
        setCountdownText(`${mins}m ${secs}s`);
      }
    };

    updateCountdown();
    const timer = setInterval(updateCountdown, 1000);
    return () => clearInterval(timer);
  }, [status?.schedule]);

  const handleCopyLogs = () => {
    const text = logs.join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleScheduleSubmit = (e) => {
    e.preventDefault();
    let start_in_seconds = 0;
    let target_iso_time = null;

    if (scheduleMode === 'delay') {
      const mins = parseFloat(delayMinutes) || 5;
      start_in_seconds = Math.max(10, Math.round(mins * 60));
      target_iso_time = new Date(Date.now() + start_in_seconds * 1000).toISOString();
    } else {
      if (!specificTime) return;
      const [h, m] = specificTime.split(':').map(Number);
      const now = new Date();
      const target = new Date();
      target.setHours(h, m, 0, 0);
      if (target.getTime() <= now.getTime()) {
        target.setDate(target.getDate() + 1);
      }
      start_in_seconds = Math.max(10, Math.floor((target.getTime() - now.getTime()) / 1000));
      target_iso_time = target.toISOString();
    }

    if (onSchedule) {
      onSchedule({
        start_in_seconds,
        duration_minutes: parseInt(autoStopMinutes, 10) || null,
        target_iso_time,
        auto_stake: autoStake,
      });
    }
  };

  const balanceFormatted = status?.balance !== null && status?.balance !== undefined 
    ? `₦${Number(status.balance).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` 
    : 'Live Synced';

  const isStaking = Boolean(status?.is_staking);
  const isRunning = Boolean(status?.is_running);
  const isReconnecting = status?.state === 'RECONNECTING';
  const isScheduleActive = Boolean(status?.schedule?.active);

  return (
    <div className="space-y-6">
      {/* Reconnecting Alert Banner */}
      {isReconnecting && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-pulse shadow-lg shadow-amber-950/30">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
              <RefreshCw className="w-5 h-5 animate-spin" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-amber-300">Network Reconnection in Progress</h4>
              <p className="text-xs text-amber-400/90">{status?.status_text || 'Attempting to re-establish game connection...'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onPause}
              disabled={loadingAction}
              className="px-3 py-1.5 bg-amber-600/80 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold transition-all shadow-md active:scale-95"
            >
              Pause Staking
            </button>
            <button
              onClick={onStop}
              disabled={loadingAction}
              className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold transition-all shadow-md active:scale-95"
            >
              Cancel Retry & Stop
            </button>
          </div>
        </div>
      )}

      {/* Active Schedule Banner */}
      {isScheduleActive && (
        <div className="p-4 rounded-xl bg-gradient-to-r from-cyan-950/60 to-blue-950/60 border border-cyan-500/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg shadow-cyan-950/40">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
              <Clock className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h4 className="text-sm font-bold text-cyan-300">Automated Schedule Armed on Server</h4>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono border ${
                  status.schedule?.auto_stake !== false
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                    : 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30'
                }`}>
                  {status.schedule?.auto_stake !== false ? 'LIVE AUTO-STAKING' : 'ODDS DATA EXTRACTION ONLY'}
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30">
                  VISIBLE BROWSER
                </span>
              </div>
              <p className="text-xs text-cyan-200/90 mt-1">
                {countdownText ? (
                  <span>Auto-starting in: <b className="text-white font-mono text-sm px-1.5 py-0.5 bg-cyan-950/80 rounded border border-cyan-700/50">{countdownText}</b> ({new Date(status.schedule.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })})</span>
                ) : (
                  <span>Armed to start at {status.schedule.start_time ? new Date(status.schedule.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'target time'}</span>
                )}
                {status.schedule.duration_minutes ? ` • Auto-stop after ${status.schedule.duration_minutes}m` : ' • Staking indefinitely'}
                {status.schedule?.auto_stake === false && ' • (No real bets will be placed)'}
              </p>
            </div>
          </div>
          <button
            onClick={onCancelSchedule}
            disabled={loadingAction}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-rose-600/80 hover:bg-rose-500 text-white rounded-xl text-xs font-semibold transition-all shadow-md active:scale-95 flex-shrink-0"
          >
            <XCircle className="w-4 h-4" />
            <span>Cancel Schedule</span>
          </button>
        </div>
      )}

      {/* Top Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Balance Card */}
        <div className="glass-card p-5 relative overflow-hidden border-emerald-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Account Balance</span>
            <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400">
              <Wallet className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              {balanceFormatted}
            </span>
          </div>
          <div className="mt-2 flex items-center gap-1.5 text-xs text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 live-pulse"></span>
            <span>Live iLOTBET Balance</span>
          </div>
        </div>

        {/* Current Next Stake */}
        <div className="glass-card p-5 relative overflow-hidden border-blue-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Next Calculated Stake</span>
            <div className="p-2 bg-blue-500/10 rounded-xl text-blue-400">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl lg:text-3xl font-bold text-white tracking-tight">
              ₦{Number(status?.current_stake || 50).toFixed(2)}
            </span>
          </div>
          <div className="mt-2 text-xs text-gray-400 flex items-center gap-1">
            <span>Strategy:</span>
            <span className="font-semibold text-blue-400 uppercase">{status?.strategy || 'Martingale'}</span>
          </div>
        </div>

        {/* Loss Streak */}
        <div className="glass-card p-5 relative overflow-hidden border-amber-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Current Loss Streak</span>
            <div className="p-2 bg-amber-500/10 rounded-xl text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-2xl lg:text-3xl font-bold text-amber-400 tracking-tight">
              {status?.loss_streak || 0}
            </span>
            <span className="text-xs text-gray-500 ml-1">/ 5 max</span>
          </div>
          <div className="mt-2 text-xs text-gray-400">
            <span>Risk Manager Guard Active</span>
          </div>
        </div>

        {/* Bot State */}
        <div className="glass-card p-5 relative overflow-hidden border-purple-500/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Bot Status</span>
            <div className="p-2 bg-purple-500/10 rounded-xl text-purple-400">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${isReconnecting ? 'bg-amber-400 live-pulse' : isStaking ? 'bg-emerald-400 live-pulse' : isRunning ? 'bg-cyan-400 live-pulse' : 'bg-gray-500'}`}></span>
            <span className={`text-lg lg:text-xl font-bold uppercase tracking-tight flex items-center gap-1.5 ${isReconnecting ? 'text-amber-400' : isStaking ? 'text-emerald-400' : isRunning ? 'text-cyan-400' : 'text-white'}`}>
              {isReconnecting && <RefreshCw className="w-4 h-4 animate-spin text-amber-400" />}
              {isReconnecting ? 'RECONNECTING' : isStaking ? 'STAKING LIVE' : isRunning ? 'OBSERVING (NO BETS)' : (status?.state || 'IDLE')}
            </span>
          </div>
          <div className="mt-2 text-xs text-gray-400 truncate">
            {isStaking ? (status?.status_text || 'Live betting active') : isRunning ? 'Extracting live odds (₦0 risked)' : (status?.status_text || 'Ready for command')}
          </div>
        </div>
      </div>

      {/* Action Control Panel */}
      <div className="glass-card p-6 border-red-500/20 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
            <Zap className="w-4 h-4 text-red-500" />
            Bot Control Deck
          </h3>
          <button
            onClick={() => setShowSchedulerCard(prev => !prev)}
            className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium px-2.5 py-1 rounded-lg bg-cyan-950/40 border border-cyan-800/40 transition-colors"
          >
            <Clock className="w-3.5 h-3.5" />
            <span>{showSchedulerCard ? 'Hide Scheduler' : 'Schedule Auto-Start'}</span>
            {showSchedulerCard ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Dynamic Mode Status Banner */}
        {isRunning && (
          <div className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
            isStaking
              ? 'bg-red-950/40 border-red-500/50 text-red-200 shadow-md shadow-red-950/30'
              : 'bg-cyan-950/40 border-cyan-500/40 text-cyan-200 shadow-md shadow-cyan-950/30'
          }`}>
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${isStaking ? 'bg-red-500/20 text-red-400' : 'bg-cyan-500/20 text-cyan-400'}`}>
                {isStaking ? <AlertOctagon className="w-5 h-5 animate-pulse" /> : <Eye className="w-5 h-5 animate-pulse" />}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className={`font-bold uppercase tracking-wider text-xs ${isStaking ? 'text-red-300' : 'text-cyan-300'}`}>
                    {isStaking ? 'Live Staking Mode Active' : 'Odds Observation Mode (No Bets)'}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                    isStaking 
                      ? 'bg-red-500/20 text-red-300 border border-red-500/30' 
                      : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  }`}>
                    {isStaking ? 'REAL MONEY AT RISK' : '₦0 RISKED (ZERO BETS)'}
                  </span>
                </div>
                <p className="text-xs text-gray-300 mt-0.5">
                  {isStaking 
                    ? 'Automated stakes are actively being submitted to the Aviator interface based on strategy.' 
                    : 'Visible browser is open and reading live round multipliers into the database without betting.'}
                </p>
              </div>
            </div>
            {!isStaking && (
              <button
                onClick={onStart}
                disabled={loadingAction}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold transition-all shadow-md active:scale-95 flex-shrink-0"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Start Live Staking Now</span>
              </button>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Prepare Button */}
          <button
            id="btn-prepare-game"
            onClick={onPrepare}
            disabled={loadingAction}
            className={`flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transform active:scale-95 ${
              isRunning && !isStaking
                ? 'bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 shadow-cyan-500/25 ring-1 ring-cyan-400/40'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-blue-500/25'
            }`}
          >
            <Rocket className="w-4 h-4" />
            <span>{isRunning ? '1. Verify / Focus Browser' : '1. Prepare Game UI'}</span>
          </button>

          {/* Start Live Staking Button */}
          <button
            id="btn-start-staking"
            onClick={onStart}
            disabled={loadingAction || isStaking}
            className={`flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-500/25 disabled:opacity-50 disabled:cursor-not-allowed transform active:scale-95 ${
              isRunning && !isStaking ? 'animate-pulse ring-2 ring-emerald-400/50' : ''
            }`}
          >
            <Play className="w-4 h-4 fill-current" />
            <span>2. Authorize & Start Staking</span>
          </button>

          {/* Pause Staking Button */}
          <button
            id="btn-pause-staking"
            onClick={onPause}
            disabled={loadingAction || !isStaking}
            className="flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 bg-gradient-to-r from-amber-600 to-yellow-600 hover:from-amber-500 hover:to-yellow-500 text-white shadow-lg shadow-amber-500/25 disabled:opacity-50 disabled:cursor-not-allowed transform active:scale-95"
          >
            <Pause className="w-4 h-4 fill-current" />
            <span>Pause Live Staking</span>
          </button>

          {/* Stop / Emergency Stop Button */}
          <button
            id="btn-emergency-stop"
            onClick={onStop}
            disabled={loadingAction || !isRunning}
            className={`flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-semibold text-sm transition-all duration-200 shadow-lg disabled:opacity-40 disabled:cursor-not-allowed transform active:scale-95 ${
              isStaking
                ? 'bg-gradient-to-r from-red-600 to-rose-700 hover:from-red-500 hover:to-rose-600 text-white shadow-red-500/30'
                : isRunning
                ? 'bg-gradient-to-r from-slate-700 to-gray-800 hover:from-slate-600 hover:to-gray-700 text-gray-200 border border-gray-600/50 shadow-black/40'
                : 'bg-gray-800 text-gray-500 border border-gray-700/40'
            }`}
          >
            {isStaking ? (
              <>
                <AlertOctagon className="w-4 h-4" />
                <span>Emergency Stop (Halt Bets)</span>
              </>
            ) : isRunning ? (
              <>
                <Square className="w-4 h-4 fill-current text-slate-300" />
                <span>Stop & Close Browser</span>
              </>
            ) : (
              <>
                <Square className="w-4 h-4 fill-current" />
                <span>Emergency Stop</span>
              </>
            )}
          </button>
        </div>

        {/* Expandable Automated Scheduler Card */}
        {showSchedulerCard && (
          <div className="p-4 rounded-xl bg-gray-900/80 border border-cyan-500/30 space-y-4 animate-in fade-in duration-200">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <h4 className="text-xs font-bold text-white uppercase tracking-wider">Automated Scheduler (Timed Auto-Start)</h4>
              </div>
              <span className="text-[11px] text-gray-400">Server-side execution</span>
            </div>

            <form onSubmit={handleScheduleSubmit} className="space-y-4">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setScheduleMode('delay')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    scheduleMode === 'delay'
                      ? 'bg-cyan-600 text-white shadow-sm shadow-cyan-500/30'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  Countdown Delay
                </button>
                <button
                  type="button"
                  onClick={() => setScheduleMode('time')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                    scheduleMode === 'time'
                      ? 'bg-cyan-600 text-white shadow-sm shadow-cyan-500/30'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  Specific Clock Time
                </button>
              </div>

              {scheduleMode === 'delay' ? (
                <div className="space-y-2">
                  <label className="block text-xs font-medium text-gray-400">
                    Start in how many minutes?
                  </label>
                  <div className="flex items-center gap-2">
                    {[5, 15, 30, 60, 120].map(mins => (
                      <button
                        key={mins}
                        type="button"
                        onClick={() => setDelayMinutes(mins)}
                        className={`px-2.5 py-1 rounded-md text-xs font-mono transition-colors ${
                          delayMinutes === mins
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/50'
                            : 'bg-gray-800/80 text-gray-400 hover:bg-gray-700'
                        }`}
                      >
                        +{mins >= 60 ? `${mins / 60}h` : `${mins}m`}
                      </button>
                    ))}
                    <input
                      type="number"
                      min="1"
                      max="1440"
                      value={delayMinutes}
                      onChange={(e) => setDelayMinutes(Math.max(1, parseInt(e.target.value, 10) || 1))}
                      className="w-20 bg-gray-950 border border-gray-700 rounded-md px-2.5 py-1 text-xs text-white font-mono text-center focus:border-cyan-500 focus:outline-none"
                    />
                    <span className="text-xs text-gray-400">mins</span>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <label className="block text-xs font-medium text-gray-400">
                    Target Time (today or tomorrow if passed)
                  </label>
                  <input
                    type="time"
                    value={specificTime}
                    onChange={(e) => setSpecificTime(e.target.value)}
                    required={scheduleMode === 'time'}
                    className="bg-gray-950 border border-gray-700 rounded-md px-3 py-1.5 text-sm text-white font-mono focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              )}

              {/* Scheduled Actions Selection (Prepare UI is mandatory, Staking is optional) */}
              <div className="space-y-3 p-3.5 bg-gray-950/70 rounded-xl border border-gray-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Scheduled Actions</span>
                  <span className="text-[10px] text-emerald-400 font-mono bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    Browser Opens Visibly (Non-Headless)
                  </span>
                </div>

                {/* Step 1: Prepare Game UI (Mandatory) */}
                <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-blue-950/20 border border-blue-800/30 text-xs">
                  <CheckCircle2 className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-blue-200">1. Prepare Game UI & Open Visible Browser</span>
                      <span className="text-[10px] uppercase font-bold text-amber-400 bg-amber-950/50 px-1.5 py-0.2 rounded border border-amber-800/50">Mandatory</span>
                    </div>
                    <p className="text-[11px] text-gray-400 mt-0.5">
                      Launches visible Chrome browser window, logs into game session, switches to Auto tab, locks Auto Cash Out at 1.50x, and begins real-time odds collection.
                    </p>
                  </div>
                </div>

                {/* Step 2: Auto-Stake Option */}
                <div className="p-2.5 rounded-lg bg-gray-900/60 border border-gray-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className={`w-4 h-4 ${autoStake ? 'text-emerald-400' : 'text-gray-500'}`} />
                      <span className="text-xs font-semibold text-white">2. Live Staking Mode</span>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={autoStake}
                        onChange={(e) => setAutoStake(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                    </label>
                  </div>

                  <div className="text-[11px] text-gray-400">
                    {autoStake ? (
                      <span className="text-emerald-300">
                        <b>Active Live Staking:</b> After preparing, automatically starts placing bets at ₦{Number(status?.current_stake || 50).toFixed(2)} with loss progression.
                      </span>
                    ) : (
                      <span className="text-cyan-300">
                        <b>Observation & Odds Extraction Only:</b> The browser opens visibly and collects all round multipliers into the database & SafeZone analytics, but <u>no real bets will be placed</u>.
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Auto-Stop Duration Option */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1">
                    Auto-Stop Session Limit (Optional)
                  </label>
                  <select
                    value={autoStopMinutes}
                    onChange={(e) => setAutoStopMinutes(parseInt(e.target.value, 10))}
                    className="w-full bg-gray-950 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white focus:border-cyan-500 focus:outline-none"
                  >
                    <option value={0}>Run indefinitely until stopped manually</option>
                    <option value={15}>Stop automatically after 15 mins</option>
                    <option value={30}>Stop automatically after 30 mins</option>
                    <option value={60}>Stop automatically after 1 hour</option>
                    <option value={120}>Stop automatically after 2 hours</option>
                    <option value={240}>Stop automatically after 4 hours</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-gray-800">
                <p className="text-[11px] text-gray-400">
                  Runs on backend. You can close your browser or phone screen once scheduled.
                </p>
                <button
                  type="submit"
                  disabled={loadingAction || isScheduleActive}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-md shadow-cyan-500/25 disabled:opacity-50"
                >
                  <BellRing className="w-3.5 h-3.5" />
                  <span>Arm Schedule</span>
                </button>
              </div>
            </form>
          </div>
        )}

        <div className="mt-4 p-3 bg-gray-900/60 rounded-xl border border-gray-800 flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span><b>Automated Protections:</b> Auto Cashout Switch, Network Auto-Recovery, Stop-Loss Guard.</span>
          </div>
          <span className="text-gray-500 font-mono">Backend: Django + PostgreSQL</span>
        </div>
      </div>

      {/* Live Event Terminal Console */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Live System & Event Console</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyLogs}
              className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors text-xs flex items-center gap-1"
              title="Copy logs"
            >
              <Copy className="w-3.5 h-3.5" />
              <span>{copied ? 'Copied!' : 'Copy'}</span>
            </button>
            <button
              onClick={onClearLogs}
              className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-rose-400 transition-colors text-xs flex items-center gap-1"
              title="Clear logs"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        <div className="bg-black/80 rounded-xl p-4 font-mono text-xs text-gray-300 h-64 overflow-y-auto border border-gray-800 space-y-1">
          {logs && logs.length > 0 ? (
            logs.map((log, idx) => (
              <div key={idx} className="leading-relaxed flex items-start gap-2">
                <span className="text-gray-600 select-none">[{idx + 1}]</span>
                <span className={
                  log.includes('Result') ? (log.includes('+') ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold')
                  : log.includes('Extracted') || log.includes('extracted_result') ? 'text-blue-400'
                  : log.includes('Error') ? 'text-rose-500 font-bold'
                  : log.includes('Schedule') ? 'text-cyan-300 font-semibold'
                  : log.includes('Network') || log.includes('Reconnecting') ? 'text-amber-400 font-semibold'
                  : log.includes('Ready') ? 'text-emerald-300'
                  : 'text-gray-300'
                }>
                  {log}
                </span>
              </div>
            ))
          ) : (
            <div className="text-gray-600 italic py-4 text-center">No events received yet. Tap "1. Prepare Game UI" to start.</div>
          )}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  );
}
