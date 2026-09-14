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
  Pencil,
  Check,
  X,
  BookmarkPlus,
  Bookmark,
  Search,
  Filter,
  Clock,
  ToggleLeft,
  ToggleRight,
  Database,
  BookOpen,
  Copy
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
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
  const [copiedMsgId, setCopiedMsgId] = useState(null);
  const chatBottomRef = useRef(null);

  const handleCopyMessage = (text, id) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedMsgId(id);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const markdownComponents = {
    table: ({ node, ...props }) => (
      <div className="overflow-x-auto my-2 rounded-lg border border-white/10 bg-black/30">
        <table className="w-full text-left border-collapse" {...props} />
      </div>
    ),
    th: ({ node, ...props }) => (
      <th className="bg-gray-800/80 px-3 py-1.5 text-[11px] font-semibold text-gray-200 border-b border-white/10 whitespace-nowrap" {...props} />
    ),
    td: ({ node, ...props }) => (
      <td className="px-3 py-1.5 text-[11px] border-b border-white/5 whitespace-nowrap text-gray-300" {...props} />
    ),
  };

  // Discovery Memory Vault State
  const [copilotMode, setCopilotMode] = useState('chat'); // 'chat' | 'vault'
  const [memories, setMemories] = useState([]);
  const [loadingMemories, setLoadingMemories] = useState(false);
  const [memorySearch, setMemorySearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [showMemoryModal, setShowMemoryModal] = useState(false);
  const [editingMemory, setEditingMemory] = useState(null);
  const [memoryForm, setMemoryForm] = useState({
    title: '',
    category: 'STREAK_TIMING',
    content: '',
    is_active: true,
  });
  const [lastSavedNotification, setLastSavedNotification] = useState(null);

  useEffect(() => {
    fetchAIStatus();
    fetchSessions();
    fetchMemories();
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

  const fetchMemories = async () => {
    setLoadingMemories(true);
    try {
      const res = await axios.get(`${API_BASE}/ai/memories/`);
      setMemories(res.data.memories || []);
    } catch (err) {
      console.error('Failed to fetch discovery memories:', err);
    } finally {
      setLoadingMemories(false);
    }
  };

  const handleToggleMemory = async (memoryId, currentActive) => {
    try {
      await axios.patch(`${API_BASE}/ai/memories/${memoryId}/`, {
        is_active: !currentActive,
      });
      setMemories(prev =>
        prev.map(m => (m.id === memoryId ? { ...m, is_active: !currentActive } : m))
      );
    } catch (err) {
      console.error('Failed to toggle memory active status:', err);
    }
  };

  const handleDeleteMemory = async (memoryId) => {
    if (!window.confirm('Delete this discovery memory from the permanent vault?')) return;
    try {
      await axios.delete(`${API_BASE}/ai/memories/${memoryId}/`);
      setMemories(prev => prev.filter(m => m.id !== memoryId));
    } catch (err) {
      console.error('Failed to delete discovery memory:', err);
    }
  };

  const handleOpenAddMemory = (prefillTitle = '', prefillContent = '', prefillCategory = 'GENERAL') => {
    setEditingMemory(null);
    setMemoryForm({
      title: prefillTitle,
      category: prefillCategory,
      content: prefillContent,
      is_active: true,
    });
    setShowMemoryModal(true);
  };

  const handleOpenEditMemory = (mem) => {
    setEditingMemory(mem);
    setMemoryForm({
      title: mem.title,
      category: mem.category,
      content: mem.content,
      is_active: mem.is_active,
    });
    setShowMemoryModal(true);
  };

  const handleSaveMemoryModal = async (e) => {
    e.preventDefault();
    if (!memoryForm.title.trim() || !memoryForm.content.trim()) return;

    try {
      if (editingMemory) {
        const res = await axios.patch(`${API_BASE}/ai/memories/${editingMemory.id}/`, memoryForm);
        setMemories(prev => prev.map(m => (m.id === editingMemory.id ? res.data : m)));
      } else {
        const res = await axios.post(`${API_BASE}/ai/memories/`, {
          ...memoryForm,
          platform: currentPlatform || 'ilotbet',
          game: currentGame || 'best_aviator',
          source_session: activeSessionId,
        });
        setMemories(prev => [res.data, ...prev]);
      }
      setShowMemoryModal(false);
      setEditingMemory(null);
    } catch (err) {
      alert('Failed to save memory: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleQuickSaveMessage = (msgText) => {
    const defaultTitle = msgText.slice(0, 45).replace(/[#*`]/g, '').trim();
    handleOpenAddMemory(defaultTitle || 'Key Swarm Insight', msgText, 'STRATEGY_RULE');
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

      // If backend captured and created an AIDiscoveryMemory, update our state & alert user
      if (res.data.saved_memory) {
        setMemories(prev => [res.data.saved_memory, ...prev.filter(m => m.id !== res.data.saved_memory.id)]);
        setLastSavedNotification(res.data.saved_memory.title);
        setTimeout(() => setLastSavedNotification(null), 6000);
      }

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

  const getCategoryBadge = (cat) => {
    switch (cat) {
      case 'STREAK_TIMING': return 'text-blue-400 bg-blue-950/40 border-blue-800/60';
      case 'CLUSTER_PATTERN': return 'text-purple-400 bg-purple-950/40 border-purple-800/60';
      case 'STRATEGY_RULE': return 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60';
      case 'RISK_LIMIT': return 'text-rose-400 bg-rose-950/40 border-rose-800/60';
      case 'MARKET_INSIGHT': return 'text-amber-400 bg-amber-950/40 border-amber-800/60';
      default: return 'text-gray-300 bg-gray-900 border-gray-700';
    }
  };

  const activeSessionObj = sessions.find(s => s.id === activeSessionId);
  const activeMemoriesCount = memories.filter(m => m.is_active).length;

  const filteredMemories = memories.filter(m => {
    const matchesCat = selectedCategory === 'ALL' || m.category === selectedCategory;
    const matchesSearch = !memorySearch || 
      m.title?.toLowerCase().includes(memorySearch.toLowerCase()) || 
      m.content?.toLowerCase().includes(memorySearch.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Toast Notification when a discovery is saved */}
      {lastSavedNotification && (
        <div className="p-3 rounded-2xl bg-gradient-to-r from-purple-900/90 to-indigo-900/90 border border-purple-400/50 shadow-2xl flex items-center justify-between animate-in slide-in-from-top-4 duration-300">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-purple-500 flex items-center justify-center text-white shadow-md">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-1.5">
                <span>Discovery Saved to Permanent Swarm Memory!</span>
                <span className="px-1.5 py-0.2 rounded text-[10px] bg-black/40 text-purple-300 font-mono">ACTIVE</span>
              </div>
              <p className="text-[11px] text-purple-200 truncate max-w-md">"{lastSavedNotification}"</p>
            </div>
          </div>
          <button
            onClick={() => setCopilotMode('vault')}
            className="px-3 py-1.5 bg-white text-purple-900 font-bold rounded-xl text-xs hover:bg-purple-100 transition-all shadow-md shrink-0"
          >
            Open Memory Vault
          </button>
        </div>
      )}

      {/* Top AI Model & Provider Header Deck */}
      <div className="glass-card p-5 rounded-2xl border border-gray-800 bg-gradient-to-r from-gray-900/90 via-gray-900/50 to-purple-950/20 space-y-4">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
              <BrainCircuit className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-white tracking-wide">AI Staking Copilot & Knowledge Vault</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  {activeMemoriesCount} ACTIVE DISCOVERIES
                </span>
              </div>
              <p className="text-xs text-gray-400">
                Grounds predictive loss-clustering models against live telemetry and permanent saved discovery rules.
              </p>
            </div>
          </div>

          {/* Sub-View Switcher (Chat vs Knowledge Vault) */}
          <div className="flex items-center bg-gray-950/90 p-1 rounded-xl border border-gray-800 shadow-inner">
            <button
              onClick={() => setCopilotMode('chat')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                copilotMode === 'chat'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Copilot Chat</span>
            </button>
            <button
              onClick={() => setCopilotMode('vault')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                copilotMode === 'vault'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Database className="w-3.5 h-3.5 text-indigo-300" />
              <span>Memory Vault</span>
              <span className="px-1.5 py-0.2 rounded-full text-[9px] font-mono bg-black/40 text-purple-200">
                {memories.length}
              </span>
            </button>
          </div>
        </div>

        {/* Provider & Model Selectors (Deck Bar) */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-gray-800/80">
          <div className="flex flex-wrap items-center gap-2.5">
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
          </div>

          <div className="flex items-center gap-2">
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


      {/* Main Mode View: Either Copilot Chat with Radar OR Full Memory Vault */}
      {copilotMode === 'chat' ? (
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
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                          components={markdownComponents}
                        >
                          {msg.text}
                        </ReactMarkdown>
                      </div>

                      {/* User Message Actions */}
                      {msg.role === 'user' && (
                        <div className="mt-1.5 flex justify-end">
                          <button
                            onClick={() => handleCopyMessage(msg.text, msg.id || i)}
                            className="flex items-center gap-1 text-[10px] text-red-200 hover:text-white transition-colors opacity-80 hover:opacity-100"
                            title="Copy message"
                          >
                            {copiedMsgId === (msg.id || i) ? (
                              <>
                                <Check className="w-2.5 h-2.5 text-white" />
                                <span className="font-semibold text-[9px]">Copied!</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-2.5 h-2.5" />
                                <span className="text-[9px]">Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                      )}

                      {/* If this response triggered a memory save, show glowing badge */}
                      {msg.metadata?.saved_memory && (
                        <div className="mt-2.5 p-2.5 rounded-xl bg-purple-950/80 border border-purple-400/40 text-[11px] text-purple-200 flex items-center justify-between animate-in fade-in shadow-lg">
                          <div className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-purple-300 shrink-0" />
                            <div>
                              <span className="font-bold text-white block">Saved to Permanent Memory Vault:</span>
                              <span className="text-purple-200">{msg.metadata.saved_memory.title}</span>
                            </div>
                          </div>
                          <button
                            onClick={() => setCopilotMode('vault')}
                            className="px-2.5 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-bold text-[10px] transition-all shrink-0 ml-2"
                          >
                            View Vault
                          </button>
                        </div>
                      )}

                      {/* Quick Action Toolbar on Assistant Messages */}
                      {msg.role !== 'user' && (
                        <div className="mt-2.5 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] text-gray-500">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleCopyMessage(msg.text, msg.id || i)}
                              className="flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-gray-800 hover:text-gray-200 text-gray-400 transition-colors"
                              title="Copy full message text"
                            >
                              {copiedMsgId === (msg.id || i) ? (
                                <>
                                  <Check className="w-3 h-3 text-emerald-400" />
                                  <span className="text-emerald-400 font-medium">Copied!</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3 text-gray-400" />
                                  <span>Copy</span>
                                </>
                              )}
                            </button>
                            <button
                              onClick={() => handleQuickSaveMessage(msg.text)}
                              className="flex items-center gap-1 px-2 py-0.5 rounded-md hover:bg-purple-900/40 hover:text-purple-300 text-gray-400 transition-colors"
                              title="Save this finding to permanent Swarm memory"
                            >
                              <BookmarkPlus className="w-3 h-3 text-purple-400" />
                              <span>Save to Memory</span>
                            </button>
                          </div>
                          <span>{msg.createdAt ? new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                        </div>
                      )}
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
                  onClick={() => setUserInput('What time of day did all the 5-in-a-row and 6-in-a-row loss streaks happen?')}
                  className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-blue-300 hover:text-white rounded-lg text-[10px] transition-colors border border-blue-900/40 flex items-center gap-1"
                >
                  <Clock className="w-3 h-3" />
                  <span>5+ Streak Hours</span>
                </button>
                <button
                  onClick={() => setUserInput('Save our current loss streak timing finding to permanent memory')}
                  className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-purple-300 hover:text-white rounded-lg text-[10px] transition-colors border border-purple-900/40 flex items-center gap-1"
                >
                  <BookmarkPlus className="w-3 h-3" />
                  <span>Save Finding to Memory</span>
                </button>
                <button
                  onClick={() => setUserInput('What discoveries and strategic rules do we have saved in our memory vault?')}
                  className="px-2 py-1 bg-gray-900 hover:bg-gray-850 text-emerald-300 hover:text-white rounded-lg text-[10px] transition-colors border border-emerald-900/40 flex items-center gap-1"
                >
                  <Database className="w-3 h-3" />
                  <span>Recall Memory Vault</span>
                </button>
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
      ) : (
        /* Knowledge & Discovery Memory Vault View */
        <div className="glass-card p-6 border border-gray-800 rounded-2xl space-y-6">
          {/* Vault Top Bar */}
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-5 border-b border-gray-800">
            <div>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white tracking-wide">
                  Swarm Knowledge & Discovery Memory Vault
                </h3>
                <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {activeMemoriesCount} Active / {memories.length} Total
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Permanent empirical discoveries, loss-streak timing observations, and custom strategic rules. Active discoveries are automatically injected into the AI Swarm's reasoning engine.
              </p>
            </div>

            <button
              onClick={() => handleOpenAddMemory('', '', 'STREAK_TIMING')}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-indigo-600/20 transition-all shrink-0"
            >
              <Plus className="w-4 h-4" />
              <span>Add New Discovery</span>
            </button>
          </div>

          {/* Search & Category Filter Deck */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            {/* Category Filter Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              {[
                { id: 'ALL', label: 'All Discoveries' },
                { id: 'STREAK_TIMING', label: 'Streak Timing' },
                { id: 'CLUSTER_PATTERN', label: 'Cluster Patterns' },
                { id: 'STRATEGY_RULE', label: 'Strategy Rules' },
                { id: 'RISK_LIMIT', label: 'Risk Limits' },
                { id: 'MARKET_INSIGHT', label: 'Market Insights' },
                { id: 'GENERAL', label: 'General' },
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    selectedCategory === cat.id
                      ? 'bg-purple-600 text-white shadow-sm'
                      : 'bg-gray-900 text-gray-400 hover:text-gray-200 border border-gray-800'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative min-w-[240px]">
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={memorySearch}
                onChange={(e) => setMemorySearch(e.target.value)}
                placeholder="Search discoveries & rules..."
                className="w-full bg-gray-950/80 border border-gray-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
              />
            </div>
          </div>

          {/* Memories Cards Grid */}
          {loadingMemories ? (
            <div className="py-16 text-center text-xs text-gray-500 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
              <span>Loading Swarm Memory Vault...</span>
            </div>
          ) : filteredMemories.length === 0 ? (
            <div className="py-16 text-center text-xs text-gray-500 space-y-3 bg-gray-950/40 rounded-2xl border border-gray-850">
              <BookOpen className="w-8 h-8 text-gray-600 mx-auto" />
              <p className="text-sm font-medium text-gray-400">No discovery memories found in this category.</p>
              <p className="text-xs text-gray-500 max-w-sm mx-auto">
                While chatting with the Copilot, say <em>"save that to memory"</em>, or click "Add New Discovery" above to record strategic findings.
              </p>
              <button
                onClick={() => handleOpenAddMemory('', '', 'STREAK_TIMING')}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-xs font-semibold shadow-md transition-all"
              >
                Create First Discovery
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredMemories.map(mem => (
                <div
                  key={mem.id}
                  className={`p-4 rounded-2xl border transition-all flex flex-col justify-between space-y-3 ${
                    mem.is_active
                      ? 'bg-gray-900/80 border-gray-800 hover:border-purple-500/40 shadow-lg'
                      : 'bg-gray-950/40 border-gray-855 opacity-60'
                  }`}
                >
                  <div className="space-y-2.5">
                    {/* Card Header: Category & Active Toggle */}
                    <div className="flex items-center justify-between">
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-bold border ${getCategoryBadge(mem.category)}`}>
                        {mem.category?.replace('_', ' ')}
                      </span>

                      <button
                        onClick={() => handleToggleMemory(mem.id, mem.is_active)}
                        className={`flex items-center gap-1 text-[11px] font-mono font-bold px-2 py-0.5 rounded-lg border transition-colors ${
                          mem.is_active
                            ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60'
                            : 'text-gray-400 bg-gray-900 border-gray-800'
                        }`}
                        title={mem.is_active ? "Memory is ACTIVE: fed to AI swarm. Click to disable." : "Memory is DISABLED. Click to activate."}
                      >
                        {mem.is_active ? <ToggleRight className="w-3.5 h-3.5 text-emerald-400" /> : <ToggleLeft className="w-3.5 h-3.5 text-gray-500" />}
                        <span>{mem.is_active ? 'ACTIVE' : 'DISABLED'}</span>
                      </button>
                    </div>

                    {/* Title */}
                    <h4 className="text-sm font-bold text-white tracking-wide">
                      {mem.title}
                    </h4>

                    {/* Content (Rendered Markdown) */}
                    <div className="react-markdown-prose text-xs text-gray-300 leading-relaxed bg-gray-950/60 p-3 rounded-xl border border-gray-850 max-h-48 overflow-y-auto">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                        components={markdownComponents}
                      >
                        {mem.content}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* Card Footer: Metadata & Actions */}
                  <div className="pt-2 border-t border-gray-850 flex items-center justify-between text-[10px] text-gray-500">
                    <div className="flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3 text-gray-400" />
                      <span>{mem.created_at?.slice(0, 10)}</span>
                      {mem.source_session_title && (
                        <span className="truncate max-w-[110px]" title={mem.source_session_title}>
                          • {mem.source_session_title}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleOpenEditMemory(mem)}
                        className="p-1 hover:text-purple-400 text-gray-400 transition-colors"
                        title="Edit discovery"
                      >
                        <Pencil className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => handleDeleteMemory(mem.id)}
                        className="p-1 hover:text-rose-400 text-gray-400 transition-colors"
                        title="Delete discovery"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Discovery Memory Save/Edit Modal */}
      {showMemoryModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="glass-card p-6 rounded-2xl border border-purple-500/40 bg-gray-900 w-full max-w-lg space-y-4 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <BookmarkPlus className="w-5 h-5 text-purple-400" />
                <h3 className="text-sm font-bold text-white tracking-wide">
                  {editingMemory ? 'Edit Discovery Memory' : 'Save Discovery to Swarm Vault'}
                </h3>
              </div>
              <button
                onClick={() => setShowMemoryModal(false)}
                className="p-1 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveMemoryModal} className="space-y-4 text-xs">
              <div>
                <label className="block text-gray-400 mb-1 font-medium">Discovery Title:</label>
                <input
                  type="text"
                  required
                  value={memoryForm.title}
                  onChange={(e) => setMemoryForm({ ...memoryForm, title: e.target.value })}
                  placeholder="e.g., 5-in-a-row Loss Streaks Peak at 14:00 UTC"
                  className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                />
              </div>

              <div>
                <label className="block text-gray-400 mb-1 font-medium">Category:</label>
                <select
                  value={memoryForm.category}
                  onChange={(e) => setMemoryForm({ ...memoryForm, category: e.target.value })}
                  className="w-full bg-gray-950 border border-gray-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-purple-500"
                >
                  <option value="STREAK_TIMING">Streak Timing & Hour Analysis</option>
                  <option value="CLUSTER_PATTERN">Cluster & Loss Pattern</option>
                  <option value="STRATEGY_RULE">Staking & Cashout Rule</option>
                  <option value="RISK_LIMIT">Risk & Drawdown Barrier</option>
                  <option value="MARKET_INSIGHT">Market Observation</option>
                  <option value="GENERAL">General Discovery</option>
                </select>
              </div>

              <div>
                <label className="block text-gray-400 mb-1 font-medium">Discovery Content / Takeaway (Markdown supported):</label>
                <textarea
                  rows={5}
                  required
                  value={memoryForm.content}
                  onChange={(e) => setMemoryForm({ ...memoryForm, content: e.target.value })}
                  placeholder="Describe the finding, observed hours, multiplier rules, or expected value advice..."
                  className="w-full bg-gray-950 border border-gray-800 rounded-xl p-3 text-white focus:outline-none focus:border-purple-500 font-mono text-xs leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-gray-800">
                <label className="flex items-center gap-2 cursor-pointer text-gray-300">
                  <input
                    type="checkbox"
                    checked={memoryForm.is_active}
                    onChange={(e) => setMemoryForm({ ...memoryForm, is_active: e.target.checked })}
                    className="accent-purple-600 rounded"
                  />
                  <span>Active (Directly influence AI Swarm decisions)</span>
                </label>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setShowMemoryModal(false)}
                    className="px-3 py-2 rounded-xl text-gray-400 hover:text-white hover:bg-gray-800 transition-colors font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-bold shadow-md shadow-purple-600/20 transition-all"
                  >
                    {editingMemory ? 'Update Memory' : 'Save to Vault'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
