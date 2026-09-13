import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BrainCircuit,
  ShieldCheck,
  TrendingUp,
  Activity,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Cpu,
  Bot,
  Zap,
  Target,
  Sparkles,
  Layers,
  Lock,
  ArrowRight
} from 'lucide-react';
import { API_BASE } from '../config';

export default function AIAgentDeckTab({ config, onUpdateConfig }) {
  const [swarmData, setSwarmData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState(null);
  const [autonomousMode, setAutonomousMode] = useState(config?.ai_autonomous_mode || false);

  useEffect(() => {
    fetchSwarmStatus();
    const interval = setInterval(fetchSwarmStatus, 6000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (config?.ai_autonomous_mode !== undefined) {
      setAutonomousMode(config.ai_autonomous_mode);
    }
  }, [config?.ai_autonomous_mode]);

  const fetchSwarmStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/ai/swarm/status/`);
      if (res.data?.consensus) {
        setSwarmData(res.data.consensus);
        if (res.data.autonomous_mode !== undefined) {
          setAutonomousMode(res.data.autonomous_mode);
        }
      }
      setError(null);
    } catch (err) {
      console.error('Failed to fetch swarm status:', err);
    }
  };

  const triggerEvaluation = async () => {
    setEvaluating(true);
    try {
      const res = await axios.post(`${API_BASE}/ai/swarm/evaluate/`);
      if (res.data?.consensus) {
        setSwarmData(res.data.consensus);
      }
    } catch (err) {
      setError('Evaluation failed. Please verify API key in settings.');
    } finally {
      setEvaluating(false);
    }
  };

  const toggleAutonomousMode = async () => {
    const nextVal = !autonomousMode;
    setAutonomousMode(nextVal);
    try {
      await axios.put(`${API_BASE}/settings/`, {
        ai_autonomous_mode: nextVal
      });
      if (onUpdateConfig) {
        onUpdateConfig({ ai_autonomous_mode: nextVal });
      }
    } catch (err) {
      console.error('Failed to update autonomous mode:', err);
      setAutonomousMode(!nextVal); // revert on error
    }
  };

  const getDirectiveBadge = (directive) => {
    switch (directive) {
      case 'BET':
      case 'RESUME_STAKING':
        return {
          bg: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
          icon: CheckCircle2,
          text: 'STAKE AUTHORIZED'
        };
      case 'CAUTION':
        return {
          bg: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
          icon: AlertTriangle,
          text: 'ELEVATED CAUTION'
        };
      case 'PAUSE_STAKING':
        return {
          bg: 'bg-red-500/20 text-red-400 border-red-500/30',
          icon: Lock,
          text: 'STAKING VETOED / PAUSED'
        };
      default:
        return {
          bg: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
          icon: Activity,
          text: directive || 'OBSERVING'
        };
    }
  };

  const agents = swarmData?.agents || {};
  const analyst = agents.analyst;
  const riskGuardian = agents.risk_guardian;
  const strategyOptimizer = agents.strategy_optimizer;
  const supervisor = agents.supervisor;

  const directiveBadge = getDirectiveBadge(swarmData?.consensus_directive);
  const DirectiveIcon = directiveBadge.icon;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner: Enterprise Swarm Header */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-gray-950 via-gray-900 to-gray-950 border border-gray-800 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-2xl bg-gradient-to-br from-red-600 to-rose-700 shadow-lg shadow-red-900/30">
                <BrainCircuit className="w-7 h-7 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-black text-white tracking-wide flex items-center gap-2">
                  Enterprise Multi-Agent Collaborative Swarm
                  <span className="text-xs font-mono font-normal px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    Live Consensus
                  </span>
                </h2>
                <p className="text-xs text-gray-400">
                  Four specialized quantitative agents analyze live telemetry simultaneously to optimize EV and protect bankroll capital.
                </p>
              </div>
            </div>
          </div>

          {/* Right Controls: Autonomous Toggle & Manual Refresh */}
          <div className="flex flex-wrap items-center gap-3">
            {/* Autonomous Switch */}
            <div className="flex items-center gap-3 px-4 py-2 rounded-2xl bg-gray-900/90 border border-gray-800">
              <div>
                <div className="text-xs font-bold text-gray-200">Autonomous AI Mode</div>
                <div className="text-[10px] text-gray-400">Auto-pause on cold streaks</div>
              </div>
              <button
                onClick={toggleAutonomousMode}
                className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  autonomousMode ? 'bg-purple-600' : 'bg-gray-800'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                    autonomousMode ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            {/* Evaluate Button */}
            <button
              onClick={triggerEvaluation}
              disabled={evaluating}
              className="flex items-center gap-2 px-4 py-2.5 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-semibold text-xs transition-all shadow-lg shadow-red-900/20 active:scale-95 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${evaluating ? 'animate-spin' : ''}`} />
              <span>{evaluating ? 'Evaluating Swarm...' : 'Re-Evaluate Telemetry'}</span>
            </button>
          </div>
        </div>

        {/* Executive Consensus Card */}
        {swarmData && (
          <div className="mt-6 p-5 rounded-2xl bg-black/40 border border-gray-800/80 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            <div className="md:col-span-4 space-y-2">
              <div className="text-[11px] font-mono text-gray-400 uppercase tracking-wider">
                Swarm Executive Consensus
              </div>
              <div className="flex items-center gap-3">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-extrabold tracking-wide ${directiveBadge.bg}`}>
                  <DirectiveIcon className="w-4 h-4" />
                  <span>{directiveBadge.text}</span>
                </div>
                <span className="text-2xl font-black text-white font-mono">
                  {swarmData.consensus_score}%
                </span>
              </div>
              <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full transition-all duration-700 ${
                    swarmData.consensus_score >= 70
                      ? 'bg-emerald-400'
                      : swarmData.consensus_score >= 50
                      ? 'bg-amber-400'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(100, Math.max(5, swarmData.consensus_score || 50))}%` }}
                ></div>
              </div>
            </div>

            <div className="md:col-span-8 space-y-2">
              <div className="text-xs text-gray-300 font-medium leading-relaxed">
                {swarmData.consensus_summary}
              </div>
              {swarmData.recommendations && swarmData.recommendations.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {swarmData.recommendations.map((rec, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-lg bg-gray-800/80 border border-gray-750 text-[11px] text-gray-300 flex items-center gap-1.5"
                    >
                      <ArrowRight className="w-3 h-3 text-red-400 shrink-0" />
                      {rec}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 4 Specialized Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Agent 1: Market Pattern Analyst */}
        <div className="p-5 rounded-3xl bg-gray-950/80 border border-gray-850 hover:border-gray-750 transition-all flex flex-col justify-between space-y-4 shadow-xl">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white">Pattern Analyst</h3>
                  <div className="text-[10px] text-gray-400">Pattern & Streak Detective</div>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {analyst?.directive || 'BET'}
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-gray-900/60 border border-gray-850 text-xs text-gray-300 leading-relaxed min-h-[90px]">
              {analyst?.reasoning || 'Observing live multiplier sequence for streak clustering...'}
            </div>

            {/* Analyst Metrics */}
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 rounded-xl bg-black/40 border border-gray-850">
                <div className="text-gray-500 text-[10px]">SafeZone Win Rate</div>
                <div className="font-mono font-bold text-emerald-400">
                  {analyst?.metrics?.safezone_win_rate || 0}%
                </div>
              </div>
              <div className="p-2 rounded-xl bg-black/40 border border-gray-850">
                <div className="text-gray-500 text-[10px]">Active Loss Streak</div>
                <div className={`font-mono font-bold ${(analyst?.metrics?.current_loss_streak || 0) >= 3 ? 'text-red-400' : 'text-gray-200'}`}>
                  {analyst?.metrics?.current_loss_streak || 0} rounds
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-gray-850 flex items-center justify-between text-[10px] text-gray-400 font-mono">
            <span>Confidence: {analyst?.confidence || 0}%</span>
            <span className="uppercase text-blue-400">{analyst?.sentiment || 'NEUTRAL'}</span>
          </div>
        </div>

        {/* Agent 2: Capital Risk Guardian */}
        <div className="p-5 rounded-3xl bg-gray-950/80 border border-gray-850 hover:border-gray-750 transition-all flex flex-col justify-between space-y-4 shadow-xl">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white">Risk Guardian</h3>
                  <div className="text-[10px] text-gray-400">Capital Preservation</div>
                </div>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded ${
                riskGuardian?.directive === 'PAUSE_STAKING'
                  ? 'bg-red-500/20 text-red-300 border border-red-500/30'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              }`}>
                {riskGuardian?.directive || 'BET'}
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-gray-900/60 border border-gray-850 text-xs text-gray-300 leading-relaxed min-h-[90px]">
              {riskGuardian?.reasoning || 'Monitoring drawdown thresholds, max stake exposure, and safety limits...'}
            </div>

            {/* Risk Guardian Metrics */}
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 rounded-xl bg-black/40 border border-gray-850">
                <div className="text-gray-500 text-[10px]">Remaining Steps</div>
                <div className="font-mono font-bold text-gray-200">
                  {riskGuardian?.metrics?.remaining_loss_steps ?? 5} steps
                </div>
              </div>
              <div className="p-2 rounded-xl bg-black/40 border border-gray-850">
                <div className="text-gray-500 text-[10px]">Stop-Loss Prox.</div>
                <div className="font-mono font-bold text-amber-400">
                  {riskGuardian?.metrics?.stop_loss_proximity_pct || 0}%
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-gray-850 flex items-center justify-between text-[10px] text-gray-400 font-mono">
            <span>Confidence: {riskGuardian?.confidence || 0}%</span>
            <span className="uppercase text-red-400">{riskGuardian?.sentiment || 'NEUTRAL'}</span>
          </div>
        </div>

        {/* Agent 3: Strategy & EV Tactician */}
        <div className="p-5 rounded-3xl bg-gray-950/80 border border-gray-850 hover:border-gray-750 transition-all flex flex-col justify-between space-y-4 shadow-xl">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
                  <Target className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white">Strategy Tactician</h3>
                  <div className="text-[10px] text-gray-400">Expected Value & Cashout</div>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                {strategyOptimizer?.directive || 'BET'}
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-gray-900/60 border border-gray-850 text-xs text-gray-300 leading-relaxed min-h-[90px]">
              {strategyOptimizer?.reasoning || 'Calculating empirical EV and cashout optimization matrices...'}
            </div>

            {/* Strategy Tactician Metrics */}
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 rounded-xl bg-black/40 border border-gray-850">
                <div className="text-gray-500 text-[10px]">Empirical EV / Unit</div>
                <div className={`font-mono font-bold ${(strategyOptimizer?.metrics?.ev_per_unit || 0) >= 0 ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {(strategyOptimizer?.metrics?.ev_per_unit || 0) > 0 ? '+' : ''}
                  {strategyOptimizer?.metrics?.ev_per_unit || 0}
                </div>
              </div>
              <div className="p-2 rounded-xl bg-black/40 border border-gray-850">
                <div className="text-gray-500 text-[10px]">Alt 1.35x Win Rate</div>
                <div className="font-mono font-bold text-purple-400">
                  {strategyOptimizer?.metrics?.alt_135_win_prob || 0}%
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-gray-850 flex items-center justify-between text-[10px] text-gray-400 font-mono">
            <span>Confidence: {strategyOptimizer?.confidence || 0}%</span>
            <span className="uppercase text-purple-400">{strategyOptimizer?.sentiment || 'NEUTRAL'}</span>
          </div>
        </div>

        {/* Agent 4: Swarm Executive Supervisor */}
        <div className="p-5 rounded-3xl bg-gray-950/80 border border-gray-850 hover:border-gray-750 transition-all flex flex-col justify-between space-y-4 shadow-xl">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
                  <Cpu className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white">Swarm Supervisor</h3>
                  <div className="text-[10px] text-gray-400">Executive Synthesizer</div>
                </div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                DIRECTIVE
              </span>
            </div>

            <div className="p-3 rounded-2xl bg-gray-900/60 border border-gray-850 text-xs text-gray-300 leading-relaxed min-h-[90px]">
              {supervisor?.reasoning || 'Synthesizing agent votes using 40/35/25 weighted risk distribution...'}
            </div>

            {/* Supervisor Logic Summary */}
            <div className="p-2.5 rounded-xl bg-black/40 border border-gray-850 text-[10px] text-gray-400 space-y-1">
              <div className="flex justify-between font-mono">
                <span>Veto Power:</span>
                <span className="text-emerald-400 font-bold">Safety First</span>
              </div>
              <div className="flex justify-between font-mono">
                <span>Consensus Agreement:</span>
                <span className="text-white font-bold">{swarmData?.consensus_score || 0}%</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-gray-850 flex items-center justify-between text-[10px] text-gray-400 font-mono">
            <span>Executive Score: {swarmData?.consensus_score || 0}%</span>
            <span className="uppercase text-amber-400">{swarmData?.consensus_sentiment || 'NEUTRAL'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
