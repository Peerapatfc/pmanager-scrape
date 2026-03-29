"use client";

/**
 * Generic paginated data-fetch hook for Supabase tables.
 *
 * Encapsulates the search-debounce + sort + pagination pattern that was
 * previously duplicated across PlayersClient, TransfersClient, and
 * BotOpportunitiesClient.
 *
 * @example
 * ```tsx
 * const { rows, total, loading, error, page, setPage } =
 *   usePaginatedFetch<Transfer>(
 *     "transfer_listings",
 *     "*",
 *     (q) => q.gte("roi", 0).order("roi", { ascending: false }),
 *     [sortField, sortDir]
 *   );
 * ```
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { supabase } from "@/lib/supabase";
import { PAGE_SIZE } from "@/lib/constants";

type QueryBuilder = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  query: any
// eslint-disable-next-line @typescript-eslint/no-explicit-any
) => any;

export interface PaginatedResult<T> {
  /** Current page rows. */
  rows: T[];
  /** Total matching row count (used for pagination). */
  total: number;
  /** True while the request is in flight. */
  loading: boolean;
  /** Error message if the last fetch failed, otherwise null. */
  error: string | null;
  /** Current 0-based page index. */
  page: number;
  /** Jump to a specific page. */
  setPage: (p: number) => void;
}

/**
 * Fetch a paginated slice of a Supabase table.
 *
 * @param table     - Supabase table name.
 * @param columns   - Column selection string passed to `.select()`.
 * @param buildQuery - Callback that receives the base query and applies
 *                    additional filters / ordering before execution.
 * @param deps      - Dependency array — the fetch re-runs when any value
 *                    here changes. Typically filter/sort state variables.
 * @param pageSize  - Rows per page (default: {@link PAGE_SIZE}).
 */
export function usePaginatedFetch<T>(
  table: string,
  columns: string,
  buildQuery: QueryBuilder,
  deps: unknown[],
  pageSize: number = PAGE_SIZE
): PaginatedResult<T> {
  const [rows, setRows] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  // Keep a stable ref to buildQuery so it doesn't cause extra re-renders
  const buildQueryRef = useRef(buildQuery);
  buildQueryRef.current = buildQuery;

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const from = page * pageSize;
      const to = from + pageSize - 1;

      const baseQuery = supabase.from(table).select(columns, { count: "exact" });
      const filteredQuery = buildQueryRef.current(baseQuery);
      const { data, error: supabaseError, count } = await filteredQuery.range(from, to);

      if (supabaseError) {
        setError(supabaseError.message);
        setRows([]);
        setTotal(0);
      } else {
        setRows((data as T[]) ?? []);
        setTotal(count ?? 0);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [table, columns, page, pageSize, ...deps]);

  // Reset to page 0 when filters/sort change
  useEffect(() => {
    setPage(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { rows, total, loading, error, page, setPage };
}
