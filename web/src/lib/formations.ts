export interface Formation {
  name: string
  /** 11 slot codes: GK, LB, CD, RB, LM, CM, RM, LF, CF, RF */
  slots: string[]
}

export const FORMATIONS: Formation[] = [
  { name: "3-2-5 v1", slots: ["GK","CD","CD","CD","CM","CM","LF","CF","CF","CF","RF"] },
  { name: "3-2-5 v2", slots: ["GK","LB","CD","RB","CM","CM","LF","CF","CF","CF","RF"] },
  { name: "3-3-4 v1", slots: ["GK","CD","CD","CD","CM","CM","CM","LF","CF","CF","RF"] },
  { name: "3-3-4 v2", slots: ["GK","LB","CD","RB","CM","CM","CM","LF","CF","CF","RF"] },
  { name: "3-3-4 v3", slots: ["GK","LB","CD","RB","LM","CM","RM","LF","CF","CF","RF"] },
  { name: "3-3-4 v4", slots: ["GK","CD","CD","CD","LM","CM","RM","LF","CF","CF","RF"] },
  { name: "3-4-3 v1", slots: ["GK","CD","CD","CD","LM","CM","CM","RM","CF","CF","CF"] },
  { name: "3-4-3 v2", slots: ["GK","LB","CD","RB","LM","CM","CM","RM","CF","CF","CF"] },
  { name: "3-4-3 v3", slots: ["GK","LB","CD","RB","LM","CM","CM","RM","LF","CF","RF"] },
  { name: "3-4-3 v4", slots: ["GK","CD","CD","CD","LM","CM","CM","RM","LF","CF","RF"] },
  { name: "3-5-2 v1", slots: ["GK","CD","CD","CD","LM","CM","CM","CM","RM","CF","CF"] },
  { name: "3-5-2 v2", slots: ["GK","LB","CD","RB","LM","CM","CM","CM","RM","CF","CF"] },
  { name: "4-2-4",    slots: ["GK","LB","CD","CD","RB","CM","CM","LF","CF","CF","RF"] },
  { name: "4-3-3 v1", slots: ["GK","LB","CD","CD","RB","CM","CM","CM","CF","CF","CF"] },
  { name: "4-3-3 v2", slots: ["GK","LB","CD","CD","RB","LM","CM","RM","CF","CF","CF"] },
  { name: "4-3-3 v3", slots: ["GK","LB","CD","CD","RB","LM","CM","RM","LF","CF","RF"] },
  { name: "4-3-3 v4", slots: ["GK","LB","CD","CD","RB","CM","CM","CM","LF","CF","RF"] },
  { name: "4-4-2",    slots: ["GK","LB","CD","CD","RB","LM","CM","CM","RM","CF","CF"] },
  { name: "4-5-1",    slots: ["GK","LB","CD","CD","RB","LM","CM","CM","CM","RM","CF"] },
  { name: "5-2-3 v1", slots: ["GK","LB","CD","CD","CD","RB","CM","CM","CF","CF","CF"] },
  { name: "5-2-3 v2", slots: ["GK","LB","CD","CD","CD","RB","CM","CM","LF","CF","RF"] },
  { name: "5-3-2 v1", slots: ["GK","LB","CD","CD","CD","RB","CM","CM","CM","CF","CF"] },
  { name: "5-3-2 v2", slots: ["GK","LB","CD","CD","CD","RB","LM","CM","RM","CF","CF"] },
  { name: "5-4-1",    slots: ["GK","LB","CD","CD","CD","RB","LM","CM","CM","RM","CF"] },
]

/** Map a formation slot code to the position group string used in AT calculations. */
export function slotToGroup(slot: string): string {
  if (slot === "GK") return "GK"
  if (["LB", "CD", "RB"].includes(slot)) return "D"
  if (["LM", "CM", "RM"].includes(slot)) return "M"
  return "F" // LF, CF, RF
}
