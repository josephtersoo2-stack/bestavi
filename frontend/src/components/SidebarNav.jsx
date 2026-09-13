import React from 'react';
import {
  LayoutDashboard,
  BrainCircuit,
  MessageSquareText,
  TrendingUp,
  ShieldCheck,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  Zap,
  Activity,
  Layers,
  Radio
} from 'lucide-react';

export default function SidebarNav({
  activeTab,
  setActiveTab,
  botStatus,
  config,
  swarmConsensus,
  collapsed,
  setCollapsed
}) {
  const isRunning = botStatus?.is_running;
  const isStaking = botStatus?.is_staking;
  const isAutonomous = config?.ai_autonomous_mode;

  const navItems = [
    {
      id: 'dashboard',
      label: 'Control Center',
      shortLabel: 'Control',
      icon: LayoutDashboard,
      badge: isRunning ? (isStaking ? 'STAKING' : 'OBSERVE') : null,
      badgeColor: isStaking ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
    },
    {
      id: 'swarm',
      label: 'Multi-Agent Deck',
      shortLabel: 'Agents',
      icon: BrainCircuit,
      badge: swarmConsensus?.consensus_directive || '4 AGENTS',
      badgeColor: swarmConsensus?.consensus_directive === 'PAUSE_STAKING'
        ? 'bg-red-500/20 text-red-400 border-red-500/30'
        : 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
    },
    {
      id: 'copilot',
      label: 'AI Copilot & Chats',
      shortLabel: 'Copilot',
      icon: MessageSquareText,
      badge: 'MEMORY',
      badgeColor: 'bg-purple-500/20 text-purple-400 border-purple-500/30'
    },
    {
      id: 'odds',
      label: 'Live Odds Stream',
      shortLabel: 'Odds',
      icon: TrendingUp
    },
    {
      id: 'safezone',
      label: 'SafeZone Analytics',
      shortLabel: 'SafeZone',
      icon: ShieldCheck
    },
    {
      id: 'analytics',
      label: 'Ledger & History',
      shortLabel: 'Ledger',
      icon: BarChart3
    },
    {
      id: 'settings',
      label: 'Config & Platform',
      shortLabel: 'Settings',
      icon: Settings
    }
  ];

  return (
    <aside
      className={`app-sidebar ${collapsed ? 'collapsed' : ''}`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-850">
        {!collapsed ? (
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-red-500 to-rose-700 flex items-center justify-center shadow-lg shadow-red-900/30 shrink-0">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="font-extrabold text-sm text-white tracking-wide truncate">
                BEST AVIATOR
              </h1>
              <div className="flex items-center gap-1.5 text-[10px] text-gray-400 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>ENTERPRISE SWARM</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="mx-auto">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-rose-700 flex items-center justify-center shadow-lg shadow-red-900/30">
              <Zap className="w-5 h-5 text-white" />
            </div>
          </div>
        )}

        {/* Toggle Collapse Button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg bg-gray-900 hover:bg-gray-800 text-gray-400 hover:text-white border border-gray-800 transition-colors"
          title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Live Status Quick Pill (when expanded) */}
      {!collapsed && (
        <div className="px-3 pt-3 pb-1">
          <div className="p-2.5 rounded-xl bg-gray-900/60 border border-gray-850 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Radio className={`w-3.5 h-3.5 ${isRunning ? 'text-emerald-400 animate-pulse' : 'text-gray-500'}`} />
              <div>
                <div className="text-[11px] font-bold text-gray-200">
                  {isRunning ? (isStaking ? 'Live Staking' : 'Observation Mode') : 'Engine Idle'}
                </div>
                <div className="text-[10px] font-mono text-gray-500 truncate">
                  {config?.platform?.toUpperCase()} • {config?.game === 'best_aviator' ? 'Best Aviator' : config?.game?.toUpperCase()}
                </div>
              </div>
            </div>

            {isAutonomous && (
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30">
                AUTO-AI
              </span>
            )}
          </div>
        </div>
      )}

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-3 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all group ${
                isActive
                  ? 'bg-red-600 text-white shadow-lg shadow-red-900/20 border border-red-500/40'
                  : 'text-gray-400 hover:text-white hover:bg-gray-900 border border-transparent'
              } ${collapsed ? 'justify-center px-0' : ''}`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-red-400'}`} />

              {!collapsed && (
                <div className="flex-1 flex items-center justify-between min-w-0">
                  <span className="truncate">{item.label}</span>
                  {item.badge && (
                    <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border uppercase tracking-wider shrink-0 ${
                      isActive ? 'bg-black/30 text-white border-white/20' : item.badgeColor || 'bg-gray-800 text-gray-300 border-gray-700'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Bottom Swarm Consensus Indicator (When Expanded) */}
      {!collapsed && swarmConsensus && (
        <div className="p-3 mx-3 mb-3 rounded-xl bg-gradient-to-br from-gray-900 to-gray-950 border border-gray-800 text-[11px] space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-gray-400 font-medium">Swarm Consensus</span>
            <span className={`font-mono font-bold px-1.5 py-0.5 rounded text-[10px] ${
              swarmConsensus.consensus_directive === 'PAUSE_STAKING'
                ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
            }`}>
              {swarmConsensus.consensus_directive}
            </span>
          </div>
          <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                swarmConsensus.consensus_score >= 70 ? 'bg-emerald-400' : (swarmConsensus.consensus_score >= 50 ? 'bg-amber-400' : 'bg-red-400')
              }`}
              style={{ width: `${Math.min(100, Math.max(5, swarmConsensus.consensus_score || 50))}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-[10px] text-gray-500 font-mono">
            <span>Score: {swarmConsensus.consensus_score}%</span>
            <span>{swarmConsensus.consensus_sentiment}</span>
          </div>
        </div>
      )}

      {/* User / Host Platform Footer */}
      <div className="p-3 border-t border-gray-850 text-center">
        {!collapsed ? (
          <div className="text-[11px] text-gray-500 flex items-center justify-between px-1">
            <span className="font-mono">v3.2 Autonomous</span>
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
          </div>
        ) : (
          <div className="inline-block w-2 h-2 rounded-full bg-emerald-500" title="System Online"></div>
        )}
      </div>
    </aside>
  );
}
