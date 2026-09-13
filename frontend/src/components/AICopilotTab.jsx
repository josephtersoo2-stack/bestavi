import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Sparkles, 
  ShieldAlert, 
  BrainCircuit, 
  Zap, 
  CheckCircle2, 
  RefreshCw, 
  Sliders, 
  MessageSquare, 
  Send, 
  Cpu, 
  TrendingUp, 
  Flame, 
  Snowflake,
  Activity,
  Bot,
  Plus,
  Trash2,
  Pin,
  History,
  Lock,
  ChevronLeft,
  ChevronRight,
  Pencil,
  Check,
  X
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { API_BASE } from '../config';

export default function AICopilotTab({ currentPlatform, currentGame, onApplySettings }) {
  const [provider, setProvider] = useState('gemini');
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [loadingModels, setLoadingModels] = useState(false);
  const [statusInfo, setStatusInfo] = useState(null);

  // Analysis & Recommendation state
  const [analyzingRisk, setAnalyzingRisk] = useState(false);
  const [riskData, setRiskData] = useState(null);
  const [generatingStrategy, setGeneratingStrategy] = useState(false);
  const [strategyData, setStrategyData] = useState(null);
  const [appliedSuccess, setAppliedSuccess] = useState(false);

  // Multi-Thread Persistent Chat State
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [showSessionDrawer, setShowSessionDrawer] = useState(true);
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editTitleValue, setEditTitleValue] = useState('');
  
  const [chatMessages, setChatMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [sendingChat, setSendingChat] = useState(false);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    fetchAIStatus();
    fetchSessions();
  }, []);

  useEffect(() => {
    fetchModels(provider);
  }, [provider]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const fetchAIStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/ai/status/`);
      setStatusInfo(res.data);
      if (res.data.ai_provider) {
        setProvider(res.data.ai_provider);
      }
      if (res.data.ai_model) {
        setSelectedModel(res.data.ai_model);
      }
    } catch (err) {
      console.error('Failed to fetch AI status:', err);
    }
  };

  const fetchModels = async (selectedProv) => {
    setLoadingModels(true);
    try {
      const res = await axios.get(`${API_BASE}/ai/models/?provider=${selectedProv}`);
      const list = res.data.models || [];
      setModels(list);
      if (list.length > 0) {
        if (!selectedModel || !list.some(m => m.id === selectedModel)) {
          setSelectedModel(list[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch AI models:', err);
    } finally {
      setLoadingModels(false);
    }
  };

  const fetchSessions = async () => {
    setLoadingSessions(true);
    try {
      const res = await axios.get(`${API_BASE}/ai/chats/`);
      const list = res.data.sessions || [];
      setSessions(list);
      if (list.length > 0) {
        // Load the first (most recent) session by default if none selected
        if (!activeSessionId) {
          loadSessionDetails(list[0].id);
        }
      } else {
        // Create initial default session
        handleCreateNewSession();
      }
    } catch (err) {
      console.error('Failed to fetch chat sessions:', err);
    } finally {
      setLoadingSessions(false);
    }
  };

  const loadSessionDetails = async (sessionId) => {
    try {
      setActiveSessionId(sessionId);
      const res = await axios.get(`${API_BASE}/ai/chats/${sessionId}/`);
      const msgs = (res.data.messages || []).map(m => ({
        id: m.id,
        role: m.role,
        senderName: m.sender_name,
        text: m.content,
        metadata: m.metadata,
        createdAt: m.created_at,
      }));
      setChatMessages(msgs);
    } catch (err) {
      console.error('Failed to load session messages:', err);
    }
  };

  const handleCreateNewSession = async () => {
    try {
      const res = await axios.post(`${API_BASE}/ai/chats/`, {
        title: 'New Conversation',
        platform: currentPlatform || 'ilotbet',
        game: currentGame || 'best_aviator',
      });
      const newSess = res.data;
      setSessions(prev => [newSess, ...prev]);
      setActiveSessionId(newSess.id);
      setChatMessages([
        {
          id: 'welcome',
          role: 'assistant',
          senderName: 'Swarm Supervisor',
          text: 'Enterprise Multi-Agent Swarm activated. I retain complete memory across all your past chat sessions and live odds telemetry. How can we optimize your staking today?'
        }
      ]);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  };

  const handleDeleteSession = async (e, sessionId) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation thread?')) return;
    try {
      await axios.delete(`${API_BASE}/ai/chats/${sessionId}/`);
      const remaining = sessions.filter(s => s.id !== sessionId);
      setSessions(remaining);
      if (activeSessionId === sessionId) {
        if (remaining.length > 0) {
          loadSessionDetails(remaining[0].id);
        } else {
          handleCreateNewSession();
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const handleStartRename = (e, session) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditTitleValue(session.title);
  };

  const handleSaveRename = async (e, sessionId) => {
    e.stopPropagation();
    if (!editTitleValue.trim()) {
      setEditingSessionId(null);
      return;
    }
    try {
      await axios.patch(`${API_BASE}/ai/chats/${sessionId}/`, { title: editTitleValue.trim() });
      setSessions(prev => prev.map(s => s.id === sessionId ? { ...s, title: editTitleValue.trim() } : s));
    } catch (err) {
      console.error('Failed to rename session:', err);
    } finally {
      setEditingSessionId(null);
    }
  };

  const handleCancelRename = (e) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  const handleRunRiskAnalysis = async () => {
    setAnalyzingRisk(true);
    setRiskData(null);
    try {
      const res = await axios.post(`${API_BASE}/ai/analyze/`, {
        provider,
        model: selectedModel,
        platform: currentPlatform,
        game: currentGame,
      });
      setRiskData(res.data.analysis);
    } catch (err) {
      alert('Risk analysis failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setAnalyzingRisk(false);
    }
  };

  const handleGenerateStrategy = async () => {
    setGeneratingStrategy(true);
    setStrategyData(null);
    try {
      const res = await axios.post(`${API_BASE}/ai/recommend/`, {
        provider,
        model: selectedModel,
        platform: currentPlatform,
        game: currentGame,
      });
      setStrategyData(res.data.recommendation);
    } catch (err) {
      alert('Strategy generation failed: ' + (err.response?.data?.error || err.message));
    } finally {
      setGeneratingStrategy(false);
    }
  };

  const handleApplyStrategy = async () => {
    if (!strategyData || !onApplySettings) return;
    const payload = {
      strategy: strategyData.recommended_strategy?.toLowerCase() || 'martingale',
      base_stake: strategyData.recommended_base_stake,
      auto_cashout: strategyData.recommended_auto_cashout,
      multiplier: strategyData.recommended_multiplier,
      max_loss_steps: strategyData.recommended_max_loss_steps,
      stop_loss: strategyData.recommended_stop_loss,
      profit_target: strategyData.recommended_profit_target,
    };
    await onApplySettings(payload);
    setAppliedSuccess(true);
    setTimeout(() => setAppliedSuccess(false), 3500);
  };

  const handleSendMessage = async (e) => {
    e?.preventDefault();
    const query = userInput.trim();
    if (!query || sendingChat) return;

    setUserInput('');
    let sessId = activeSessionId;
    if (!sessId) {
      const newSessRes = await axios.post(`${API_BASE}/ai/chats/`, {
        title: query.slice(0, 30),
        platform: currentPlatform,
        game: currentGame,
      });
      sessId = newSessRes.data.id;
      setActiveSessionId(sessId);
      setSessions(prev => [newSessRes.data, ...prev]);
    }

    // Optimistic UI push
    setChatMessages(prev => [
      ...prev,
      { role: 'user', senderName: 'User', text: query }
    ]);
    setSendingChat(true);

    try {
      const res = await axios.post(`${API_BASE}/ai/chats/${sessId}/message/`, {
        content: query,
      });

      const assistantMsg = res.data.assistant_message;
      setChatMessages(prev => [
        ...prev,
        {
          id: assistantMsg.id,
          role: assistantMsg.role,
          senderName: assistantMsg.sender_name,
          text: assistantMsg.content,
          metadata: assistantMsg.metadata,
          createdAt: assistantMsg.created_at,
        }
      ]);

      // Refresh session list to update titles/timestamps
      const sessListRes = await axios.get(`${API_BASE}/ai/chats/`);
      setSessions(sessListRes.data.sessions || []);
    } catch (err) {
      setChatMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          senderName: 'System', 
          text: 'Error connecting to AI Swarm: ' + (err.response?.data?.error || err.message) 
        }
      ]);
    } finally {
      setSendingChat(false);
    }
  };

  const getRiskBadgeColor = (level) => {
    switch (level) {
      case 'CRITICAL': return 'text-rose-400 bg-rose-950/40 border-rose-800/60';
      case 'HIGH': return 'text-orange-400 bg-orange-950/40 border-orange-800/60';
      case 'MODERATE': return 'text-amber-400 bg-amber-950/40 border-amber-800/60';
      default: return 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60';
    }
  };

  const getRegimeIcon = (regime) => {
    if (regime === 'COLD_CLUSTER') return <Snowflake className="w-4 h-4 text-blue-400" />;
    if (regime === 'HOT_STREAK') return <Flame className="w-4 h-4 text-orange-400" />;
    if (regime === 'VOLATILE') return <Activity className="w-4 h-4 text-purple-400" />;
    return <TrendingUp className="w-4 h-4 text-emerald-400" />;
  };

  const activeSessionObj = sessions.find(s => s.id === activeSessionId);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Top AI Model & Provider Header Deck */}
      <div className="glass-card p-5 rounded-2xl border border-gray-800 bg-gradient-to-r from-gray-900/90 via-gray-900/50 to-purple-950/20">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <BrainCircuit className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-wide">AI Staking Copilot & Multi-Thread Memory</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  CROSS-SESSION MEMORY
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Grounds predictive loss-clustering models directly against live telemetry and recalls past chat discussions.
              </p>
            </div>
          </div>

          {/* Provider & Model Selectors */}
          <div className="flex flex-wrap items-center gap-2.5 w-full lg:w-auto">
            {/* Provider Switcher */}
            <div className="flex items-center bg-gray-950/80 p-1 rounded-xl border border-gray-800">
              <button
                type="button"
                onClick={() => setProvider('gemini')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  provider === 'gemini'
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Google Gemini
              </button>
              <button
                type="button"
                onClick={() => setProvider('openrouter')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  provider === 'openrouter'
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                OpenRouter.ai
              </button>
            </div>

            {/* Dynamic Model Dropdown */}
            <div className="flex items-center gap-1.5 bg-gray-950/80 px-3 py-1.5 rounded-xl border border-gray-800">
              <Cpu className="w-3.5 h-3.5 text-gray-400" />
              {loadingModels ? (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <RefreshCw className="w-3 h-3 animate-spin" /> Fetching models...
                </span>
              ) : (
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="bg-transparent text-xs text-white font-mono focus:outline-none cursor-pointer max-w-[200px]"
                >
                  {models.map(m => (
                    <option key={m.id} value={m.id} className="bg-gray-900 text-white">
                      {m.name || m.id}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Run Analysis Buttons */}
            <button
              onClick={handleRunRiskAnalysis}
              disabled={analyzingRisk}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all disabled:opacity-50"
            >
              {analyzingRisk ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
              <span>Analyze Risk</span>
            </button>

            <button
              onClick={handleGenerateStrategy}
              disabled={generatingStrategy}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {generatingStrategy ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span>Optimize Strategy</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Left Side (Risk & Strategy) | Right Side (Copilot Chat with Thread Sessions) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Intelligence Cards (6 cols) */}
        <div className="lg:col-span-6 space-y-6">
          {/* AI Risk Radar Card */}
          <div className="glass-card p-5 border border-gray-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Predictive Risk Radar</h3>
              </div>
              {riskData && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getRiskBadgeColor(riskData.risk_level)}`}>
                  {riskData.risk_level} ({riskData.risk_score}/100)
                </span>
              )}
            </div>

            {riskData ? (
              <div className="space-y-4 text-xs">
                <div className="p-3.5 rounded-xl bg-gray-950/60 border border-gray-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Market Regime:</span>
                    <span className="font-bold text-white flex items-center gap-1.5 font-mono">
                      {getRegimeIcon(riskData.market_regime)}
                      {riskData.market_regime?.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Observed SafeZone Win Rate:</span>
                    <span className="font-mono font-bold text-emerald-400">
                      {riskData.odds_summary?.safezone_win_rate}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Streak Breach Hazard (5+):</span>
                    <span className="font-mono font-bold text-red-400">
                      {riskData.consecutive_loss_hazard_prob}%
                    </span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <span className="text-gray-400 font-medium">Quantitative Reasoning:</span>
                  <p className="text-gray-300 leading-relaxed bg-gray-900/40 p-3 rounded-xl border border-gray-850">
                    {riskData.reasoning}
                  </p>
                </div>

                {riskData.actionable_recommendation && (
                  <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-800/40 text-purple-200">
                    <span className="font-bold text-white block mb-1">Recommended Action:</span>
                    {riskData.actionable_recommendation}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-gray-500 space-y-2">
                <p>Click "Analyze Risk" to trigger quantitative clustering models.</p>
                <button
                  onClick={handleRunRiskAnalysis}
                  disabled={analyzingRisk}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold transition-all"
                >
                  Run Risk Evaluation
                </button>
              </div>
            )}
          </div>

          {/* Strategy Advisor Card */}
          <div className="glass-card p-5 border border-gray-800 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Dynamic Strategy Optimizer</h3>
              </div>
              {strategyData && (
                <span className="text-xs font-mono font-bold text-indigo-300">
                  {strategyData.recommended_strategy?.toUpperCase()}
                </span>
              )}
            </div>

            {strategyData ? (
              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2.5 rounded-xl bg-gray-950/60 border border-gray-800 text-center">
                    <div className="text-gray-400 text-[10px]">Auto Cashout</div>
                    <div className="font-mono font-bold text-base text-emerald-400">
                      {strategyData.recommended_auto_cashout}x
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-gray-950/60 border border-gray-800 text-center">
                    <div className="text-gray-400 text-[10px]">Loss Multiplier</div>
                    <div className="font-mono font-bold text-base text-amber-400">
                      {strategyData.recommended_multiplier}x
                    </div>
                  </div>
                  <div className="p-2.5 rounded-xl bg-gray-950/60 border border-gray-800 text-center">
                    <div className="text-gray-400 text-[10px]">Max Loss Steps</div>
                    <div className="font-mono font-bold text-base text-red-400">
                      {strategyData.recommended_max_loss_steps}
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-gray-900/40 rounded-xl border border-gray-850 text-gray-300 leading-relaxed">
                  <span className="font-bold text-white block mb-1">Mathematical Rationale:</span>
                  {strategyData.rationale}
                </div>

                <div className="flex items-center justify-between pt-2">
                  <span className="text-[11px] text-gray-400">
                    Confidence: <strong className="text-white">{strategyData.confidence_score}%</strong>
                  </span>
                  <button
                    onClick={handleApplyStrategy}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                      appliedSuccess
                        ? 'bg-emerald-600 text-white'
                        : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/20'
                    }`}
                  >
                    {appliedSuccess ? <CheckCircle2 className="w-4 h-4" /> : <Sliders className="w-4 h-4" />}
                    <span>{appliedSuccess ? 'Settings Applied!' : 'Apply Strategy (1-Click)'}</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-xs text-gray-500 space-y-2">
                <p>Click "Optimize Strategy" to calculate mathematically sound odds.</p>
                <button
                  onClick={handleGenerateStrategy}
                  disabled={generatingStrategy}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition-all"
                >
                  Generate Strategy Recommendation
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Multi-Thread Chat with Persistent Drawer (6 cols) */}
        <div className="lg:col-span-6 glass-card p-0 flex flex-col h-[640px] border border-gray-800 rounded-2xl overflow-hidden shadow-2xl">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-950/80">
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => setShowSessionDrawer(!showSessionDrawer)}
                className="p-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-gray-400 hover:text-white border border-gray-800 transition-colors"
                title={showSessionDrawer ? "Hide Saved Sessions" : "Show Saved Sessions"}
              >
                <History className="w-4 h-4" />
              </button>
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Bot className="w-4 h-4 text-purple-400" />
                  {activeSessionObj?.title || 'Interactive Copilot'}
                </h3>
                <div className="text-[10px] text-purple-400 flex items-center gap-1 font-mono">
                  <span>🧠 Full Cross-Session Memory Active</span>
                </div>
              </div>
            </div>

            {/* New Chat Button */}
            <button
              onClick={handleCreateNewSession}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Chat</span>
            </button>
          </div>

          {/* Main Body: Drawer + Messages Area */}
          <div className="flex-1 flex overflow-hidden">
            {/* Saved Sessions Drawer */}
            {showSessionDrawer && (
              <div className="w-56 border-r border-gray-800 bg-gray-950/90 flex flex-col shrink-0 animate-in slide-in-from-left duration-150">
                <div className="p-2.5 border-b border-gray-850 text-[10px] font-mono text-gray-400 uppercase tracking-wider flex justify-between items-center">
                  <span>Saved Threads ({sessions.length})</span>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1 text-xs">
                  {sessions.map(s => {
                    const isActive = s.id === activeSessionId;
                    return (
                      <div
                        key={s.id}
                        onClick={() => { if (editingSessionId !== s.id) loadSessionDetails(s.id); }}
                        className={`p-2 rounded-xl cursor-pointer transition-all flex items-center justify-between group ${
                          isActive
                            ? 'bg-purple-600/20 text-purple-200 border border-purple-500/40'
                            : 'text-gray-400 hover:bg-gray-900 hover:text-gray-200 border border-transparent'
                        }`}
                      >
                        {editingSessionId === s.id ? (
                          <div className="flex-1 flex items-center gap-1 min-w-0 pr-1">
                            <input
                              type="text"
                              autoFocus
                              value={editTitleValue}
                              onChange={(e) => setEditTitleValue(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleSaveRename(e, s.id);
                                if (e.key === 'Escape') handleCancelRename(e);
                              }}
                              className="flex-1 min-w-0 bg-gray-900 border border-purple-500 text-white rounded px-1.5 py-0.5 text-xs outline-none focus:ring-1 focus:ring-purple-500"
                              onClick={(e) => e.stopPropagation()}
                            />
                            <button onClick={(e) => handleSaveRename(e, s.id)} className="text-emerald-400 hover:text-emerald-300 p-0.5 shrink-0"><Check className="w-3 h-3" /></button>
                            <button onClick={handleCancelRename} className="text-gray-400 hover:text-gray-300 p-0.5 shrink-0"><X className="w-3 h-3" /></button>
                          </div>
                        ) : (
                          <>
                            <div className="min-w-0 pr-1">
                              <div className="font-semibold text-xs truncate">
                                {s.title}
                              </div>
                              <div className="text-[10px] text-gray-500 font-mono">
                                {s.message_count || 0} msgs • {s.updated_at?.slice(5, 10)}
                              </div>
                            </div>
                            <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity gap-0.5 shrink-0">
                              <button
                                onClick={(e) => handleStartRename(e, s)}
                                className="p-1 hover:text-purple-400 transition-colors"
                                title="Rename thread"
                              >
                                <Pencil className="w-3 h-3" />
                              </button>
                              <button
                                onClick={(e) => handleDeleteSession(e, s.id)}
                                className="p-1 hover:text-red-400 transition-colors"
                                title="Delete thread"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Conversation Messages */}
            <div className="flex-1 flex flex-col justify-between bg-gray-900/30 overflow-hidden">
              <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
                {chatMessages.map((msg, i) => (
                  <div
                    key={msg.id || i}
                    className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.role !== 'user' && (
                      <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-purple-600 to-indigo-600 flex items-center justify-center flex-shrink-0 text-white text-[11px] font-bold shadow-md">
                        AI
                      </div>
                    )}
                    <div
                      className={`p-3.5 rounded-2xl max-w-[85%] leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-red-600 text-white rounded-tr-none'
                          : 'bg-gray-900/90 border border-gray-800 text-gray-200 rounded-tl-none font-sans shadow-lg'
                      }`}
                    >
                      <div className="flex items-center justify-between pb-1 mb-1 border-b border-white/10 text-[10px] font-mono opacity-80">
                        <span>{msg.senderName || (msg.role === 'user' ? 'You' : 'Swarm Supervisor')}</span>
                        {msg.metadata?.consensus_directive && (
                          <span className="px-1.5 py-0.2 rounded bg-black/40 text-purple-300 font-bold">
                            {msg.metadata.consensus_directive} ({msg.metadata.consensus_score}%)
                          </span>
                        )}
                      </div>
                      <div className="react-markdown-prose whitespace-normal break-words leading-relaxed text-xs">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.text}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                ))}

                {sendingChat && (
                  <div className="flex gap-2.5 justify-start">
                    <div className="w-7 h-7 rounded-xl bg-purple-600 flex items-center justify-center flex-shrink-0 text-white text-[11px] font-bold">
                      AI
                    </div>
                    <div className="p-3.5 bg-gray-900/90 border border-gray-800 rounded-2xl rounded-tl-none text-xs text-gray-400 flex items-center gap-2">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-purple-400" />
                      <span>Swarm agents cross-referencing past memory & live telemetry...</span>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              {/* Bottom Quick Chips */}
              <div className="p-2 px-4 flex flex-wrap gap-1.5 border-t border-gray-850 bg-gray-950/60">
                <button
                  onClick={() => setUserInput('What is our current risk profile across the last 100 rounds?')}
                  className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-gray-400 hover:text-white rounded-lg text-[10px] transition-colors border border-gray-800"
                >
                  Risk Profile
                </button>
                <button
                  onClick={() => setUserInput('Does 1.35x cashout yield a higher EV than 1.50x right now?')}
                  className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-gray-400 hover:text-white rounded-lg text-[10px] transition-colors border border-gray-800"
                >
                  1.35x vs 1.50x EV
                </button>
                <button
                  onClick={() => setUserInput('Review our past conversations: what advice did we agree on?')}
                  className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-purple-300 hover:text-white rounded-lg text-[10px] transition-colors border border-purple-900/40"
                >
                  Recall Past Threads
                </button>
              </div>

              {/* Chat Input Box */}
              <form onSubmit={handleSendMessage} className="p-3 border-t border-gray-800 bg-gray-950 flex items-center gap-2">
                <input
                  type="text"
                  value={userInput}
                  onChange={(e) => setUserInput(e.target.value)}
                  placeholder="Ask the Swarm about odds streaks, risk, or past strategies..."
                  className="flex-1 bg-gray-900 border border-gray-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                />
                <button
                  type="submit"
                  disabled={!userInput.trim() || sendingChat}
                  className="p-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl transition-all disabled:opacity-40"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
