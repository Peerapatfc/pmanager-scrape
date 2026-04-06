"use client";

import { Fragment, useState, useEffect } from "react";
import {
  Swords,
  ExternalLink,
  Filter,
  ArrowDownWideNarrow,
  ArrowUpWideNarrow,
  Search,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  Play,
  CheckCircle2,
} from "lucide-react";

import { supabase } from "@/lib/supabase";
import { PAGE_SIZE, DEBOUNCE_MS, POSITIONS } from "@/lib/constants";
import { formatDeadline, qualityColor } from "@/lib/utils";
import type { OpponentScoutResult, Player } from "@/types";

export default function OpponentScoutClient() {
  const [rows, setRows] = useState<OpponentScoutResult[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playerDbMap, setPlayerDbMap] = useState<Map<string, Player>>(new Map());
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [filterPos, setFilterPos] = useState("");
  const [filterMatchOnly, setFilterMatchOnly] = useState(false);
  const [sortField, setSortField] = useState("scouted_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Trigger form
  const [teamTarget, setTeamTarget] = useState("");
  const [triggering, setTriggering] = useState(false);
  const [triggerStatus, setTriggerStatus] = useState<{ ok: boolean; message: string } | null>(null);

  // Debounce search
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, DEBOUNCE_MS);
    return () => clearTimeout(handler);
  }, [search]);

  // Reset page on filter/sort change
  useEffect(() => {
    setPage(1);
  }, [filterPos, filterMatchOnly, sortField, sortOrder]);

  // Fetch
  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      setLoading(true);
      setError(null);
      setPlayerDbMap(new Map());
      setExpandedIds(new Set());

      try {
        let query = supabase
          .from("opponent_scout_results")
          .select("*", { count: "exact" });

        if (debouncedSearch) {
          query = query.or(
            `player_name.ilike.%${debouncedSearch}%,team_id.ilike.%${debouncedSearch}%`
          );
        }
        if (filterPos) query = query.eq("position", filterPos);
        if (filterMatchOnly) query = query.eq("is_watchlist_match", true);

        query = query.order(sortField, { ascending: sortOrder === "asc", nullsFirst: false });
        if (sortField !== "player_id") {
          query = query.order("player_id", { ascending: true });
        }

        const from = (page - 1) * PAGE_SIZE;
        query = query.range(from, from + PAGE_SIZE - 1);

        const { data, count, error: supabaseError } = await query;
        if (supabaseError) throw supabaseError;

        if (isMounted) {
          const results = (data as OpponentScoutResult[]) ?? [];
          setRows(results);
          setTotalCount(count ?? 0);

          if (results.length > 0) {
            const ids = results.map((r) => r.player_id);
            const { data: dbMatches } = await supabase
              .from("players")
              .select("*")
              .in("id", ids);
            if (isMounted) {
              const map = new Map<string, Player>();
              (dbMatches ?? []).forEach((p: Player) => map.set(p.id, p));
              setPlayerDbMap(map);
            }
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load scout results.");
          setRows([]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchData();
    return () => { isMounted = false; };
  }, [debouncedSearch, filterPos, filterMatchOnly, sortField, sortOrder, page]);

  function toggleExpand(playerId: string) {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(playerId)) next.delete(playerId);
      else next.add(playerId);
      return next;
    });
  }

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);
  const clearFilters = () => { setSearch(""); setFilterPos(""); setFilterMatchOnly(false); };

  async function handleTrigger(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!teamTarget.trim()) return;
    setTriggering(true);
    setTriggerStatus(null);
    try {
      const res = await fetch("/api/scout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_target: teamTarget.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setTriggerStatus({ ok: true, message: `Scout job dispatched for "${teamTarget.trim()}". Results will appear here once the GitHub Actions run completes (~2 min).` });
        setTeamTarget("");
      } else {
        setTriggerStatus({ ok: false, message: data.error ?? "Failed to trigger scout." });
      }
    } catch {
      setTriggerStatus({ ok: false, message: "Network error — could not reach the API." });
    } finally {
      setTriggering(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-orange-400 to-red-400 bg-clip-text text-transparent flex items-center gap-3">
            <Swords size={32} className="text-orange-400" />
            Opponent Scout
          </h1>
          <p className="text-neutral-400 mt-2">
            Showing {rows.length} of {totalCount} players. Players in your database are highlighted as matches.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-end gap-3 bg-neutral-900/40 p-3 rounded-xl border border-neutral-800 shadow-inner">
          <div className="flex flex-col gap-1 flex-1 min-w-[180px]">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Search size={10} /> Search Player / Team ID
            </label>
            <input
              type="text"
              aria-label="Search by player name or team ID"
              placeholder="e.g. Messi or 12345"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-full outline-none focus:border-orange-500 transition-colors"
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
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-orange-500 transition-colors"
              value={filterPos}
              onChange={(e) => setFilterPos(e.target.value)}
            >
              <option value="">All Positions</option>
              {POSITIONS.filter(Boolean).map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1 justify-end">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500">
              Watchlist
            </label>
            <button
              onClick={() => setFilterMatchOnly((v) => !v)}
              aria-pressed={filterMatchOnly}
              className={`px-3 py-2 rounded-lg text-sm font-semibold border transition-all ${
                filterMatchOnly
                  ? "bg-orange-500/20 border-orange-500/60 text-orange-400"
                  : "bg-neutral-950 border-neutral-700 text-neutral-400 hover:border-orange-500/40"
              }`}
            >
              {filterMatchOnly ? "Matches Only" : "All Players"}
            </button>
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              {sortOrder === "asc" ? <ArrowUpWideNarrow size={10} /> : <ArrowDownWideNarrow size={10} />} Sort By
            </label>
            <div className="flex gap-2">
              <select
                aria-label="Sort field"
                className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-orange-500 transition-colors"
                value={sortField}
                onChange={(e) => setSortField(e.target.value)}
              >
                <option value="scouted_at">Scouted At</option>
                <option value="player_name">Player Name</option>
                <option value="position">Position</option>
                <option value="team_id">Team ID</option>
              </select>
              <button
                onClick={() => setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))}
                aria-label={`Sort ${sortOrder === "asc" ? "descending" : "ascending"}`}
                className="bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 hover:border-orange-500/50 p-2 rounded-lg text-neutral-300 transition-all flex items-center justify-center"
              >
                {sortOrder === "asc"
                  ? <ArrowUpWideNarrow size={18} className="text-orange-400" />
                  : <ArrowDownWideNarrow size={18} className="text-orange-400" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Trigger form */}
      <form
        onSubmit={handleTrigger}
        className="flex flex-col sm:flex-row gap-3 items-start sm:items-end bg-neutral-900/40 border border-neutral-800 rounded-xl p-4"
      >
        <div className="flex flex-col gap-1 flex-1 min-w-[220px]">
          <label htmlFor="scout-target" className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
            <Swords size={10} /> Run Scout — Team ID or URL
          </label>
          <input
            id="scout-target"
            type="text"
            placeholder="e.g. 12345 or https://pmanager.org/ver_equipa.asp?equipa=12345"
            className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-orange-500 transition-colors w-full"
            value={teamTarget}
            onChange={(e) => setTeamTarget(e.target.value)}
            disabled={triggering}
          />
        </div>
        <button
          type="submit"
          disabled={triggering || !teamTarget.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm rounded-lg transition-colors shrink-0"
        >
          {triggering
            ? <><Loader2 size={15} className="animate-spin" /> Dispatching...</>
            : <><Play size={15} /> Run Scout</>}
        </button>
      </form>

      {/* Trigger status */}
      {triggerStatus && (
        <div className={`flex items-start gap-3 p-4 rounded-xl border text-sm ${
          triggerStatus.ok
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            : "bg-red-500/10 border-red-500/30 text-red-400"
        }`}>
          {triggerStatus.ok
            ? <CheckCircle2 size={18} className="shrink-0 mt-0.5" />
            : <AlertCircle size={18} className="shrink-0 mt-0.5" />}
          <p>{triggerStatus.message}</p>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
          <AlertCircle size={18} className="shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden shadow-xl shadow-black/50 relative min-h-[400px]">
        {loading && (
          <div className="absolute inset-0 bg-neutral-900/80 backdrop-blur-sm z-30 flex items-center justify-center flex-col gap-3">
            <Loader2 className="animate-spin text-orange-500" size={40} />
            <p className="text-orange-400 font-medium animate-pulse">Loading Scout Results...</p>
          </div>
        )}

        <div className="overflow-x-auto max-h-[600px] 2xl:max-h-[800px] border-t border-neutral-800 custom-scrollbar">
          <table className="w-full text-sm text-left border-collapse whitespace-nowrap" aria-label="Opponent scout results table">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-950 sticky top-0 z-20 shadow-sm">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Player</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Pos</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Team ID</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-center">Match</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-center">In DB</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Scouted At</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-neutral-800 text-center">Profile</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {rows.map((r) => {
                const dbPlayer = playerDbMap.get(r.player_id);
                const isExpanded = expandedIds.has(r.player_id);
                return (
                  <Fragment key={`${r.team_id}-${r.player_id}`}>
                    <tr className="hover:bg-neutral-800/60 transition-colors even:bg-neutral-900/40">
                      <td className="px-4 py-3 font-medium text-white border-r border-neutral-800/60">
                        <div className="font-semibold">{r.player_name ?? (dbPlayer?.name ?? "—")}</div>
                        <div className="text-xs text-neutral-500">ID: {r.player_id}</div>
                      </td>
                      <td className="px-4 py-3 border-r border-neutral-800/60">
                        <span className="px-2.5 py-1 rounded-md bg-neutral-800 text-neutral-300 text-xs font-medium border border-neutral-700/50">
                          {r.position ?? (dbPlayer?.position ?? "—")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-neutral-300 border-r border-neutral-800/60">
                        <span className="flex items-center gap-1.5">
                          <Swords size={13} className="text-neutral-500 shrink-0" />
                          {r.team_id}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center border-r border-neutral-800/60">
                        {r.is_watchlist_match
                          ? <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold bg-orange-500/20 text-orange-400 border border-orange-500/40">Match</span>
                          : <span className="text-neutral-600 text-xs">—</span>}
                      </td>
                      <td className="px-4 py-3 text-center border-r border-neutral-800/60">
                        {dbPlayer ? (
                          <button
                            onClick={() => toggleExpand(r.player_id)}
                            aria-expanded={isExpanded}
                            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30 transition-colors cursor-pointer"
                          >
                            In DB
                            {isExpanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                          </button>
                        ) : (
                          <span className="text-neutral-600 text-xs">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-neutral-400 border-r border-neutral-800/60">
                        {formatDeadline(r.scouted_at)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {r.player_link ? (
                          <a
                            href={r.player_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            aria-label={`View ${r.player_name ?? r.player_id} on PManager`}
                            className="inline-flex items-center justify-center p-2 rounded-lg bg-neutral-800 text-neutral-300 hover:bg-orange-500/20 hover:text-orange-400 hover:border-orange-500/50 border border-transparent transition-all"
                          >
                            <ExternalLink size={15} />
                          </a>
                        ) : (
                          <span className="text-neutral-600">—</span>
                        )}
                      </td>
                    </tr>

                    {/* Expanded player detail row */}
                    {isExpanded && dbPlayer && (
                      <tr className="bg-emerald-950/20 border-b border-emerald-800/30">
                        <td colSpan={7} className="px-6 py-4">
                          <div className="flex flex-wrap gap-4 items-start">
                            {/* Basic info */}
                            <div className="flex flex-col gap-1.5 min-w-[160px]">
                              <span className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500">Player Info</span>
                              <div className="font-semibold text-white text-sm">{dbPlayer.name}</div>
                              <div className="flex flex-wrap gap-1.5 mt-0.5">
                                <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 text-xs border border-neutral-700/50">
                                  {dbPlayer.position}
                                </span>
                                <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 text-xs border border-neutral-700/50">
                                  Age {dbPlayer.age}
                                </span>
                                {dbPlayer.nationality && (
                                  <span className="px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 text-xs border border-neutral-700/50">
                                    {dbPlayer.nationality}
                                  </span>
                                )}
                              </div>
                              <div className="flex flex-wrap gap-1.5 mt-0.5">
                                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${qualityColor(dbPlayer.quality)}`}>
                                  {dbPlayer.quality}
                                </span>
                                <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 text-xs font-semibold border border-cyan-500/20">
                                  {dbPlayer.potential}
                                </span>
                              </div>
                            </div>

                            <div className="w-px self-stretch bg-neutral-700/50 hidden sm:block" />

                            {/* Skills grid */}
                            {dbPlayer.skills && Object.keys(dbPlayer.skills).length > 0 && (
                              <div className="flex flex-col gap-1.5 flex-1 min-w-[240px]">
                                <span className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500">Skills</span>
                                <div className="flex flex-wrap gap-1.5">
                                  {Object.entries(dbPlayer.skills)
                                    .sort(([, a], [, b]) => b - a)
                                    .map(([skill, value]) => (
                                      <span
                                        key={skill}
                                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-neutral-800 border border-neutral-700/50 text-xs"
                                      >
                                        <span className="text-neutral-400">{skill}</span>
                                        <span className="font-bold text-emerald-400">{value}</span>
                                      </span>
                                    ))}
                                </div>
                              </div>
                            )}

                            {/* Profile link */}
                            {dbPlayer.url && (
                              <div className="flex flex-col gap-1.5 justify-end self-end">
                                <a
                                  href={dbPlayer.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20 transition-colors text-xs font-semibold"
                                >
                                  <ExternalLink size={12} /> View Profile
                                </a>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
              {!loading && !error && rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center text-neutral-500">
                      <Swords size={32} className="mb-3 opacity-50" />
                      <p className="text-base font-medium text-neutral-400">No scout results found</p>
                      <p className="text-sm text-neutral-500 mt-1">
                        Run <code className="bg-neutral-800 px-1.5 py-0.5 rounded text-orange-400">python main_opponent_scout.py &lt;team_id&gt;</code> to populate data.
                      </p>
                      {(search || filterPos) && (
                        <button
                          onClick={clearFilters}
                          className="mt-4 px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-white rounded-lg text-sm transition-colors border border-neutral-700 cursor-pointer"
                        >
                          Clear Filters
                        </button>
                      )}
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
