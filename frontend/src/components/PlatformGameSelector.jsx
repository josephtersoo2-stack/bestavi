import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layers, Gamepad2, ChevronDown } from 'lucide-react';
import { API_BASE } from '../config';

export default function PlatformGameSelector({ currentPlatform, currentGame, onChange }) {
  const [platforms, setPlatforms] = useState([]);
  const [openDropdown, setOpenDropdown] = useState(false);

  useEffect(() => {
    fetchPlatforms();
  }, []);

  const fetchPlatforms = async () => {
    try {
      const res = await axios.get(`${API_BASE}/platforms/`);
      setPlatforms(res.data.platforms || []);
    } catch (err) {
      console.error('Failed to fetch platforms:', err);
    }
  };

  const activePlatformObj = platforms.find(p => p.id.toLowerCase() === (currentPlatform || 'ilotbet').toLowerCase()) || platforms[0];
  const activeGames = activePlatformObj ? activePlatformObj.games : [];
  const activeGameObj = activeGames.find(g => 
    g.id.toLowerCase() === (currentGame || 'best_aviator').toLowerCase() || 
    (g.aliases && g.aliases.includes(currentGame))
  ) || activeGames[0];

  const handleSelect = (platformId, gameId) => {
    setOpenDropdown(false);
    if (onChange) {
      onChange(platformId, gameId);
    }
  };

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setOpenDropdown(!openDropdown)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-gray-900/90 hover:bg-gray-850 border border-gray-750 hover:border-gray-600 transition-all text-xs font-mono group"
        title="Switch Platform & Game Type"
      >
        <div className="w-2 h-2 rounded-full bg-emerald-400 group-hover:scale-110 transition-transform"></div>
        <div className="flex items-center gap-1.5">
          <span className="font-bold text-white tracking-wide">
            {activePlatformObj ? activePlatformObj.name : 'iLOTBET'}
          </span>
          <span className="text-gray-600 font-sans">•</span>
          <span className="text-red-400 font-medium">
            {activeGameObj ? activeGameObj.name : 'Best Aviator'}
          </span>
        </div>
        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-200 ${openDropdown ? 'rotate-180' : ''}`} />
      </button>

      {/* Popover Menu */}
      {openDropdown && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpenDropdown(false)}></div>
          <div className="absolute left-0 mt-2 w-72 rounded-2xl bg-gray-950/95 backdrop-blur-xl border border-gray-800 shadow-2xl p-3 z-50 animate-in fade-in slide-in-from-top-2 duration-150 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-gray-850 text-[11px] text-gray-400 font-semibold uppercase tracking-wider px-1">
              <span className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-red-500" />
                Select Platform & Game
              </span>
              <span className="text-[10px] text-emerald-400">Addon System</span>
            </div>

            <div className="space-y-2">
              {platforms.map(platform => {
                const isCurrentPlatform = platform.id.toLowerCase() === (currentPlatform || 'ilotbet').toLowerCase();

                return (
                  <div key={platform.id} className="p-2 rounded-xl bg-gray-900/60 border border-gray-800/80 space-y-1.5">
                    <div className="flex items-center justify-between text-xs font-bold text-white px-1">
                      <span>{platform.name}</span>
                      <span className="text-[10px] font-mono text-gray-500">{platform.games.length} game{platform.games.length > 1 ? 's' : ''}</span>
                    </div>

                    <div className="grid grid-cols-1 gap-1">
                      {platform.games.map(game => {
                        const isCurrentGame = isCurrentPlatform && game.id.toLowerCase() === (currentGame || 'aviator').toLowerCase();

                        return (
                          <button
                            key={game.id}
                            onClick={() => handleSelect(platform.id, game.id)}
                            className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-all ${
                              isCurrentGame
                                ? 'bg-red-600/90 text-white font-semibold shadow-sm'
                                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                            }`}
                          >
                            <span className="flex items-center gap-2">
                              <Gamepad2 className="w-3.5 h-3.5 text-gray-400" />
                              {game.name}
                            </span>
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-black/40 text-gray-400">
                              {game.category}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="pt-1 text-[10px] text-gray-500 text-center">
              New platforms and games can be added under <code className="text-gray-400">aviator_bot/platforms/</code>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
