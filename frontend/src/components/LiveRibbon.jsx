import React from 'react';
import { Activity, Flame, Radio } from 'lucide-react';

export default function LiveRibbon({ multipliers = [], isConnected = false }) {
  const getBadgeClass = (val) => {
    if (val >= 10.0) return 'badge-gold';
    if (val >= 2.0) return 'badge-purple';
    return 'badge-blue';
  };

  return (
    <div className="glass-card p-3 mb-6 flex flex-col md:flex-row items-center justify-between gap-3 overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-1 bg-gray-900/80 rounded-full border border-gray-800 shrink-0">
        <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-400 live-pulse' : 'bg-amber-400'}`}></span>
        <span className="text-xs font-semibold tracking-wider uppercase text-gray-300 flex items-center gap-1">
          <Radio className="w-3.5 h-3.5 text-red-500" />
          Live Game Ribbon
        </span>
      </div>

      <div className="flex items-center gap-2 overflow-x-auto w-full py-1 scrollbar-none">
        {multipliers && multipliers.length > 0 ? (
          multipliers.map((mult, idx) => (
            <div
              key={idx}
              className={`px-3 py-1 rounded-full text-xs font-bold tracking-tight shrink-0 shadow-md transform hover:scale-105 transition-all ${getBadgeClass(
                mult
              )}`}
            >
              {typeof mult === 'number' ? `${mult.toFixed(2)}x` : mult}
            </div>
          ))
        ) : (
          <span className="text-xs text-gray-500 italic flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 animate-spin text-gray-400" />
            Connecting to in-game multiplier ribbon...
          </span>
        )}
      </div>
    </div>
  );
}
