/**
 * Shared formatting and colour-classification utilities for the dashboard.
 *
 * All functions are pure and dependency-free so they can be used in both
 * server and client components.
 */

import { toZonedTime, format } from "date-fns-tz";

import {
  MARGIN_HIGH_THRESHOLD,
  MARGIN_MED_THRESHOLD,
  ROI_HIGH_THRESHOLD,
  ROI_MED_THRESHOLD,
} from "@/lib/constants";

const BKK = "Asia/Bangkok";

/**
 * Parse and format a PManager deadline string into Bangkok time.
 *
 * Accepts ISO strings, PostgreSQL timestamps ("2026-03-30 14:30:00"),
 * and TIMESTAMPTZ strings. Returns "—" for null/unparseable values.
 *
 * @param value - Raw deadline string from Supabase.
 * @returns Formatted string like "30/03/2026, 14:30" or "—".
 */
export function formatDeadline(value: string | null | undefined): string {
  if (!value) return "—";
  // Normalise "YYYY-MM-DD HH:mm:ss" → ISO 8601 with Bangkok offset
  const iso = value.includes("T") ? value : value.replace(" ", "T") + "+07:00";
  const date = new Date(iso);
  if (isNaN(date.getTime())) return "—";
  return format(toZonedTime(date, BKK), "dd/MM/yyyy, HH:mm", { timeZone: BKK });
}

/**
 * Format a large number as a human-readable string with M/K suffix.
 *
 * Examples:
 *   formatValue(5_000_000) → "5.0M"
 *   formatValue(500_000)   → "500K"
 *   formatValue(999)       → "999"
 */
export function formatValue(n: number): string {
  if (!n && n !== 0) return "—";
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

/**
 * Return a Tailwind text-colour class based on a player's quality tier.
 *
 * @param quality - Quality string from the database (e.g. "World Class").
 * @returns Tailwind CSS class string.
 */
export function qualityColor(quality: string): string {
  switch (quality) {
    case "World Class":
      return "text-yellow-400";
    case "Formidable":
      return "text-purple-400";
    case "Excellent":
      return "text-blue-400";
    case "Good":
      return "text-green-400";
    default:
      return "text-gray-400";
  }
}

/**
 * Return a Tailwind text-colour class based on an ROI percentage value.
 *
 * @param roiValue - ROI percentage (e.g. 150 for 150%).
 * @returns Tailwind CSS class string.
 */
export function roiColor(roiValue: number): string {
  if (roiValue >= ROI_HIGH_THRESHOLD) return "text-emerald-400";
  if (roiValue >= ROI_MED_THRESHOLD) return "text-yellow-400";
  return "text-red-400";
}

/**
 * Return a Tailwind text-colour class based on a profit margin percentage.
 *
 * @param margin - Profit margin percentage (e.g. 75 for 75%).
 * @returns Tailwind CSS class string.
 */
export function marginColor(margin: number): string {
  if (margin >= MARGIN_HIGH_THRESHOLD) return "text-emerald-400";
  if (margin >= MARGIN_MED_THRESHOLD) return "text-yellow-400";
  return "text-red-400";
}
