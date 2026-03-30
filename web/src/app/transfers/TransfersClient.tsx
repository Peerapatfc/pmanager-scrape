"use client";

import { useState, useEffect } from "react";
import {
  ArrowRightLeft,
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
import { PAGE_SIZE, DEBOUNCE_MS, POSITIONS } from "@/lib/constants";
import { formatValue, roiColor } from "@/lib/utils";
import type { Transfer } from "@/types";

export default function TransfersClient() {
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [sortField, setSortField] = useState("forecast_profit");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [filterPos, setFilterPos] = useState("");

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
  }, [sortField, sortOrder, filterPos]);

  // Fetch transfers
  useEffect(() => {
    let isMounted = true;

    async function fetchTransfers() {
      setLoading(true);
      setError(null);

      try {
        let query = supabase.from("transfer_listings").select("*", { count: "exact" });

        if (debouncedSearch) {
          query = query.ilike("name", `%${debouncedSearch}%`);
        }
        if (filterPos) {
          query = query.eq("position", filterPos);
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
          setTransfers((data as Transfer[]) ?? []);
          setTotalCount(count ?? 0);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "Failed to load transfers.");
          setTransfers([]);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    fetchTransfers();
    return () => { isMounted = false; };
  }, [debouncedSearch, sortField, sortOrder, filterPos, page]);

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  return (
    <div className="space-y-6">
      <div className="flex flex-col xl:flex-row xl:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent flex items-center gap-3">
            <ArrowRightLeft size={32} className="text-cyan-400" />
            Transfer Listings
          </h1>
          <p className="text-neutral-400 mt-2">
            Showing {transfers.length} of {totalCount} transfers.
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-end gap-3 bg-neutral-900/40 p-3 rounded-xl border border-neutral-800 shadow-inner">
          <div className="flex flex-col gap-1 flex-1 min-w-[200px]">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Search size={10} /> Search Name
            </label>
            <input
              type="text"
              aria-label="Search transfers by player name"
              placeholder="e.g. Messi"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 w-full outline-none focus:border-cyan-500 transition-colors"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              <Filter size={10} /> Filter Position
            </label>
            <select
              aria-label="Filter by position"
              className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-cyan-500 transition-colors"
              value={filterPos}
              onChange={(e) => setFilterPos(e.target.value)}
            >
              <option value="">All Positions</option>
              {POSITIONS.filter(Boolean).map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="w-px h-8 bg-neutral-800 mx-1 self-center hidden sm:block" />

          <div className="flex flex-col gap-1">
            <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
              {sortOrder === "asc" ? <ArrowUpWideNarrow size={10} /> : <ArrowDownWideNarrow size={10} />} Sort By
            </label>
            <div className="flex gap-2">
              <select
                aria-label="Sort field"
                className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-cyan-500 transition-colors"
                value={sortField}
                onChange={(e) => setSortField(e.target.value)}
              >
                <option value="roi">ROI (%)</option>
                <option value="estimated_value">Estimated Value</option>
                <option value="asking_price">Asking Price</option>
                <option value="forecast_profit">Forecast Profit</option>
                <option value="quality">Quality</option>
                <option value="potential">Potential</option>
                <option value="age">Age</option>
                <option value="deadline">Deadline</option>
              </select>
              <button
                onClick={() => setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))}
                aria-label={`Sort ${sortOrder === "asc" ? "descending" : "ascending"}`}
                className="bg-neutral-900 border border-neutral-700 hover:bg-neutral-800 hover:border-cyan-500/50 p-2 rounded-lg text-neutral-300 transition-all flex items-center justify-center"
              >
                {sortOrder === "asc"
                  ? <ArrowUpWideNarrow size={18} className="text-cyan-400" />
                  : <ArrowDownWideNarrow size={18} className="text-cyan-400" />}
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
            <Loader2 className="animate-spin text-cyan-500" size={40} />
            <p className="text-cyan-400 font-medium animate-pulse">Fetching Transfers...</p>
          </div>
        )}

        <div className="overflow-x-auto max-h-[600px] 2xl:max-h-[800px] border-t border-neutral-800 custom-scrollbar">
          <table className="w-full text-sm text-left border-collapse whitespace-nowrap" aria-label="Transfer listings table">
            <thead className="text-xs text-neutral-400 uppercase bg-neutral-950 sticky top-0 z-20 shadow-sm">
              <tr>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Player</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Pos</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Quality</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Est. Value</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Asking Price</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">Forecast Profit</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-r border-neutral-800">ROI (%)</th>
                <th scope="col" className="px-4 py-3 font-semibold border-b border-neutral-800">Deadline</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60">
              {transfers.map((tx) => (
                <tr key={tx.id} className="hover:bg-neutral-800/60 transition-colors even:bg-neutral-900/40">
                  <td className="px-4 py-3 font-medium text-white border-r border-neutral-800/60">
                    <div className="flex flex-col gap-1">
                      {tx.url ? (
                        <a href={tx.url} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 hover:underline">
                          {tx.name}
                        </a>
                      ) : tx.name}
                      <span className="text-neutral-500 text-xs text-nowrap">
                        Age: {tx.age} | Pot: {tx.potential}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 border-r border-neutral-800/60">
                    <span className="px-2.5 py-1 rounded-md bg-neutral-800 text-neutral-300 text-xs font-medium border border-neutral-700/50">
                      {tx.position}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-emerald-400 font-medium border-r border-neutral-800/60">{tx.quality}</td>
                  <td className="px-4 py-3 text-neutral-300 font-medium border-r border-neutral-800/60">
                    ${formatValue(tx.estimated_value)}
                  </td>
                  <td className="px-4 py-3 font-medium text-neutral-100 border-r border-neutral-800/60">
                    ${formatValue(tx.asking_price)}
                  </td>
                  <td className="px-4 py-3 font-medium text-emerald-400 border-r border-neutral-800/60">
                    {tx.forecast_profit > 0 ? "+" : ""}${formatValue(tx.forecast_profit)}
                  </td>
                  <td className="px-4 py-3 border-r border-neutral-800/60">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-bold ${roiColor(tx.roi ?? 0)}`}>
                      {tx.roi}%
                    </span>
                  </td>
                  <td className="px-4 py-3 text-neutral-400">
                    {tx.deadline
                      ? new Date(tx.deadline).toLocaleString("en-GB", {
                          timeZone: "Asia/Bangkok",
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })
                      : "-"}
                  </td>
                </tr>
              ))}
              {!loading && !error && transfers.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center justify-center text-neutral-500">
                      <Filter size={32} className="mb-3 opacity-50" />
                      <p className="text-base font-medium text-neutral-400">No transfers found matching your criteria</p>
                      <button
                        onClick={() => { setFilterPos(""); setSearch(""); }}
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
