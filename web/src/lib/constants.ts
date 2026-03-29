/**
 * Shared UI constants for the pmanager-scrape dashboard.
 *
 * Keep magic numbers and option lists here so they are defined once and
 * imported wherever needed.
 */

/** Default number of rows displayed per page in all data tables. */
export const PAGE_SIZE = 50;

/** Debounce delay (ms) for search input fields. */
export const DEBOUNCE_MS = 500;

/** Player position filter options (empty string = "All"). */
export const POSITIONS = ["", "GK", "DF", "MF", "FW"] as const;
export type Position = (typeof POSITIONS)[number];

/** BOT player quality filter options (empty string = "All"). */
export const QUALITIES = [
  "",
  "World Class",
  "Formidable",
  "Excellent",
] as const;
export type Quality = (typeof QUALITIES)[number];

/** ROI percentage above which a listing is highlighted green. */
export const ROI_HIGH_THRESHOLD = 200;

/** ROI percentage above which a listing is highlighted yellow. */
export const ROI_MED_THRESHOLD = 100;

/** Profit margin percentage above which an opportunity is highlighted green. */
export const MARGIN_HIGH_THRESHOLD = 50;

/** Profit margin percentage above which an opportunity is highlighted yellow. */
export const MARGIN_MED_THRESHOLD = 20;
