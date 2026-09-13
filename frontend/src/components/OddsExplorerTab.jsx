import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Database, Download, Filter, RefreshCw, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { API_BASE } from '../config';

export default function OddsExplorerTab() {
  const [odds, setOdds] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState('all');
  const [searchMin, setSearchMin] = useState('');
  const [searchMax, setSearchMax] = useState('');

  const fetchOdds = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/odds/?page=${page}`;
      if (filterType === 'under_2x') url += '&under_2x=true';
      if (filterType === 'over_10x') url += '&min_multiplier=10.0';
      if (searchMin) url += `&min_multiplier=${searchMin}`;
      if (searchMax) url += `&max_multiplier=${searchMax}`;

      const res = await axios.get(url);
      setOdds(res.data.results || []);
      setTotalCount(res.data.count || 0);
    } catch (err) {
      console.error('Failed to fetch odds from database:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOdds();
  }, [page, filterType]);

  const handleApplyFilter = (type) => {
    setFilterType(type);
    setPage(1);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchOdds();
  };

  const getBadgeClass = (val) => {
    if (val >= 10.0) return 'badge-gold';
    if (val >= 2.0) return 'badge-purple';
    return 'badge-blue';
  };

  const totalPages = Math.ceil(totalCount / 50) || 1;

  return (
    <div className="space-y-6">
      {/* Top Header Card */}
      <div className="glass-card p-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-red-500/10 rounded-xl text-red-500">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">PostgreSQL Database Odds Explorer</h3>
            <p className="text-xs text-gray-400">
              Total {totalCount.toLocaleString()} crash multipliers recorded & stored in database.
            </p>
          </div>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center gap-3">
          <a
            href={`${API_BASE}/export/odds/?format=csv`}
            download="extracted_odds.csv"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-emerald-400" />
            <span>Export CSV</span>
          </a>
          <a
            href={`${API_BASE}/export/odds/?format=json`}
            download="extracted_odds.json"
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors shadow-sm"
          >
            <Download className="w-3.5 h-3.5 text-blue-400" />
            <span>Export JSON</span>
          </a>
          <button
            onClick={fetchOdds}
            disabled={loading}
            className="p-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition-colors"
            title="Refresh database records"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-red-400' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Chips & Search Bar */}
      <div className="glass-card p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
          <span className="text-xs text-gray-500 font-medium flex items-center gap-1 shrink-0">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </span>
          {[
            { id: 'all', label: 'All Rounds' },
            { id: 'under_2x', label: 'Under 2.0x (Crash)' },
            { id: 'over_10x', label: '10.0x+ (High Flyers)' },
          ].map(f => (
            <button
              key={f.id}
              onClick={() => handleApplyFilter(f.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                filterType === f.id
                  ? 'bg-red-500/20 text-red-400 border border-red-500/40 font-semibold'
                  : 'bg-gray-900/60 text-gray-400 hover:text-white border border-gray-800'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {/* Multiplier Search Form */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full md:w-auto">
          <input
            type="number"
            step="0.1"
            placeholder="Min x"
            value={searchMin}
            onChange={(e) => setSearchMin(e.target.value)}
            className="w-20 bg-gray-900/80 border border-gray-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-red-500 font-mono"
          />
          <span className="text-gray-600">-</span>
          <input
            type="number"
            step="0.1"
            placeholder="Max x"
            value={searchMax}
            onChange={(e) => setSearchMax(e.target.value)}
            className="w-20 bg-gray-900/80 border border-gray-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-red-500 font-mono"
          />
          <button
            type="submit"
            className="p-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* Odds Data Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-gray-800 bg-gray-900/40 text-gray-400 uppercase tracking-wider">
                <th className="py-3 px-4"># ID</th>
                <th className="py-3 px-4">Crash Multiplier</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Platform</th>
                <th className="py-3 px-4 text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-850">
              {odds && odds.length > 0 ? (
                odds.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-800/30 transition-colors">
                    <td className="py-3 px-4 text-gray-500 font-mono">#{o.id}</td>
                    <td className="py-3 px-4 font-bold">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold tracking-tight inline-block shadow-sm ${getBadgeClass(o.multiplier)}`}>
                        {o.multiplier.toFixed(2)}x
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {o.multiplier >= 10.0 ? (
                        <span className="text-amber-400 font-semibold">Mega Crash (10x+)</span>
                      ) : o.multiplier >= 2.0 ? (
                        <span className="text-purple-400 font-semibold">Standard (2x - 10x)</span>
                      ) : (
                        <span className="text-blue-400">Early Crash (&lt;2x)</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-400 uppercase">{o.site}</td>
                    <td className="py-3 px-4 text-gray-400 text-right font-mono">
                      {new Date(o.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" className="py-12 text-center text-gray-500 italic">
                    {loading ? 'Querying database...' : 'No multiplier records match the selected filters.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-gray-800 flex items-center justify-between text-xs text-gray-400">
          <span>
            Showing Page <b>{page}</b> of <b>{totalPages}</b> ({totalCount.toLocaleString()} items)
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1 || loading}
              className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed text-gray-300 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:opacity-30 disabled:cursor-not-allowed text-gray-300 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
