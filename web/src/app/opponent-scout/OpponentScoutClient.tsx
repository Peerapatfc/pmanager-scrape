"use client";

import { Fragment, useState, useEffect, useMemo } from "react";
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
  Users,
} from "lucide-react";

import { supabase } from "@/lib/supabase";
import { PAGE_SIZE, DEBOUNCE_MS, POSITIONS } from "@/lib/constants";
import { formatDeadline, qualityColor } from "@/lib/utils";
import type { OpponentScoutResult, Player } from "@/types";

// ── AT Matchup types & helpers ────────────────────────────────────────────────
interface MySquadPlayer { id: string; position: string; skills: Record<string, number> }

function posG(pos: string | null | undefined): "GK" | "D" | "M" | "F" {
  const p = (pos ?? "").trim().toUpperCase();
  if (p.startsWith("GK")) return "GK";
  if (p.startsWith("D")) return "D";
  if (p.startsWith("M")) return "M";
  return "F";
}

function avgSk<T extends { skills: Record<string, number> }>(players: T[], field: string): number {
  if (!players.length) return 0;
  return players.reduce((s, p) => s + (p.skills?.[field] ?? 0), 0) / players.length;
}

interface ATMatchup {
  label: string;
  mine: number | null;
  theirs: number | null;
  /** true=win, false=lose, null=N/A */
  result: boolean | null;
  partial?: boolean;
}

function computeATMatchup(my: MySquadPlayer[], opp: Player[]): ATMatchup[] {
  type P = { skills: Record<string, number> };
  const myAll = my as unknown as P[];
  const oppAll = opp as unknown as P[];
  const myGK  = my.filter(p => posG(p.position) === "GK") as unknown as P[];
  const myD   = my.filter(p => posG(p.position) === "D")  as unknown as P[];
  const myMF  = my.filter(p => ["M","F"].includes(posG(p.position))) as unknown as P[];
  const myDM  = my.filter(p => ["D","M"].includes(posG(p.position))) as unknown as P[];
  const myF   = my.filter(p => posG(p.position) === "F")  as unknown as P[];
  const oppGK = opp.filter(p => posG(p.position) === "GK") as unknown as P[];
  const oppD  = opp.filter(p => posG(p.position) === "D")  as unknown as P[];
  const oppMF = opp.filter(p => ["M","F"].includes(posG(p.position))) as unknown as P[];
  const oppDM = opp.filter(p => ["D","M"].includes(posG(p.position))) as unknown as P[];
  const oppF  = opp.filter(p => posG(p.position) === "F")  as unknown as P[];

  const a = (arr: P[], f: string) => avgSk(arr as unknown as MySquadPlayer[], f);

  function multi(conditions: { mine: number; theirs: number; lowerIsBetter?: boolean }[]): ATMatchup["result"] | { partial: boolean; result: boolean } {
    const wins = conditions.filter(c => c.lowerIsBetter ? c.mine < c.theirs : c.mine > c.theirs).length;
    if (wins === conditions.length) return true;
    if (wins === 0) return false;
    return { partial: true, result: false };
  }

  function row(label: string, conditions: { mine: number; theirs: number; lowerIsBetter?: boolean }[]): ATMatchup {
    const res = multi(conditions);
    const mine = conditions[0].mine;
    const theirs = conditions[0].theirs;
    if (typeof res === "object") return { label, mine, theirs, result: false, partial: true };
    return { label, mine, theirs, result: res };
  }

  function single(label: string, mine: number | null, theirs: number | null): ATMatchup {
    if (mine === null || theirs === null) return { label, mine, theirs, result: null };
    return { label, mine, theirs, result: mine > theirs };
  }

  const results: ATMatchup[] = [
    row("Pressing – High", [
      { mine: a(myAll, "Speed"),   theirs: a(oppAll, "Speed") },
      { mine: a(myAll, "Passing"), theirs: a(oppAll, "Passing") },
    ]),
    row("Pressing – Low", [
      { mine: a(myAll, "Speed"),    theirs: a(oppAll, "Speed"),    lowerIsBetter: true },
      { mine: a(myAll, "Tackling"), theirs: a(oppAll, "Tackling") },
    ]),
    row("Counter Attack", [
      { mine: a(myAll, "Speed"),   theirs: a(oppAll, "Speed") },
      { mine: a(myAll, "Passing"), theirs: a(oppAll, "Passing") },
    ]),
    row("Offside Trap", [
      { mine: a(myD, "Positioning"), theirs: a(oppF, "Positioning") },
      { mine: a(myD, "Speed"),       theirs: a(oppF, "Speed") },
    ]),
    row("High Balls", [
      { mine: a(myAll, "Heading"),  theirs: a(oppAll, "Heading") },
      { mine: a(myAll, "Strength"), theirs: a(oppAll, "Strength") },
    ]),
    single("One on Ones",
      myMF.length  ? (a(myMF,  "Technique") + a(myMF,  "Strength")) / 2 : null,
      oppDM.length ? (a(oppDM, "Tackling")  + a(oppDM, "Strength")) / 2 : null,
    ),
    single("Keeping – Stand In",
      myGK.length ? (a(myGK, "Reflexes") + a(myGK, "Handling"))   / 2 : null,
      oppF.length  ? (a(oppF,  "Heading")  + a(oppF,  "Finishing")) / 2 : null,
    ),
    single("Keeping – Rush Out",
      myGK.length ? (a(myGK, "Agility") + a(myGK, "Out of Area")) / 2 : null,
      oppF.length  ? (a(oppF,  "Heading") + a(oppF,  "Technique"))  / 2 : null,
    ),
    single("Marking – Zonal",
      myDM.length  ? (a(myDM,  "Speed")    + a(myDM,  "Tackling"))    / 2 : null,
      oppMF.length ? (a(oppMF, "Positioning") + a(oppMF, "Speed"))     / 2 : null,
    ),
    single("Marking – Man to Man",
      myDM.length  ? (a(myDM,  "Strength") + a(myDM,  "Tackling"))    / 2 : null,
      oppMF.length ? (a(oppMF, "Positioning") + a(oppMF, "Strength"))  / 2 : null,
    ),
    single("Long Shots",
      myMF.length                    ? (a(myMF,  "Finishing") + a(myMF,  "Technique"))  / 2 : null,
      oppGK.length && oppD.length    ? (a(oppGK, "Agility")   + a(oppD,  "Positioning")) / 2 : null,
    ),
    (() => {
      if (myF.length < 3) return { label: "First Time Shots", mine: null, theirs: null, result: null };
      return single("First Time Shots",
        (a(myF,  "Finishing") + a(myF,  "Heading"))  / 2,
        oppGK.length && oppD.length ? (a(oppGK, "Reflexes") + a(oppD, "Heading")) / 2 : null,
      );
    })(),
  ];
  return results;
}

