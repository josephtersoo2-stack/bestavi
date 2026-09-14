import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Sliders, 
  Save, 
  Calculator, 
  AlertCircle, 
  RefreshCw, 
  CheckCircle2, 
  Wifi, 
  ShieldAlert,
  Layers,
  BrainCircuit,
  Key,
  Cpu
} from 'lucide-react';
import { API_BASE } from '../config';

export default function SettingsTab({ settings, onSave, saving }) {
  const [formData, setFormData] = useState({
    base_stake: 50.0,
    strategy: 'martingale',
    multiplier: 3.0,
    auto_cashout: 1.50,
    max_stake: 5000.0,
    max_loss_steps: 5,
    stop_loss: 10000.0,
    profit_target: 5000.0,
    dry_run: false,
    ceiling_rule: true,
    network_auto_retry: true,
    network_retry_delay: 10,
    network_max_retries: 5,
    site: 'ilotbet',
    platform: 'ilotbet',
    game: 'aviator',
    game_url: '',
    ai_enabled: true,
    ai_autonomous_mode: false,
    ai_provider: 'gemini',
    ai_model: 'gemini-3.6-flash',
    gemini_api_key: '',
    openrouter_api_key: '',
    ai_risk_tolerance: 'conservative',
  });

  const [savedSuccess, setSavedSuccess] = useState(false);
  const [platformsList, setPlatformsList] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);

  useEffect(() => {
    fetchPlatforms();
  }, []);

  useEffect(() => {
    if (settings) {
      setFormData(prev => ({
        ...prev,
        ...settings,
        platform: settings.platform || settings.site || 'ilotbet',
        game: settings.game || 'aviator',
        // Keep credential inputs empty if already securely encrypted in DB
        gemini_api_key: '',
        openrouter_api_key: '',
        game_url: (settings.game_url && settings.game_url.includes('REDACTED')) ? '' : '',
      }));
    }
  }, [settings]);


  useEffect(() => {
    if (formData.ai_provider) {
      fetchModels(formData.ai_provider);
    }
  }, [formData.ai_provider]);

  const fetchPlatforms = async () => {
    try {
      const res = await axios.get(`${API_BASE}/platforms/`);
      setPlatformsList(res.data.platforms || []);
    } catch (err) {
      console.error('Failed to load platforms:', err);
    }
  };

  const fetchModels = async (prov) => {
    setLoadingModels(true);
    try {
      const res = await axios.get(`${API_BASE}/ai/models/?provider=${prov}`);
      setAvailableModels(res.data.models || []);
    } catch (err) {
      console.error('Failed to load AI models:', err);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    let val = type === 'checkbox' ? checked : value;

    if (type === 'number') {
      val = parseFloat(value) || 0;
    }

    setFormData(prev => {
      const updated = { ...prev, [name]: val };
      if (name === 'platform') {
        updated.site = val;
        // Auto select first game of selected platform
        const plat = platformsList.find(p => p.id === val);
        if (plat && plat.games.length > 0) {
          updated.game = plat.games[0].id;
        }
      }
      // Auto suggest loss multiplier when auto cashout changes
      if (name === 'auto_cashout' && updated.strategy === 'martingale') {
        const odds = parseFloat(val);
        if (odds > 1.0) {
          const suggested = Math.max(1.01, Math.round((odds / (odds - 1.0)) * 10000) / 10000);
          updated.multiplier = suggested;
        }
      }
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (onSave) {
      await onSave(formData);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    }
  };

  // Calculate projected stakes simulation across consecutive losses
  const generateEscalationTable = () => {
    const base = Number(formData.base_stake) || 50;
    const mult = Number(formData.multiplier) || 3;
    const maxSteps = Number(formData.max_loss_steps) || 5;
    const maxStake = Number(formData.max_stake) || 5000;
    const cashout = Number(formData.auto_cashout) || 1.5;
    const isCeiling = formData.ceiling_rule ?? (formData.platform === 'ilotbet');

    const rows = [];
    let current = isCeiling ? Math.ceil(base) : base;
    let totalInvested = 0;

    for (let i = 0; i <= maxSteps; i++) {
      if (i > 0) {
        if (formData.strategy === 'martingale') {
          current = isCeiling ? Math.ceil(current * mult) : Math.round(current * mult * 100) / 100;
        } else if (formData.strategy === 'dalembert') {
          current = current + base;
        } else if (formData.strategy === 'flat') {
          current = isCeiling ? Math.ceil(base) : base;
        }
      }
      totalInvested += current;
      const profitOnWin = current * cashout - totalInvested;
      const exceedsMax = current > maxStake;

      rows.push({
        step: i,
        stake: current,
        totalInvested,
        profitOnWin,
        exceedsMax,
      });

      if (exceedsMax) break;
    }
    return rows;
  };

  const escalationRows = generateEscalationTable();
  const currentPlatformObj = platformsList.find(p => p.id === formData.platform) || platformsList[0];
  const currentSupportedGames = currentPlatformObj ? currentPlatformObj.games : [];

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Parameters Card */}
          <div className="lg:col-span-2 space-y-6">
            {/* Section 1: Platform & Multi-Game Addon Selection */}
            <div className="glass-card p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-red-500" />
                  <h3 className="text-base font-semibold text-white">Platform & Game Addon Selection</h3>
                </div>
                <span className="text-[11px] text-emerald-400 font-mono">MODULAR ADDON SYSTEM</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Platform */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Casino / Bookmaker Platform
                  </label>
                  <select
                    name="platform"
                    value={formData.platform}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                  >
                    {platformsList.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </select>
                  <span className="text-[11px] text-gray-500">Active platform addon module</span>
                </div>

                {/* Game Type */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Game Type
                  </label>
                  <select
                    name="game"
                    value={formData.game}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                  >
                    {currentSupportedGames.map(g => (
                      <option key={g.id} value={g.id}>
                        {g.name} ({g.category})
                      </option>
                    ))}
                  </select>
                  <span className="text-[11px] text-gray-500">Supported games inside selected platform</span>
                </div>
              </div>

              {/* Game URL Input */}
              <div className="pt-2">
                <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5 flex items-center justify-between">
                  <span>Game Session / Iframe URL</span>
                  {settings?.game_url && (
                    <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-semibold bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/60">
                      <CheckCircle2 className="w-3 h-3" /> Encrypted & Active
                    </span>
                  )}
                </label>
                <input
                  type="password"
                  name="game_url"
                  value={formData.game_url}
                  onChange={handleChange}
                  className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-xs text-gray-300 focus:outline-none focus:border-red-500 font-mono transition-colors"
                  placeholder={settings?.game_url ? "•••••••••••••••••••• (Encrypted at rest — leave blank to keep)" : "https://www.ilotbet.com/pc/iframe?url=..."}
                />
                <span className="text-[10px] text-gray-500">Session credentials & URL parameters are encrypted at rest</span>
              </div>
            </div>


            {/* Section 2: AI LLM Staking Copilot & Model Selection */}
            <div className="glass-card p-6 space-y-4 border-l-4 border-l-purple-600">
              <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="w-5 h-5 text-purple-400" />
                  <h3 className="text-base font-semibold text-white">AI LLM Intelligence & Model Configuration</h3>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    name="ai_enabled"
                    checked={formData.ai_enabled}
                    onChange={handleChange}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* AI Provider */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    AI Provider
                  </label>
                  <select
                    name="ai_provider"
                    value={formData.ai_provider}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors"
                  >
                    <option value="gemini">Google Gemini (AI Studio)</option>
                    <option value="openrouter">OpenRouter.ai (Multi-Model)</option>
                  </select>
                  <span className="text-[11px] text-gray-500">Select active intelligence backend</span>
                </div>

                {/* AI Model (Dynamic from platform) */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5 flex items-center justify-between">
                    <span>Active LLM Model</span>
                    {loadingModels && <RefreshCw className="w-3 h-3 animate-spin text-purple-400" />}
                  </label>
                  <select
                    name="ai_model"
                    value={formData.ai_model}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors font-mono"
                  >
                    {availableModels.map(m => (
                      <option key={m.id} value={m.id}>
                        {m.name || m.id}
                      </option>
                    ))}
                  </select>
                  <span className="text-[11px] text-gray-500">Dynamically queried from {formData.ai_provider} API</span>
                </div>
              </div>

              {/* API Keys Configuration */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5 flex items-center justify-between">
                    <span>Gemini API Key</span>
                    {settings?.has_gemini_key && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-semibold bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/60">
                        <CheckCircle2 className="w-3 h-3" /> Encrypted & Active
                      </span>
                    )}
                  </label>
                  <input
                    type="password"
                    name="gemini_api_key"
                    value={formData.gemini_api_key}
                    onChange={handleChange}
                    placeholder={settings?.has_gemini_key ? "•••••••••••••••••••• (Encrypted — enter new key to replace)" : "AIzaSy... or AQ...."}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-xs text-gray-300 focus:outline-none focus:border-purple-500 font-mono transition-colors"
                  />
                  <span className="text-[10px] text-gray-500">Leave blank to keep existing encrypted key</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5 flex items-center justify-between">
                    <span>OpenRouter API Key</span>
                    {settings?.has_openrouter_key && (
                      <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-semibold bg-emerald-950/60 px-2 py-0.5 rounded-full border border-emerald-800/60">
                        <CheckCircle2 className="w-3 h-3" /> Encrypted & Active
                      </span>
                    )}
                  </label>
                  <input
                    type="password"
                    name="openrouter_api_key"
                    value={formData.openrouter_api_key}
                    onChange={handleChange}
                    placeholder={settings?.has_openrouter_key ? "•••••••••••••••••••• (Encrypted — enter new key to replace)" : "sk-or-v1-..."}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-xs text-gray-300 focus:outline-none focus:border-purple-500 font-mono transition-colors"
                  />
                  <span className="text-[10px] text-gray-500">Leave blank to keep existing encrypted key</span>
                </div>
              </div>


              {/* Autonomous Mode Toggle */}
              <div className="flex items-center justify-between p-3.5 bg-purple-950/20 rounded-xl border border-purple-900/40">
                <div>
                  <h4 className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Cpu className="w-4 h-4 text-purple-400" />
                    Autonomous AI Safety Mode
                  </h4>
                  <p className="text-[11px] text-gray-400">
                    Allows the AI to automatically pause staking if critical consecutive loss clustering is detected.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    name="ai_autonomous_mode"
                    checked={formData.ai_autonomous_mode}
                    onChange={handleChange}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-purple-600"></div>
                </label>
              </div>
            </div>

            {/* Section 3: Staking & Mathematical Parameters */}
            <div className="glass-card p-6 space-y-6">
              <div className="flex items-center justify-between border-b border-gray-800 pb-4">
                <div className="flex items-center gap-2">
                  <Sliders className="w-5 h-5 text-red-500" />
                  <h3 className="text-base font-semibold text-white">Staking & Strategy Parameters</h3>
                </div>
                <span className="text-xs text-gray-500">Auto-saved to PostgreSQL</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Base Stake */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Base Stake (NGN)
                  </label>
                  <input
                    type="number"
                    name="base_stake"
                    step="0.0001"
                    min="0.0001"
                    value={formData.base_stake}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                    required
                  />
                  <span className="text-[11px] text-gray-500">Initial stake on every clean round</span>
                </div>

                {/* Strategy */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Staking Strategy
                  </label>
                  <select
                    name="strategy"
                    value={formData.strategy}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors"
                  >
                    <option value="martingale">Martingale (Multiply on Loss)</option>
                    <option value="dalembert">D'Alembert (Linear Addition)</option>
                    <option value="flat">Flat Stake (Constant)</option>
                    <option value="fibonacci">Fibonacci Sequence</option>
                  </select>
                  <span className="text-[11px] text-gray-500">Mathematical progression model</span>
                </div>

                {/* Auto Cashout Multiplier */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Auto Cash Out Target (x)
                  </label>
                  <input
                    type="number"
                    name="auto_cashout"
                    step="0.0001"
                    min="1.01"
                    max="100.0"
                    value={formData.auto_cashout}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                    required
                  />
                  <span className="text-[11px] text-gray-500">Target multiplier (e.g. 1.30x or 1.50x, up to 4 decimals)</span>
                </div>

                {/* Loss Escalation Multiplier */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Loss Multiplier (x)
                  </label>
                  <input
                    type="number"
                    name="multiplier"
                    step="0.0001"
                    min="1.01"
                    max="100.0"
                    value={formData.multiplier}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                    required
                  />
                  <span className="text-[11px] text-gray-500">Recommended: 3.0x for 1.50x, 4.33x for 1.30x (up to 4 decimals)</span>
                </div>

                {/* Maximum Loss Steps */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Max Loss Streak Steps
                  </label>
                  <input
                    type="number"
                    name="max_loss_steps"
                    min="1"
                    max="20"
                    step="1"
                    value={formData.max_loss_steps}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                    required
                  />
                  <span className="text-[11px] text-gray-500">Safety cutoff after consecutive losses</span>
                </div>

                {/* Maximum Single Stake */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Maximum Single Stake (NGN)
                  </label>
                  <input
                    type="number"
                    name="max_stake"
                    step="0.0001"
                    min="1"
                    value={formData.max_stake}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                    required
                  />
                  <span className="text-[11px] text-gray-500">Hard cap preventing runaway bets</span>
                </div>

                {/* Stop Loss */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Total Session Stop-Loss (NGN)
                  </label>
                  <input
                    type="number"
                    name="stop_loss"
                    step="0.0001"
                    min="1"
                    value={formData.stop_loss}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                    required
                  />
                  <span className="text-[11px] text-gray-500">Max loss before bot pauses automatically</span>
                </div>

                {/* Profit Target */}
                <div>
                  <label className="block text-xs font-semibold text-gray-400 uppercase mb-1.5">
                    Total Profit Target (NGN)
                  </label>
                  <input
                    type="number"
                    name="profit_target"
                    step="0.0001"
                    min="1"
                    value={formData.profit_target}
                    onChange={handleChange}
                    className="w-full bg-gray-900/80 border border-gray-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition-colors font-mono"
                    required
                  />
                  <span className="text-[11px] text-gray-500">Auto-stops once profit target is reached</span>
                </div>
              </div>

              {/* Ceiling Rule (Integer-Only Staking) */}
              <div className="flex items-start gap-3 p-3 bg-gray-900/60 rounded-xl border border-gray-800">
                <input
                  type="checkbox"
                  id="ceiling_rule"
                  name="ceiling_rule"
                  checked={formData.ceiling_rule ?? true}
                  onChange={handleChange}
                  className="w-4 h-4 mt-0.5 text-red-500 rounded bg-gray-800 border-gray-700 focus:ring-red-500"
                />
                <label htmlFor="ceiling_rule" className="text-xs text-gray-300 select-none cursor-pointer leading-relaxed">
                  <b className="text-white">Ceiling Rule (Always Round UP to Whole Number):</b> Required for ILOTBET and zero-decimal betting. Rounds any fractional stake up to the nearest integer so you never suffer a deficit on win (e.g. 433.33 &rarr; 434).
                </label>
              </div>

              {/* Dry Run Mode Checkbox */}
              <div className="flex items-center gap-3 p-3 bg-gray-900/60 rounded-xl border border-gray-800">
                <input
                  type="checkbox"
                  id="dry_run"
                  name="dry_run"
                  checked={formData.dry_run}
                  onChange={handleChange}
                  className="w-4 h-4 text-red-500 rounded bg-gray-800 border-gray-700 focus:ring-red-500"
                />
                <label htmlFor="dry_run" className="text-xs text-gray-300 select-none cursor-pointer">
                  <b>Simulation Mode (Dry Run):</b> Simulates placing bets and calculating stakes without touching real money.
                </label>
              </div>

              {/* Network Resilience & Auto-Recovery */}
              <div className="p-4 bg-gray-900/60 rounded-xl border border-gray-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Wifi className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-semibold text-white uppercase tracking-wider">Network Resilience & Auto-Retry</span>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      name="network_auto_retry"
                      checked={formData.network_auto_retry}
                      onChange={handleChange}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                  </label>
                </div>
                <p className="text-[11px] text-gray-400">
                  If the internet drops, the bot will avoid terminating immediately and will attempt reconnection.
                </p>

                {formData.network_auto_retry && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                    <div>
                      <label className="block text-[11px] font-semibold text-gray-400 uppercase mb-1">
                        Retry Delay (Seconds)
                      </label>
                      <input
                        type="number"
                        name="network_retry_delay"
                        min="2"
                        max="300"
                        value={formData.network_retry_delay}
                        onChange={handleChange}
                        className="w-full bg-gray-950/80 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                        required
                      />
                      <span className="text-[10px] text-gray-500">Delay between reconnect attempts</span>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-gray-400 uppercase mb-1">
                        Max Reconnect Attempts
                      </label>
                      <input
                        type="number"
                        name="network_max_retries"
                        min="1"
                        max="50"
                        value={formData.network_max_retries}
                        onChange={handleChange}
                        className="w-full bg-gray-950/80 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                        required
                      />
                      <span className="text-[10px] text-gray-500">Stops permanently if limit exceeded</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Save Button */}
              <div className="flex items-center justify-end gap-3 pt-2">
                {savedSuccess && (
                  <span className="text-xs text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    Settings saved & synced to live bot!
                  </span>
                )}
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-lg shadow-red-500/25 disabled:opacity-50"
                >
                  {saving ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  <span>Save Configuration</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Stake Escalation Simulator Card */}
          <div className="glass-card p-6 space-y-4 h-fit">
            <div className="flex items-center gap-2 border-b border-gray-800 pb-3">
              <Calculator className="w-5 h-5 text-blue-400" />
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Stake Escalation Simulator</h3>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Shows how your stake escalates on consecutive losses before resetting on a win.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-gray-800 text-gray-500">
                    <th className="py-2">Streak</th>
                    <th className="py-2">Stake</th>
                    <th className="py-2">Net Win</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-850">
                  {escalationRows.map(row => (
                    <tr key={row.step} className={row.exceedsMax ? 'text-rose-400 bg-rose-950/20' : 'text-gray-300'}>
                      <td className="py-2 font-semibold">
                        {row.step === 0 ? 'Base (0)' : `Loss ${row.step}`}
                      </td>
                      <td className="py-2">
                        ₦{row.stake.toFixed(2)}
                      </td>
                      <td className="py-2 text-emerald-400 font-semibold">
                        +{row.profitOnWin.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-blue-950/30 rounded-xl border border-blue-900/50 text-[11px] text-blue-300 leading-relaxed">
              <b>Notice:</b> At 1.50x cashout, a 3.0x multiplier guarantees that any win covers all previous losses plus a profit of at least <b>₦{(Number(formData.base_stake) * 0.5).toFixed(2)}</b>.
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
