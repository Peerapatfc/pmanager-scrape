"use client";

import { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import {
  Bot, ExternalLink, Filter, ArrowDownWideNarrow, ArrowUpWideNarrow,
  Search, ChevronLeft, ChevronRight, Loader2, ArrowUpRight,
} from 'lucide-react';

const POSITIONS = ['GK', 'DL', 'DC', 'DR', 'DMC', 'ML', 'MC', 'MR', 'AML', 'AMC', 'AMR', 'SC'];
const QUALITIES = ['World Class', 'Excellent', 'Formidable', 'Very Good', 'Good', 'Passable', 'Bad', 'Low'];

export default function BotOpportunitiesClient() {
  const [rows, setRows] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const [page, setPage] = useState(1);
  const pageSize = 50;

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  const [filterQuality, setFilterQuality] = useState('All');
  const [filterPos, setFilterPos] = useState('All');
  const [sortField, setSortField] = useState('profit_margin');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Debounce search
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 500);
    return () => clearTimeout(handler);
  }, [search]);

  // Reset page on filter/sort change
  useEffect(() => {
    setPage(1);
  }, [filterQuality, filterPos, sortField, sortOrder]);

  // Fetch
  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      setLoading(true);
      try {
        let query = supabase
          .from('bot_opportunities')
          .select('*', { count: 'exact' });

        if (debouncedSearch) {
          query = query.ilike('name', `%${debouncedSearch}%`);
        }
        if (filterQuality !== 'All') {
          query = query.eq('quality', filterQuality);
        }
        if (filterPos !== 'All') {
          query = query.eq('position', filterPos);
        }

        query = query.order(sortField, { ascending: sortOrder === 'asc', nullsFirst: false });
        if (sortField !== 'id') {
          query = query.order('id', { ascending: true });
        }

        const from = (page - 1) * pageSize;
        query = query.range(from, from + pageSize - 1);

        const { data, count, error } = await query;
        if (error) throw error;

        if (isMounted) {
          setRows(data || []);
          setTotalCount(count || 0);
        }
      } catch (err) {
        console.error('Error fetching bot opportunities:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchData();
    return () => { isMounted = false; };
  }, [debouncedSearch, filterQuality, filterPos, sortField, sortOrder, page]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const fmt = (val: number) => val ? val.toLocaleString('en-US') : '0';

  const qualityColor = (q: string) => {
    if (!q) return 'text-neutral-400';
    if (['World Class', 'Formidable'].includes(q)) return 'text-yellow-400';
    if (q === 'Excellent') return 'text-emerald-400';
    if (q === 'Very Good') return 'text-cyan-400';
    if (q === 'Good') return 'text-blue-400';
    return 'text-neutral-400';
  };

  const marginColor = (m: number) => {
    if (m >= 50) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
    if (m >= 20) return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    return 'bg-neutral-800 text-neutral-400 border-neutral-700';
  };

  const clearFilters = () => {
    setSearch('');
    setFilterQuality('All');
    setFilterPos('All');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-3">
            <Bot size={32} className="text-purple-400" />
            Bot Opportunities
          </h1>
          <p className="text-neutral-400 mt-2">
            Showing {rows.length} of {totalCount} players from BOT teams.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-end gap-3 bg-neutral-900/40 p-3 rounded-xl border border-neutral-800 shadow-inner">
          {/* Search */}
          <div className="flex flex-col gap-1 flex-1 min-w-[180px]">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Search size={10} /> Search Name
            </label>
            <input
              type="text"
              placeholder="e.g. Messi"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-full outline-none focus:border-purple-500 transition-colors"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          {/* Quality filter */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Quality
            </label>
            <select
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-purple-500 transition-colors"
              value={filterQuality}
              onChange={(e) => setFilterQuality(e.target.value)}
            >
              <option value="All">All Qualities</option>
              {QUALITIES.map(q => <option key={q} value={q}>{q}</option>)}
            </select>
          </div>

          {/* Position filter */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Position
            </label>
            <select
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-purple-500 transition-colors"
              value={filterPos}
              onChange={(e) => setFilterPos(e.target.value)}
            >
              <option value="All">All Positions</option>
              {POSITIONS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          {/* Sort */}
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              {sortOrder === 'asc' ? <ArrowUpWideNarrow size={10} /> : <ArrowDownWideNarrow size={10} />} Sort By
            </label>
            <div className="flex gap-2">
              <select
                className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-purple-500 transition-colors"
                value={sortField}
                onChange={(e) => setSortField(e.target.value)}
              >
                <option value="profit_margin">Profit Margin (%)</option>
                <option value="value_diff">Value Diff</option>
                <option value="estimated_value">Est. Value</option>
                <option value="asking_price">Asking Price</option>
                <option value="age">Age</option>
              </select>
              <button
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                className="bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 hover:border-purple-500/50 p-2 rounded-lg text-neutral-300 transition-all flex items-center justify-center"
                title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
              >
                {sortOrder === 'asc'
                  ? <ArrowUpWideNarrow size={18} className="text-purple-400" />
                  : <ArrowDownWideNarrow size={18} className="text-purple-400" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-xl shadow-black/50 relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-neutral-900/80 backdrop-blur-sm z-30 flex items-center justify-center flex-col gap-3">
            <Loader2 className="animate-spin text-purple-500" size={40} />
            <p className="text-purple-400 font-medium animate-pulse">Fetching Opportunities...</p>
          </div>
        )}

        <div className="overflow-x-auto max-h-[600px] 2xl:max-h-[800px] border-t border-neutral-800 custom-scrollbar">
          <table className="w-full text-sm text-left border-collapse whitespace-nowrap">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-950 sticky top-0 z-20 shadow-sm">
              <tr>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Player</th>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Pos</th>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Quality</th>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800">BOT Team</th>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Asking Price</th>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Est. Value</th>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Value Diff</th>
                <th className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Margin</th>
                <th className="px-4 py-3 font-semibold border-b border-neutral-800 text-center">Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {rows.map((opp) => (
                <tr key={opp.id} className="hover:bg-neutral-800/60 transition-colors even:bg-neutral-900/40">
                  <td className="px-4 py-3 font-medium text-white border-r border-neutral-800/60">
                    <div className="font-semibold">{opp.name}</div>
                    <div className="text-xs text-neutral-500">ID: {opp.id}</div>
                  </td>
                  <td className="px-4 py-3 border-r border-neutral-800/60">
                    <span className="px-2.5 py-1 rounded-md bg-neutral-800 text-neutral-300 text-xs font-medium border border-neutral-700/50">
                      {opp.position}
                    </span>
                  </td>
                  <td className="px-4 py-3 border-r border-neutral-800/60">
                    <span className={`font-medium ${qualityColor(opp.quality)}`}>{opp.quality}</span>
                  </td>
                  <td className="px-4 py-3 text-neutral-300 border-r border-neutral-800/60">
                    <span className="flex items-center gap-1.5">
                      <Bot size={13} className="text-neutral-500 shrink-0" />
                      {opp.team_name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-medium text-white border-r border-neutral-800/60">
                    ${fmt(opp.asking_price)}
                  </td>
                  <td className="px-4 py-3 text-right text-neutral-400 border-r border-neutral-800/60">
                    ${fmt(opp.estimated_value)}
                  </td>
                  <td className="px-4 py-3 text-right border-r border-neutral-800/60">
                    <span className="text-emerald-400 font-medium flex items-center justify-end gap-0.5">
                      <ArrowUpRight size={13} />
                      ${fmt(opp.value_diff)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right border-r border-neutral-800/60">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${marginColor(opp.profit_margin)}`}>
                      {opp.profit_margin}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {opp.url ? (
                      <a
                        href={opp.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center p-2 rounded-lg bg-neutral-800 text-neutral-300 hover:bg-purple-500/20 hover:text-purple-400 hover:border-purple-500/50 border border-transparent transition-all"
                        title="View on PManager"
                      >
                        <ExternalLink size={15} />
                      </a>
                    ) : (
                      <span className="text-neutral-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center text-neutral-500">
                      <Filter size={32} className="mb-3 opacity-50" />
                      <p className="text-base font-medium text-neutral-400">No players found matching your criteria</p>
                      <button
                        onClick={clearFilters}
                        className="mt-4 px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg text-sm transition-colors border border-neutral-700 cursor-pointer"
                      >
                        Clear Filters
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-neutral-800 bg-neutral-950/30 flex items-center justify-between">
            <span className="text-sm text-neutral-400">
              Showing{' '}
              <span className="text-white font-medium">{(page - 1) * pageSize + 1}</span>
              {' '}to{' '}
              <span className="text-white font-medium">{Math.min(page * pageSize, totalCount)}</span>
              {' '}of{' '}
              <span className="text-white font-medium">{totalCount}</span> results
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 bg-neutral-900 border border-neutral-700 rounded-lg hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed text-neutral-300 transition-colors"
              >
                <ChevronLeft size={18} />
              </button>
              <div className="flex items-center justify-center px-4 bg-neutral-900 border border-neutral-700 rounded-lg text-sm font-medium text-white">
                Page {page} of {totalPages}
              </div>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-2 bg-neutral-900 border border-neutral-700 rounded-lg hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed text-neutral-300 transition-colors"
              >
                <ChevronRight size={18} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
