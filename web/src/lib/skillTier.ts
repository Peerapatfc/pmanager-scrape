export interface SkillTier {
  label: string;
  /** Text color (for labels) */
  color: string;
  /** Background color (for chips / bar fills) */
  bg: string;
}

/**
 * Maps a 0–20 skill value to a quality tier with display colors.
 *
 * Scale:
 *  0       → Terrible
 *  1–2     → Very Bad
 *  3–4     → Bad
 *  5–6     → Very Weak
 *  7–8     → Weak
 *  9–10    → Passable
 *  11–12   → Good
 *  13–14   → Very Good
 *  15–16   → Excellent
 *  17–18   → Formidable
 *  19–20   → World Class
 */
export function getSkillTier(value: number): SkillTier {
  if (value <= 0)  return { label: "Terrible",    color: "#fca5a5", bg: "#7f1d1d" };
  if (value <= 2)  return { label: "Very Bad",    color: "#fca5a5", bg: "#b91c1c" };
  if (value <= 4)  return { label: "Bad",         color: "#fdba74", bg: "#c2410c" };
  if (value <= 6)  return { label: "Very Weak",   color: "#fde68a", bg: "#b45309" };
  if (value <= 8)  return { label: "Weak",        color: "#fef08a", bg: "#a16207" };
  if (value <= 10) return { label: "Passable",    color: "#d9f99d", bg: "#4d7c0f" };
  if (value <= 12) return { label: "Good",        color: "#bbf7d0", bg: "#15803d" };
  if (value <= 14) return { label: "Very Good",   color: "#6ee7b7", bg: "#047857" };
  if (value <= 16) return { label: "Excellent",   color: "#5eead4", bg: "#0f766e" };
  if (value <= 18) return { label: "Formidable",  color: "#67e8f9", bg: "#0e7490" };
  return            { label: "World Class",       color: "#a5f3fc", bg: "#0369a1" };
}

/** Clamp a value to [0, 20] before passing to getSkillTier. */
export function skillTier(value: number | undefined | null): SkillTier {
  return getSkillTier(Math.max(0, Math.min(20, value ?? 0)));
}
