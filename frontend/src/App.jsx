import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Plane, 
  LayoutDashboard, 
  Sliders, 
  Database, 
  BarChart3, 
  Radio, 
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Key,
  Lock,
  Eye,
  EyeOff,
  Check,
  AlertTriangle,
  BrainCircuit,
  Laptop
} from 'lucide-react';

import LiveRibbon from './components/LiveRibbon';
import DashboardTab from './components/DashboardTab';
import SettingsTab from './components/SettingsTab';
import OddsExplorerTab from './components/OddsExplorerTab';
import AnalyticsTab from './components/AnalyticsTab';
import SafeZoneTab from './components/SafeZoneTab';
import AICopilotTab from './components/AICopilotTab';
import AIAgentDeckTab from './components/AIAgentDeckTab';
import SidebarNav from './components/SidebarNav';
import PlatformGameSelector from './components/PlatformGameSelector';
import { API_BASE, WS_BASE, DEFAULT_DEV_KEY } from './config';

// Synchronously set initial X-API-Key on axios defaults before any component effects run
const initialApiKey = (typeof window !== 'undefined' && window.localStorage ? localStorage.getItem('aviator_bot_api_key') : null) || import.meta.env.VITE_BOT_API_KEY || DEFAULT_DEV_KEY;
if (initialApiKey) {
  axios.defaults.headers.common['X-API-Key'] = initialApiKey;
}

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [swarmConsensus, setSwarmConsensus] = useState(null);
  const [status, setStatus] = useState({
    is_running: false,
    is_staking: false,
    state: 'IDLE',
    status_text: 'Ready',
    balance: null,
    current_stake: 50.0,
    loss_streak: 0,
    recent_multipliers: [],
    runner_connected: false,
    runner_ip: null,
  });

  const [settings, setSettings] = useState(null);
  const [logs, setLogs] = useState([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [loadingAction, setLoadingAction] = useState(false);
  const [savingSettings, setSavingSettings] = useState(false);

  // Grade-A Security Key State
  const [apiKey, setApiKey] = useState(initialApiKey);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [tempKeyInput, setTempKeyInput] = useState('');
  const [keyVisible, setKeyVisible] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const [authError, setAuthError] = useState(false);

  const wsRef = useRef(null);

  // Attach API Key to all Axios HTTP requests via Interceptor
  useEffect(() => {
    if (apiKey) {
      axios.defaults.headers.common['X-API-Key'] = apiKey;
    }
    const interceptor = axios.interceptors.request.use(config => {
      if (apiKey) {
        config.headers['X-API-Key'] = apiKey;
      }
      return config;
    });


    const respInterceptor = axios.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401 || error.response?.status === 403) {
          setAuthError(true);
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(interceptor);
      axios.interceptors.response.eject(respInterceptor);
    };
  }, [apiKey]);

  // 1. Fetch initial status and settings
  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/bot/status/`);
      setStatus(prev => ({
        ...prev,
        ...res.data,
      }));
      setAuthError(false);
    } catch (err) {
      if (err.response?.status === 401) {
        setAuthError(true);
      }
    }
  };

  const fetchSettings = async () => {
    try {
      const res = await axios.get(`${API_BASE}/settings/`);
      setSettings(res.data);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    }
  };

  const fetchSwarmConsensus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/ai/swarm/status/`);
      if (res.data?.consensus) {
        setSwarmConsensus(res.data.consensus);
      }
    } catch (err) {
      // quiet catch
    }
  };

  const fetchInitialLogs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/logs/`);
      if (res.data?.results) {
        const initial = res.data.results.reverse().map(l => l.message);
        setLogs(initial);
      }
    } catch (err) {
      console.error('Failed to fetch logs:', err);
    }
  };

  // 2. WebSocket setup with authenticated handshake
  useEffect(() => {
    fetchStatus();
    fetchSettings();
    fetchInitialLogs();
    fetchSwarmConsensus();

    const swarmInterval = setInterval(fetchSwarmConsensus, 8000);

    let reconnectTimer = null;

    const connectWebSocket = () => {
      try {
        const wsUrl = `${WS_BASE}?token=${encodeURIComponent(apiKey || '')}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
          setAuthError(false);
        };

        ws.onclose = (evt) => {
          setWsConnected(false);
          if (evt.code === 4003) {
            setAuthError(true);
            setLogs(prev => [...prev.slice(-300), '[Security] WebSocket connection rejected: Invalid or missing API Key.']);
            return; // Do not rapidly reconnect if unauthorized
          }
          // Reconnect after 3 seconds
          reconnectTimer = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
        };

        ws.onmessage = (evt) => {
          try {
            const payload = JSON.parse(evt.data);
            const { type, data } = payload;

            if (type === 'odds_extracted') {
              if (data?.recent_ribbon) {
                setStatus(prev => ({
                  ...prev,
                  recent_multipliers: data.recent_ribbon,
                }));
              }
              setLogs(prev => [...prev.slice(-300), `[Live Extractor] Extracted crash multiplier: ${data.multiplier.toFixed(2)}x`]);
            } else if (type === 'round_result') {
              setStatus(prev => ({
                ...prev,
                balance: data.balance ?? prev.balance,
                current_stake: data.current_stake ?? prev.current_stake,
                loss_streak: data.loss_streak ?? prev.loss_streak,
              }));
              if (data?.message) {
                setLogs(prev => [...prev.slice(-300), data.message]);
              }
            } else if (type === 'balance_updated') {
              setStatus(prev => ({
                ...prev,
                balance: data.balance,
              }));
            } else if (type === 'status_changed') {
              setStatus(prev => ({
                ...prev,
                status_text: data.status,
              }));
            } else if (type === 'schedule_updated') {
              setStatus(prev => ({
                ...prev,
                schedule: {
                  active: data.active,
                  start_time: data.start_time,
                  duration_minutes: data.duration_minutes,
                  auto_stake: data.auto_stake,
                }
              }));
            } else if (type === 'runner_status') {
              setStatus(prev => ({
                ...prev,
                runner_connected: Boolean(data?.connected),
                runner_ip: data?.client_ip || prev.runner_ip,
              }));
              if (data?.connected) {
                setLogs(prev => [...prev.slice(-300), `[System] Desktop Runner connected (${data.client_ip || 'Residential IP Active'})`]);
              } else {
                setLogs(prev => [...prev.slice(-300), '[System] Desktop Runner disconnected']);
              }
            } else if (type === 'log' || type === 'bot_message') {
              if (data?.message) {
                setLogs(prev => [...prev.slice(-300), data.message]);
              }
            }
          } catch (e) {
            console.error('Error parsing WS message:', e);
          }
        };
      } catch (err) {
        console.error('WebSocket connection error:', err);
      }
    };

    connectWebSocket();

    // Fallback polling every 4 seconds
    const interval = setInterval(fetchStatus, 4000);

    return () => {
      clearInterval(interval);
      clearInterval(swarmInterval);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (wsRef.current) wsRef.current.close();
    };
  }, [apiKey]);

  // 3. Bot Control Handlers
  const handleControlAction = async (actionName) => {
    setLoadingAction(true);
    try {
      const res = await axios.post(`${API_BASE}/bot/control/`, { action: actionName });
      if (res.data?.message) {
        setLogs(prev => [...prev.slice(-300), `[Command] ${res.data.message}`]);
      }
      await fetchStatus();
    } catch (err) {
      const errMsg = err.response?.data?.message || err.message;
      setLogs(prev => [...prev.slice(-300), `[Error] ${errMsg}`]);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleSchedule = async (scheduleData) => {
    setLoadingAction(true);
    try {
      const res = await axios.post(`${API_BASE}/bot/control/`, {
        action: 'schedule',
        start_in_seconds: scheduleData.start_in_seconds,
        duration_minutes: scheduleData.duration_minutes,
        target_iso_time: scheduleData.target_iso_time,
        auto_stake: scheduleData.auto_stake !== false,
      });
      if (res.data?.message) {
        setLogs(prev => [...prev.slice(-300), `[Schedule] ${res.data.message}`]);
      }
      await fetchStatus();
    } catch (err) {
      const errMsg = err.response?.data?.message || err.message;
      setLogs(prev => [...prev.slice(-300), `[Error] ${errMsg}`]);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleCancelSchedule = async () => {
    setLoadingAction(true);
    try {
      const res = await axios.post(`${API_BASE}/bot/control/`, {
        action: 'cancel_schedule',
      });
      if (res.data?.message) {
        setLogs(prev => [...prev.slice(-300), `[Schedule] ${res.data.message}`]);
      }
      await fetchStatus();
    } catch (err) {
      const errMsg = err.response?.data?.message || err.message;
      setLogs(prev => [...prev.slice(-300), `[Error] ${errMsg}`]);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleSaveSettings = async (newSettings) => {
    setSavingSettings(true);
    try {
      const res = await axios.put(`${API_BASE}/settings/`, newSettings);
      setSettings(res.data);
      setLogs(prev => [...prev.slice(-300), `[Settings] Bot configuration updated successfully.`]);
      await fetchStatus();
    } catch (err) {
      setLogs(prev => [...prev.slice(-300), `[Error] Failed to save settings: ${err.message}`]);
    } finally {
      setSavingSettings(false);
    }
  };

  const currentPlatform = settings?.platform || settings?.site || 'ilotbet';
  const currentGame = settings?.game || 'best_aviator';

  const handlePlatformGameChange = async (newPlatform, newGame) => {
    if (!settings) return;
    const updated = {
      ...settings,
      platform: newPlatform,
      site: newPlatform,
      game: newGame,
    };
    await handleSaveSettings(updated);
  };

  const handleUpdateApiKey = (e) => {
    e.preventDefault();
    if (tempKeyInput.trim()) {
      const newKey = tempKeyInput.trim();
      setApiKey(newKey);
      localStorage.setItem('aviator_bot_api_key', newKey);
      setShowKeyModal(false);
      setAuthError(false);
      setLogs(prev => [...prev.slice(-300), '[Security] API Key updated in browser session.']);
    }
  };

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  return (
    <div className="app-layout">
      {/* Collapsible Left Sidebar */}
      <SidebarNav
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        botStatus={status}
        config={settings}
        swarmConsensus={swarmConsensus}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      {/* Main Workspace Column */}
      <div className="app-workspace">
        {/* Streamlined Top Navigation Header */}
        <header className="app-top-header">
          <div className="flex items-center gap-4">
            <h2 className="text-sm font-extrabold text-white tracking-wide uppercase">
              {activeTab === 'dashboard' && 'Control Center & Live Staking'}
              {activeTab === 'swarm' && 'Multi-Agent Swarm Command Deck'}
              {(activeTab === 'copilot' || activeTab === 'ai_copilot') && 'AI Staking Copilot & Cross-Session Memory'}
              {activeTab === 'safezone' && 'SafeZone Analytics & Risk Radar'}
              {(activeTab === 'odds' || activeTab === 'odds_explorer') && 'Database Crash Multipliers'}
              {activeTab === 'analytics' && 'Staking Ledger & Session Performance'}
              {activeTab === 'settings' && 'Bot Parameters & Platform Config'}
            </h2>

            {/* Platform & Game Switcher */}
            <div className="hidden sm:block">
              <PlatformGameSelector
                currentPlatform={currentPlatform}
                currentGame={currentGame}
                onChange={handlePlatformGameChange}
              />
            </div>
          </div>

          {/* Right Header Status Controls */}
          <div className="flex items-center gap-3 text-xs font-mono">
            {/* Desktop Runner Status Pill */}
            <div
              title={status.runner_connected ? `Desktop Runner Connected (${status.runner_ip || 'Residential IP Active'})` : "Desktop Runner Offline - Start Desktop Agent on your PC"}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border transition-all ${
                status.runner_connected
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                  : 'bg-gray-900 border-gray-800 text-gray-400'
              }`}
            >
              <Laptop className="w-3.5 h-3.5" />
              <span className="text-[11px] font-semibold hidden md:inline">
                {status.runner_connected ? 'RUNNER ACTIVE' : 'RUNNER OFFLINE'}
              </span>
            </div>
            {/* Grade-A Security Key Button */}
            <button
              onClick={() => {
                setTempKeyInput(apiKey);
                setShowKeyModal(true);
              }}
              title="API Authentication Key Settings"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border transition-all ${
                authError 
                  ? 'bg-rose-500/20 border-rose-500/40 text-rose-400 animate-pulse' 
                  : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span className="text-[11px] font-semibold hidden md:inline">
                {authError ? 'AUTH FAILED' : 'API SECURED'}
              </span>
            </button>

            {/* Stream Connection Pill */}
            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-900 rounded-full border border-gray-800">
              <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-400 live-pulse' : 'bg-rose-500'}`}></span>
              <span className="text-gray-400 text-[11px] hidden sm:inline">{wsConnected ? 'STREAM ACTIVE' : 'CONNECTING'}</span>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="app-main-content">
          {/* Auth Error Banner if present */}
          {authError && (
            <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-bold text-rose-300">API Key Authentication Required</h4>
                  <p className="text-xs text-rose-400/80">Backend rejected unauthenticated request. Please configure your BOT_API_KEY.</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setTempKeyInput(apiKey);
                  setShowKeyModal(true);
                }}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold"
              >
                Configure Key
              </button>
            </div>
          )}

          {/* Live Ribbon on every tab */}
          <LiveRibbon 
            multipliers={status.recent_multipliers} 
            isConnected={wsConnected} 
          />

          {/* Tab Views */}
          {activeTab === 'dashboard' && (
            <DashboardTab
              status={status}
              logs={logs}
              onPrepare={() => handleControlAction('prepare')}
              onStart={() => handleControlAction('start')}
              onPause={() => handleControlAction('pause')}
              onStop={() => handleControlAction('stop')}
              onSchedule={handleSchedule}
              onCancelSchedule={handleCancelSchedule}
              onClearLogs={() => setLogs([])}
              loadingAction={loadingAction}
            />
          )}

          {activeTab === 'swarm' && (
            <AIAgentDeckTab
              config={settings}
              onUpdateConfig={handleSaveSettings}
            />
          )}

          {(activeTab === 'copilot' || activeTab === 'ai_copilot') && (
            <AICopilotTab
              currentPlatform={currentPlatform}
              currentGame={currentGame}
              onApplySettings={handleSaveSettings}
            />
          )}

          {activeTab === 'safezone' && (
            <SafeZoneTab />
          )}

          {activeTab === 'settings' && (
            <SettingsTab
              settings={settings}
              onSave={handleSaveSettings}
              saving={savingSettings}
            />
          )}

          {(activeTab === 'odds' || activeTab === 'odds_explorer') && (
            <OddsExplorerTab />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsTab />
          )}
        </main>

        {/* Footer */}
        <footer className="app-footer">
          Aviator Bot Full-Stack &copy; 2026 &bull; Django REST Framework &bull; PostgreSQL Database &bull; Grade-A Zero-Leak Security Active
        </footer>
      </div>

      {/* Grade-A Security Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="glass-card max-w-md w-full p-6 border-emerald-500/30 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                  <Lock className="w-5 h-5" />
                </div>
                <h3 className="text-base font-bold text-white">API Authentication Key</h3>
              </div>
              <button 
                onClick={() => setShowKeyModal(false)}
                className="text-gray-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-gray-400">
              Grade-A defense is active. All control commands and live WebSocket streams require this high-entropy token to prevent unauthorized access.
            </p>

            <form onSubmit={handleUpdateApiKey} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-gray-300">Active BOT_API_KEY</label>
                <div className="relative">
                  <input
                    type={keyVisible ? 'text' : 'password'}
                    value={tempKeyInput}
                    onChange={(e) => setTempKeyInput(e.target.value)}
                    placeholder="Enter 64-char API Key..."
                    className="w-full bg-gray-900 border border-gray-700 rounded-xl px-3 py-2 text-xs font-mono text-white pr-20 focus:outline-none focus:border-emerald-500"
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setKeyVisible(!keyVisible)}
                      className="p-1 text-gray-400 hover:text-white"
                      title={keyVisible ? "Hide Key" : "Show Key"}
                    >
                      {keyVisible ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      type="button"
                      onClick={handleCopyKey}
                      className="p-1 text-gray-400 hover:text-white"
                      title="Copy Key"
                    >
                      {copiedKey ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Key className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowKeyModal(false)}
                  className="px-3 py-2 rounded-xl text-xs font-semibold text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-500/20"
                >
                  Save & Authenticate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
