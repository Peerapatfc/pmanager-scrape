"use client";

import { useState, useEffect } from "react";
import {
  Users,
  Filter,
  ArrowDownWideNarrow,
  ArrowUpWideNarrow,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
} from "lucide-react";

import { supabase } from "@/lib/supabase";
import { PAGE_SIZE, DEBOUNCE_MS, POSITIONS, QUALITIES } from "@/lib/constants";
import { qualityColor } from "@/lib/utils";
import { SKILLS } from "@/lib/skills";
import { SkillChip } from "@/lib/SkillChip";
import type { Player } from "@/types";

export default function PlayersClient() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sortField, setSortField] = useState("quality");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [filterSkill, setFilterSkill] = useState("All");
  const [filterMin, setFilterMin] = useState(0);
  const [filterPos, setFilterPos] = useState("");
  const [filterQuality, setFilterQuality] = useState("");

  // Debounce search
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [search]);

  // Reset page when filters/sort change
  useEffect(() => {
    setPage(1);
  }, [sortField, sortOrder, filterSkill, filterMin, filterPos, filterQuality]);

  // Fetch players
  useEffect(() => {
    let isMounted = true;

    async function fetchPlayers() {
      setLoading(true);
      setError(null);

      try {
        let query = supabase.from("players").select("*", { count: "exact" });

        if (debouncedSearch) {
          query = query.or(
            `name.ilike.%${debouncedSearch}%,id.eq.${debouncedSearch},id.ilike.%${debouncedSearch}%`
          );
        }

        if (filterPos) query = query.eq("position", filterPos);
        if (filterQuality) query = query.eq("quality", filterQuality);
        if (filterSkill !== "All" && filterMin > 0) {
          query = query.gte(`skills->>${filterSkill}`, filterMin);
        }

        if (sortField.startsWith("skill:")) {
          const skillName = sortField.split(":")[1];
          query = query.order(`skills->>${skillName}`, {
            ascending: sortOrder === "asc",
            nullsFirst: false,
          });
        } else {
          query = query.order(sortField, {
            ascending: sortOrder === "asc",
            nullsFirst: false,
          });
        }
        query = query.order("id", { ascending: true });

        const from = (page - 1) * PAGE_SIZE;
        query = query.range(from, from + PAGE_SIZE - 1);

        const { data, count, error: supabaseError } = await query;
        if (supabaseError) throw supabaseError;

        if (isMounted) {
          setPlayers((data as Player[]) ?? []);
          setTotalCount(count ?? 0);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load players.");
          setPlayers([]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchPlayers();
    return () => { isMounted = false; };
  }, [debouncedSearch, sortField, sortOrder, filterSkill, filterMin, filterPos, filterQuality, page]);

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

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
              <Search size={10} /> Search Name/ID
            </label>
            <input
              type="text"
              aria-label="Search players by name or ID"
              placeholder="e.g. Messi or 123456"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-full outline-none focus:border-emerald-500 transition-colors"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Position
            </label>
            <select
              aria-label="Filter by position"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-emerald-500 transition-colors"
              value={filterPos}
              onChange={(e) => setFilterPos(e.target.value)}
            >
              <option value="">All Positions</option>
              {POSITIONS.filter(Boolean).map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Quality
            </label>
            <select
              aria-label="Filter by quality"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-emerald-500 transition-colors"
              value={filterQuality}
              onChange={(e) => setFilterQuality(e.target.value)}
            >
              <option value="">All Qualities</option>
              {QUALITIES.filter(Boolean).map((q) => <option key={q} value={q}>{q}</option>)}
            </select>
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Filter By Skill
            </label>
            <select
              aria-label="Filter by skill"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-emerald-500 transition-colors"
              value={filterSkill}
              onChange={(e) => setFilterSkill(e.target.value)}
            >
              <option value="All">All Skills</option>
              {SKILLS.map(({ abbr, field }) => <option key={field} value={field}>{abbr} — {field}</option>)}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500">
              Min Rating
            </label>
            <input
              type="number"
              aria-label="Minimum skill rating"
              min="0"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-24 outline-none focus:border-emerald-500 transition-colors"
              value={filterMin}
              onChange={(e) => setFilterMin(Number(e.target.value))}
              disabled={filterSkill === "All"}
            />
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              {sortOrder === "asc" ? <ArrowUpWideNarrow size={10} /> : <ArrowDownWideNarrow size={10} />} Sort By
            </label>
            <div className="flex gap-2">
              <select
                aria-label="Sort field"
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
                  {SKILLS.map(({ abbr, field }) => <option key={field} value={`skill:${field}`}>{abbr} — {field}</option>)}
                </optgroup>
              </select>
              <button
                onClick={() => setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))}
                aria-label={`Sort ${sortOrder === "asc" ? "descending" : "ascending"}`}
                className="bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 hover:border-emerald-500/50 p-2 rounded-lg text-neutral-300 transition-all flex items-center justify-center"
              >
                {sortOrder === "asc"
                  ? <ArrowUpWideNarrow size={18} className="text-emerald-400" />
                  : <ArrowDownWideNarrow size={18} className="text-emerald-400" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
          <AlertCircle size={18} className="shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-xl shadow-black/50 relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-neutral-900/80 backdrop-blur-sm z-10 flex items-center justify-center flex-col gap-3">
            <Loader2 className="animate-spin text-emerald-500" size={40} />
            <p className="text-emerald-400 font-medium animate-pulse">Fetching Players...</p>
          </div>
        )}

        <div className="overflow-x-auto max-h-[600px] 2xl:max-h-[800px] border-t border-neutral-800 custom-scrollbar">
          <table className="w-full text-sm text-left border-collapse whitespace-nowrap" aria-label="Players table">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-950 sticky top-0 z-20 shadow-sm">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Name</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Pos</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Age</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Quality</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Potential</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Nationality</th>
                {SKILLS.map(({ abbr, field }) => (
                  <th key={field} scope="col" className="px-1 py-3 font-semibold border-b border-r border-neutral-800 text-center w-10">
                    <span title={field}>{abbr}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {players.map((player) => (
                <tr key={player.id} className="hover:bg-neutral-800/60 transition-colors even:bg-neutral-900/40">
                  <td className="px-4 py-3 font-medium text-white border-r border-neutral-800/60">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold shrink-0">
                        {player.name?.charAt(0) ?? "?"}
                      </div>
                      <div className="flex flex-col">
                        {player.url ? (
                          <a href={player.url} target="_blank" rel="noopener noreferrer" className="hover:text-emerald-400 hover:underline">
                            {player.name}
                          </a>
                        ) : player.name}
                        <span className="text-neutral-500 text-[10px] font-mono leading-tight mt-0.5">#{player.id}</span>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 border-r border-neutral-800/60">
                    <span className="px-2.5 py-1 rounded-md bg-neutral-800 text-neutral-300 text-xs font-medium border border-neutral-700/50">
                      {player.position}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-300 border-r border-neutral-800/60">{player.age}</td>
                  <td className={`px-4 py-3 font-medium border-r border-neutral-800/60 ${qualityColor(player.quality)}`}>
                    {player.quality}
                  </td>
                  <td className="px-4 py-3 text-cyan-400 font-medium border-r border-neutral-800/60">{player.potential}</td>
                  <td className="px-4 py-3 text-neutral-300 border-r border-neutral-800/60 bg-neutral-900/40">{player.nationality}</td>
                  {SKILLS.map(({ field }) => {
                    const raw = player.skills?.[field];
                    const value = raw != null ? Number(raw) : null;
                    const isHighlighted = filterSkill === field || sortField === `skill:${field}`;
                    if (value === null) {
                      return (
                        <td key={field} className={`px-1 py-1 text-center border-r border-neutral-800/60 ${isHighlighted ? "bg-emerald-500/5" : ""}`}>
                          <span className="text-neutral-700 text-[10px]">—</span>
                        </td>
                      );
                    }
                    return (
                      <td key={field} className={`px-1 py-1 border-r border-neutral-800/60 ${isHighlighted ? "ring-1 ring-inset ring-emerald-500/30" : ""}`}>
                        <SkillChip value={value} title={`${field}: ${value}`} />
                      </td>
                    );
                  })}
                </tr>
              ))}
              {!loading && !error && players.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center text-neutral-500">
                      <Filter size={32} className="mb-3 opacity-50" />
                      <p className="text-base font-medium text-neutral-400">No players found matching your criteria</p>
                      <p className="text-sm mt-1">Try lowering the minimum rating or changing the search/filter parameters.</p>
                      <button
                        onClick={() => { setFilterSkill("All"); setFilterMin(0); setSearch(""); setFilterPos(""); setFilterQuality(""); }}
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

        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-neutral-800 bg-neutral-950/30 flex items-center justify-between">
            <span className="text-sm text-neutral-400">
              Showing{" "}
              <span className="text-white font-medium">{(page - 1) * PAGE_SIZE + 1}</span> to{" "}
              <span className="text-white font-medium">{Math.min(page * PAGE_SIZE, totalCount)}</span> of{" "}
              <span className="text-white font-medium">{totalCount}</span> results
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                aria-label="Previous page"
                className="p-2 bg-neutral-900 border border-neutral-700 rounded-lg hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed text-neutral-300 transition-colors"
              >
                <ChevronLeft size={18} />
              </button>
              <div className="flex items-center justify-center px-4 bg-neutral-900 border border-neutral-700 rounded-lg text-sm font-medium text-white">
                Page {page} of {totalPages}
              </div>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                aria-label="Next page"
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
