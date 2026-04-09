/** Shared skill column definitions — used by Squad and Players tables. */
export const SKILLS = [
  { abbr: "Han", field: "Handling" },
  { abbr: "Cro", field: "Out of Area" },
  { abbr: "Ref", field: "Reflexes" },
  { abbr: "Agi", field: "Agility" },
  { abbr: "Tck", field: "Tackling" },
  { abbr: "Hea", field: "Heading" },
  { abbr: "Pas", field: "Passing" },
  { abbr: "Pos", field: "Positioning" },
  { abbr: "Fin", field: "Finishing" },
  { abbr: "Tec", field: "Technique" },
  { abbr: "Spe", field: "Speed" },
  { abbr: "Str", field: "Strength" },
] as const;

export type SkillEntry = (typeof SKILLS)[number];
