"use client";

import { useState, useMemo, useEffect } from 'react';
import { supabase } from '@/lib/supabase';
import { Users, Filter, ArrowDownWideNarrow, ArrowUpWideNarrow, Search, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';

// Common skills to populate the dropdown
const COMMON_SKILLS = [
  'Pace', 'Finishing', 'Passing', 'Tackling', 'Stamina', 'Aggression', 
  'Handling', 'Reflexes', 'Agility', 'Crossing', 'Dribbling', 'Heading', 
  'Positioning', 'Strength', 'Tech.', 'Fitness', 'Work Rate', 'Vision',
  'Jumping', 'Composure', 'Free Kick'
].sort();

export default function PlayersClient() {
  // Data state
  const [players, setPlayers] = useState<any[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  
  // Pagination
  const [page, setPage] = useState<number>(1);
  const pageSize = 50;

  // Search
  const [search, setSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');

  // Sorting & Filtering
  const [sortField, setSortField] = useState<string>('quality');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterSkill, setFilterSkill] = useState<string>('All');
  const [filterMin, setFilterMin] = useState<number>(0);

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // reset to first page on search change
    }, 500);
    return () => clearTimeout(handler);
  }, [search]);

  // Reset page when filters or sort change
  useEffect(() => {
    setPage(1);
  }, [sortField, sortOrder, filterSkill, filterMin]);

  // Fetch data
  useEffect(() => {
    let isMounted = true;

    async function fetchPlayers() {
      setLoading(true);

      try {
        let query = supabase
          .from('players')
          .select('*', { count: 'exact' });

        // Apply Search (name or id)
        if (debouncedSearch) {
          query = query.or(`name.ilike.%${debouncedSearch}%,id.eq.${debouncedSearch},id.ilike.%${debouncedSearch}%`);
        }

        // Apply Skill Filter using Supabase JSONB querying -> text cast
        // Note: ->> performs string comparison so we might need to rely on DB,
        // but for exact/gte match on PostgREST, we can use JSON path querying.
        if (filterSkill !== 'All' && filterMin > 0) {
          // In PostgREST, we can query jsonb by casting it to int implicitly via filter
          // Actually, text `>=` works okay for single digit vs double digit? No, "10" < "5"
          // We will use the standard text comparison since PostgREST limits us without a custom View,
          // but we can pad it or just use it as is.
          // For now, let's use numeric GTE on the JSONB extracted text scalar.
          query = query.gte(`skills->>${filterSkill}`, filterMin);
        }

        // Apply Sorting
        if (sortField.startsWith('skill:')) {
          const skillName = sortField.split(':')[1];
          // Sort by JSONB field scalar. Note: text sort.
          query = query.order(`skills->>${skillName}`, { ascending: sortOrder === 'asc', nullsFirst: false });
        } else {
          query = query.order(sortField, { ascending: sortOrder === 'asc', nullsFirst: false });
        }
        
        // For stable sort if ties occur
        query = query.order('id', { ascending: true });

        // Apply Pagination
        const from = (page - 1) * pageSize;
        const to = from + pageSize - 1;
        query = query.range(from, to);

        const { data, count, error } = await query;
        
        if (error) throw error;

        if (isMounted) {
          setPlayers(data || []);
          setTotalCount(count || 0);
        }
      } catch (err) {
        console.error('Error fetching players:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchPlayers();

    return () => { isMounted = false; };
  }, [debouncedSearch, sortField, sortOrder, filterSkill, filterMin, page]);

  // Combined skills from common standard + whatever is in the current page
  const allSkills = useMemo(() => {
    const skillsSet = new Set<string>(COMMON_SKILLS);
    players.forEach(p => {
      if (p.skills) {
        Object.keys(p.skills).forEach(s => skillsSet.add(s));
      }
    });
    return Array.from(skillsSet).sort();
  }, [players]);

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent flex items-center gap-3">
            <Users size={32} className="text-emerald-400" />
            All Players
          </h1>
          <p className="text-neutral-400 mt-2">
            Showing {players.length} of {totalCount} players.
          </p>
        </div>
        
        {/* Controls */}
        <div className="flex flex-wrap items-end gap-3 bg-neutral-900/40 p-3 rounded-xl border border-neutral-800 shadow-inner">
          <div className="flex flex-col gap-1 flex-1 min-w-[200px]">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Search size={10}/> Search Name/ID
            </label>
            <input 
              type="text"
              placeholder="e.g. Messi or 123456"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-full outline-none focus:border-emerald-500 transition-colors"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block"></div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10}/> Filter By Skill
            </label>
            <select 
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-emerald-500 transition-colors"
              value={filterSkill}
              onChange={(e) => setFilterSkill(e.target.value)}
            >
              <option value="All">All Skills</option>
              {allSkills.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500">Min Rating</label>
            <input 
              type="number"
              min="0"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-24 outline-none focus:border-emerald-500 transition-colors"
              value={filterMin}
              onChange={(e) => setFilterMin(Number(e.target.value))}
              disabled={filterSkill === 'All'}
            />
          </div>
          
          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block"></div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              {sortOrder === 'asc' ? <ArrowUpWideNarrow size={10}/> : <ArrowDownWideNarrow size={10}/>} Sort By
            </label>
            <div className="flex gap-2">
              <select 
                className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-emerald-500 transition-colors"
                value={sortField}
                onChange={(e) => setSortField(e.target.value)}
              >
                <optgroup label="Basic Attributes">
                  <option value="quality">Quality</option>
                  <option value="potential">Potential</option>
                  <option value="age">Age</option>
                </optgroup>
                <optgroup label="Specific Skills">
                  {allSkills.map(s => <option key={s} value={`skill:${s}`}>{s}</option>)}
                </optgroup>
              </select>
              <button 
                onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
                className="bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 hover:border-emerald-500/50 p-2 rounded-lg text-neutral-300 transition-all flex items-center justify-center"
                title={`Sort ${sortOrder === 'asc' ? 'Descending' : 'Ascending'}`}
              >
                {sortOrder === 'asc' ? <ArrowUpWideNarrow size={18} className="text-emerald-400" /> : <ArrowDownWideNarrow size={18} className="text-emerald-400" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-xl shadow-black/50 relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-neutral-900/80 backdrop-blur-sm z-10 flex items-center justify-center flex-col gap-3">
             <Loader2 className="animate-spin text-emerald-500" size={40} />
             <p className="text-emerald-400 font-medium animate-pulse">Fetching Players...</p>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-950/50 border-b border-neutral-800">
              <tr>
                <th scope="col" className="px-6 py-4 font-semibold">Name</th>
                <th scope="col" className="px-6 py-4 font-semibold">Pos</th>
                <th scope="col" className="px-6 py-4 font-semibold">Age</th>
                <th scope="col" className="px-6 py-4 font-semibold">Quality</th>
                <th scope="col" className="px-6 py-4 font-semibold">Potential</th>
                <th scope="col" className="px-6 py-4 font-semibold">Nationality</th>
                <th scope="col" className="px-6 py-4 font-semibold">Skills</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {players.map((player) => (
                <tr key={player.id} className="hover:bg-neutral-800/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-white flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold shrink-0">
                      {player.name?.charAt(0) || '?'}
                    </div>
                    <div className="flex flex-col">
                      {player.url ? (
                        <a href={player.url} target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400 hover:underline">
                          {player.name}
                        </a>
                      ) : (
                        player.name
                      )}
                      <span className="text-neutral-500 text-[10px] font-mono leading-tight mt-0.5">#{player.id}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded-md bg-neutral-800 text-neutral-300 text-xs font-medium border border-neutral-700/50">
                      {player.position}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-neutral-300">{player.age}</td>
                  <td className="px-6 py-4 text-emerald-400 font-medium">{player.quality}</td>
                  <td className="px-6 py-4 text-cyan-400 font-medium">{player.potential}</td>
                  <td className="px-6 py-4 text-neutral-300">{player.nationality}</td>
                  <td className="px-6 py-4 h-full relative" style={{ maxWidth: '300px' }}>
                    <div className="flex flex-wrap gap-1 max-h-16 overflow-y-auto pr-2 custom-scrollbar">
                      {player.skills && Object.keys(player.skills).length > 0 ? (
                        Object.entries(player.skills).map(([skill, value]) => {
                          const isHighlighted = (filterSkill === skill) || (sortField === `skill:${skill}`);
                          return (
                            <span 
                              key={skill} 
                              className={`px-2 py-[2px] rounded text-[10px] font-medium flex items-center gap-1 border transition-colors ${
                                isHighlighted 
                                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300' 
                                  : 'bg-neutral-800/80 border-neutral-700 text-neutral-300'
                              }`}
                            >
                              <span className={isHighlighted ? 'text-emerald-400' : 'text-white/60'}>
                                {skill}
                              </span>
                              <span className={isHighlighted ? 'text-emerald-300 font-bold' : 'text-emerald-400'}>
                                {String(value)}
                              </span>
                            </span>
                          );
                        })
                      ) : (
                        <span className="text-neutral-600 text-xs italic">No skills</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {!loading && players.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center text-neutral-500">
                      <Filter size={32} className="mb-3 opacity-50" />
                      <p className="text-base font-medium text-neutral-400">No players found matching your criteria</p>
                      <p className="text-sm mt-1">Try lowering the minimum rating or changing the search/filter parameters.</p>
                      <button 
                        onClick={() => { setFilterSkill('All'); setFilterMin(0); setSearch(''); }}
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

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-neutral-800 bg-neutral-950/30 flex items-center justify-between">
            <span className="text-sm text-neutral-400">
              Showing <span className="text-white font-medium">{(page - 1) * pageSize + 1}</span> to <span className="text-white font-medium">{Math.min(page * pageSize, totalCount)}</span> of <span className="text-white font-medium">{totalCount}</span> results
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
