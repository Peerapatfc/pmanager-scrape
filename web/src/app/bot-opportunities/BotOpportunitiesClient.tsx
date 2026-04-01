"use client";

import { useState, useEffect } from "react";
import {
  Bot,
  ExternalLink,
  Filter,
  ArrowDownWideNarrow,
  ArrowUpWideNarrow,
  Search,
  ChevronLeft,
  ChevronRight,
  Loader2,
  ArrowUpRight,
  AlertCircle,
} from "lucide-react";

import { supabase } from "@/lib/supabase";
import { PAGE_SIZE, DEBOUNCE_MS, POSITIONS, QUALITIES } from "@/lib/constants";
import { formatValue, qualityColor, marginColor } from "@/lib/utils";
import type { BotOpportunity } from "@/types";

export default function BotOpportunitiesClient() {
  const [rows, setRows] = useState<BotOpportunity[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [filterQuality, setFilterQuality] = useState("");
  const [filterPos, setFilterPos] = useState("");
  const [filterPlusOnly, setFilterPlusOnly] = useState(true);
  const [sortField, setSortField] = useState("profit_margin");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

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
  }, [filterQuality, filterPos, filterPlusOnly, sortField, sortOrder]);

  // Fetch
  useEffect(() => {
    let isMounted = true;

    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        let query = supabase.from("bot_opportunities").select("*", { count: "exact" });

        if (debouncedSearch) {
          query = query.ilike("name", `%${debouncedSearch}%`);
        }
        if (filterQuality) {
          query = query.eq("quality", filterQuality);
        }
        if (filterPos) {
          query = query.eq("position", filterPos);
        }
        if (filterPlusOnly) {
          query = query.gt("value_diff", 0);
        }

        query = query.order(sortField, { ascending: sortOrder === "asc", nullsFirst: false });
        if (sortField !== "id") {
          query = query.order("id", { ascending: true });
        }

        const from = (page - 1) * PAGE_SIZE;
        query = query.range(from, from + PAGE_SIZE - 1);

        const { data, count, error: supabaseError } = await query;
        if (supabaseError) throw supabaseError;

        if (isMounted) {
          setRows((data as BotOpportunity[]) ?? []);
          setTotalCount(count ?? 0);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load bot opportunities.");
          setRows([]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchData();
    return () => { isMounted = false; };
  }, [debouncedSearch, filterQuality, filterPos, filterPlusOnly, sortField, sortOrder, page]);

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  const clearFilters = () => { setSearch(""); setFilterQuality(""); setFilterPos(""); setFilterPlusOnly(false); };

  // Margin badge — needs border colour in addition to text/bg
  const marginBadgeClass = (m: number): string => {
    const base = marginColor(m);
    if (base.includes("emerald")) return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    if (base.includes("yellow")) return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    return "bg-neutral-800 text-neutral-400 border-neutral-700";
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
          <div className="flex flex-col gap-1 flex-1 min-w-[180px]">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Search size={10} /> Search Name
            </label>
            <input
              type="text"
              aria-label="Search bot opportunities by player name"
              placeholder="e.g. Messi"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-full outline-none focus:border-purple-500 transition-colors"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Quality
            </label>
            <select
              aria-label="Filter by quality"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-purple-500 transition-colors"
              value={filterQuality}
              onChange={(e) => setFilterQuality(e.target.value)}
            >
              <option value="">All Qualities</option>
              {QUALITIES.filter(Boolean).map((q) => <option key={q} value={q}>{q}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Position
            </label>
            <select
              aria-label="Filter by position"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-purple-500 transition-colors"
              value={filterPos}
              onChange={(e) => setFilterPos(e.target.value)}
            >
              <option value="">All Positions</option>
              {POSITIONS.filter(Boolean).map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="flex flex-col gap-1 justify-end">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Value Diff
            </label>
            <button
              onClick={() => setFilterPlusOnly((prev) => !prev)}
              aria-pressed={filterPlusOnly}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all ${
                filterPlusOnly
                  ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400"
                  : "bg-neutral-950 border-neutral-700 text-neutral-400 hover:border-neutral-600"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${filterPlusOnly ? "bg-emerald-400" : "bg-neutral-600"}`} />
              Positive Only
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
                onClick={() => setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))}
                aria-label={`Sort ${sortOrder === "asc" ? "descending" : "ascending"}`}
                className="bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 hover:border-purple-500/50 p-2 rounded-lg text-neutral-300 transition-all flex items-center justify-center"
              >
                {sortOrder === "asc"
                  ? <ArrowUpWideNarrow size={18} className="text-purple-400" />
                  : <ArrowDownWideNarrow size={18} className="text-purple-400" />}
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
          <div className="absolute inset-0 bg-neutral-900/80 backdrop-blur-sm z-30 flex items-center justify-center flex-col gap-3">
            <Loader2 className="animate-spin text-purple-500" size={40} />
            <p className="text-purple-400 font-medium animate-pulse">Fetching Opportunities...</p>
          </div>
        )}

        <div className="overflow-x-auto max-h-[600px] 2xl:max-h-[800px] border-t border-neutral-800 custom-scrollbar">
          <table className="w-full text-sm text-left border-collapse whitespace-nowrap" aria-label="Bot opportunities table">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-950 sticky top-0 z-20 shadow-sm">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Player</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Pos</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Quality</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">BOT Team</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Asking Price</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Est. Value</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Value Diff</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800 text-right">Margin</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-neutral-800 text-center">Link</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {rows.map((opp) => {
                const vd = opp.value_diff ?? 0;
                const tier = vd >= 10_000_000 ? "superb" : vd >= 5_000_000 ? "great" : vd >= 3_000_000 ? "good" : "normal";
                return (
                <tr
                  key={opp.id}
                  className={`transition-colors ${
                    tier === "superb"
                      ? "bg-purple-950/50 hover:bg-purple-900/40 border-l-2 border-l-purple-400/70"
                      : tier === "great"
                      ? "bg-emerald-950/40 hover:bg-emerald-900/30 border-l-2 border-l-emerald-500/60"
                      : tier === "good"
                      ? "bg-yellow-950/30 hover:bg-yellow-900/20 border-l-2 border-l-yellow-500/50"
                      : "hover:bg-neutral-800/60 even:bg-neutral-900/40"
                  }`}
                >
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
                    ${formatValue(opp.asking_price)}
                  </td>
                  <td className="px-4 py-3 text-right text-neutral-400 border-r border-neutral-800/60">
                    ${formatValue(opp.estimated_value)}
                  </td>
                  <td className="px-4 py-3 text-right border-r border-neutral-800/60">
                    <span className="text-emerald-400 font-medium flex items-center justify-end gap-0.5">
                      <ArrowUpRight size={13} />
                      ${formatValue(opp.value_diff)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right border-r border-neutral-800/60">
                    <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold border ${marginBadgeClass(opp.profit_margin)}`}>
                      {opp.profit_margin}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {opp.url ? (
                      <a
                        href={opp.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={`View ${opp.name ?? opp.id} on PManager`}
                        className="inline-flex items-center justify-center p-2 rounded-lg bg-neutral-800 text-neutral-300 hover:bg-purple-500/20 hover:text-purple-400 hover:border-purple-500/50 border border-transparent transition-all"
                      >
                        <ExternalLink size={15} />
                      </a>
                    ) : (
                      <span className="text-neutral-600">—</span>
                    )}
                  </td>
                </tr>
                );
              })}
              {!loading && !error && rows.length === 0 && (
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