function ATMatchupPanel({ my, opp, teamName }: { my: MySquadPlayer[]; opp: Player[]; teamName: string }) {
  const matchups = useMemo(() => computeATMatchup(my, opp), [my, opp]);
  const hasData = opp.some(p => Object.keys(p.skills ?? {}).length > 0);

  return (
    <div className="mt-3 border border-neutral-700/50 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 bg-neutral-800/60 border-b border-neutral-700/50">
        <Swords size={12} className="text-orange-400" />
        <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
          AT Matchup vs {teamName}
        </span>
        {my.length < 11 && (
          <span className="ml-auto text-[9px] text-yellow-500/80 italic">Select starting 11 on Squad page for best accuracy</span>
        )}
        {!hasData && (
          <span className="ml-auto text-[9px] text-red-500/80 italic">Opponent skill data sparse — results may be inaccurate</span>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-px bg-neutral-700/30 text-xs">
        {matchups.map(({ label, mine, theirs, result, partial }) => (
          <div key={label} className="flex items-center gap-2 px-4 py-2 bg-neutral-900">
            <span className="text-neutral-400 w-36 shrink-0 text-[11px]">{label}</span>
            {result === null ? (
              <span className="text-neutral-600 italic text-[10px]">N/A</span>
            ) : (
              <>
                <span className="font-mono text-[11px] text-neutral-300 w-8 text-right shrink-0">
                  {mine !== null ? mine.toFixed(1) : "—"}
                </span>
                <span className="text-neutral-600 text-[10px] shrink-0">vs</span>
                <span className="font-mono text-[11px] text-neutral-500 w-8 shrink-0">
                  {theirs !== null ? theirs.toFixed(1) : "—"}
                </span>
                <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded border shrink-0 ${
                  partial
                    ? "text-yellow-400 bg-yellow-500/10 border-yellow-500/25"
                    : result
                    ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/25"
                    : "text-red-400 bg-red-500/10 border-red-500/25"
                }`}>
                  {partial ? "~ Partial" : result ? "✓ Win" : "✗ Lose"}
                </span>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

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

  // My squad (for AT matchup)
  const [mySquad, setMySquad] = useState<MySquadPlayer[]>([]);
  const [atExpanded, setAtExpanded] = useState<Set<string>>(new Set());

  // Trigger form
  const [teamTarget, setTeamTarget] = useState("");
  const [triggering, setTriggering] = useState(false);
  const [triggerStatus, setTriggerStatus] = useState<{ ok: boolean; message: string } | null>(null);

  // Fetch my squad for AT matchup
  useEffect(() => {
    async function fetchMySquad() {
      const { data: squadData } = await supabase
        .from("my_squad")
        .select("player_id, position");
      if (!squadData?.length) return;
      const ids = squadData.map((r: { player_id: string }) => r.player_id);
      const { data: playersData } = await supabase
        .from("players")
        .select("id, skills")
        .in("id", ids);
      const map = new Map((playersData ?? []).map((p: { id: string; skills: Record<string, number> }) => [p.id, p.skills]));
      setMySquad(squadData.map((r: { player_id: string; position: string }) => ({
        id: r.player_id,
        position: r.position,
        skills: (map.get(r.player_id) as Record<string, number>) ?? {},
      })));
    }
    fetchMySquad();
  }, []);

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

  // Group rows by team_id, preserving order
  const groupedRows = useMemo(() => {
    const map = new Map<string, OpponentScoutResult[]>();
    rows.forEach((r) => {
      const group = map.get(r.team_id) ?? [];
      group.push(r);
      map.set(r.team_id, group);
    });
    return map;
  }, [rows]);

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

  // Column count for colSpan: Player, Pos, Match, In DB, Profile = 5
  const COL_COUNT = 5;

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-orange-400 to-red-400 bg-clip-text text-transparent flex items-center gap-3">
            <Swords size={32} className="text-orange-400" />
            Opponent Scout
          </h1>
          <p className="text-neutral-400 mt-2">
            {playerDbMap.size > 0
              ? <>{playerDbMap.size} of {totalCount} scouted players are in your database.</>
              : <>Scouted {totalCount} players across {groupedRows.size} team{groupedRows.size !== 1 ? "s" : ""}.</>}
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
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-center">Match</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-center">In DB</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-neutral-800 text-center">Profile</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {rows.length > 0 && Array.from(groupedRows.entries()).map(([teamId, teamRows]) => {
                const teamName = teamRows[0].team_name;
                const scoutedAt = teamRows[0].scouted_at;
                const dbRows = teamRows.filter((r) => playerDbMap.has(r.player_id));

                // Skip teams with no players in DB
                if (dbRows.length === 0) return null;

                return (
                  <Fragment key={teamId}>
                    {/* Team group header */}
                    <tr className="bg-neutral-950/60 border-y border-orange-900/30">
                      <td colSpan={COL_COUNT} className="px-4 py-2.5">
                        <div className="flex flex-wrap items-center gap-3">
                          <div className="flex items-center gap-2">
                            <Swords size={14} className="text-orange-400 shrink-0" />
                            <span className="font-bold text-orange-300 text-sm">
                              {teamName ?? `Team ${teamId}`}
                            </span>
                            {teamName && (
                              <span className="text-neutral-600 text-xs font-mono">#{teamId}</span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-neutral-500">
                            <Users size={11} />
                            <span>{dbRows.length} of {teamRows.length} players in your DB</span>
                          </div>
                          <span className="text-neutral-600 text-xs ml-auto">
                            Scouted {formatDeadline(scoutedAt)}
                          </span>
                          <button
                            onClick={() => setAtExpanded(prev => {
                              const next = new Set(prev);
                              next.has(teamId) ? next.delete(teamId) : next.add(teamId);
                              return next;
                            })}
                            className={`flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded border transition-colors ${
                              atExpanded.has(teamId)
                                ? "bg-orange-500/20 border-orange-500/40 text-orange-400"
                                : "bg-neutral-800 border-neutral-700 text-neutral-500 hover:border-orange-500/40 hover:text-orange-400"
                            }`}
                          >
                            <Swords size={10} /> AT
                          </button>
                        </div>
                      </td>
                    </tr>

                    {/* Player rows — only those in DB */}
                    {dbRows.map((r) => {
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

                          {/* Expanded player detail */}
                          {isExpanded && dbPlayer && (
                            <tr className="bg-emerald-950/20 border-b border-emerald-800/30">
                              <td colSpan={COL_COUNT} className="px-6 py-4">
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

                                  {/* Skills */}
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

                    {/* AT Matchup panel */}
                    {atExpanded.has(teamId) && (
                      <tr className="bg-neutral-950/40">
                        <td colSpan={COL_COUNT} className="px-4 pb-4">
                          <ATMatchupPanel
                            my={mySquad}
                            opp={dbRows.map(r => playerDbMap.get(r.player_id)).filter((p): p is Player => p !== undefined)}
                            teamName={teamName ?? `Team ${teamId}`}
                          />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}

              {!loading && !error && rows.length === 0 && (
                <tr>
                  <td colSpan={COL_COUNT} className="px-6 py-12 text-center">
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
