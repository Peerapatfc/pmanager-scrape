// web/src/lib/atCalculations.ts
// AT matchup calculations per PManager manual §13.

import type { ATPatternRecord } from "@/types"

export type ATResult = "win" | "lose" | "partial" | "na"

export interface ConditionResult {
  label: string
  myValue: number
  oppValue: number
  myWins: boolean
}

export interface ATMatchup {
  name: string
  opponentEnabled: boolean
  enabledCount: number
  activatedCount: number
  totalMatches: number
  conditions: ConditionResult[]
  result: ATResult
}

export interface PlayerWithPos {
  position: string
  skills: Record<string, number>
}

// Position helpers
const isGK = (pos: string) => pos === "GK"
const isDF = (pos: string) => pos.startsWith("D")
const isMF = (pos: string) => pos.startsWith("M")
const isFW = (pos: string) => pos.startsWith("F") || pos.startsWith("A")

function skillAvg(players: Record<string, number>[], ...keys: string[]): number {
  if (!players.length) return 0
  const total = players.reduce((s, p) => s + keys.reduce((ks, k) => ks + (p[k] ?? 0), 0), 0)
  return total / (players.length * keys.length)
}

function skillSum(players: Record<string, number>[], key: string): number {
  return players.reduce((s, p) => s + (p[key] ?? 0), 0)
}

function group(all: PlayerWithPos[], fn: (p: string) => boolean): Record<string, number>[] {
  return all.filter(p => fn(p.position)).map(p => p.skills)
}

function cond(label: string, myVal: number, oppVal: number): ConditionResult {
  return { label, myValue: +myVal.toFixed(1), oppValue: +oppVal.toFixed(1), myWins: myVal > oppVal }
}

function resolve(conditions: ConditionResult[]): ATResult {
  if (!conditions.length) return "na"
  const wins = conditions.filter(c => c.myWins).length
  if (wins === conditions.length) return "win"
  if (wins === 0) return "lose"
  return "partial"
}

function pat(
  patterns: Record<string, { enabled_count: number; activated_count: number; total_matches: number }>,
  key: string
) {
  const p = patterns[key] ?? { enabled_count: 0, activated_count: 0, total_matches: 10 }
  return { enabledCount: p.enabled_count, activatedCount: p.activated_count, totalMatches: p.total_matches }
}

export function calculateATMatchups(
  myPlayers: PlayerWithPos[],
  oppPlayers: PlayerWithPos[],
  atPatterns: Record<string, ATPatternRecord>,
  oppSettings: {
    pressing?: string
    offside_trap?: boolean
    counter_attack?: boolean
    high_balls?: boolean
    one_on_ones?: boolean
    marking?: string
    keeping?: string
    first_time?: boolean
    long_shots?: boolean
  }
): ATMatchup[] {
  const myGK  = group(myPlayers, isGK)
  const myDF  = group(myPlayers, isDF)
  const myMF  = group(myPlayers, isMF)
  const myFW  = group(myPlayers, isFW)
  const myAll = myPlayers.map(p => p.skills)

  const oppGK  = group(oppPlayers, isGK)
  const oppDF  = group(oppPlayers, isDF)
  const oppMF  = group(oppPlayers, isMF)
  const oppFW  = group(oppPlayers, isFW)
  const oppAll = oppPlayers.map(p => p.skills)

  const matchups: ATMatchup[] = []

  // ── PRESSING ──────────────────────────────────────────────────────────
  const pressing = oppSettings.pressing
  if (pressing === "High") {
    const cs = [
      cond("Speed (sum)", skillSum(myAll, "Speed"), skillSum(oppAll, "Speed")),
      cond("Passing (sum)", skillSum(myAll, "Passing"), skillSum(oppAll, "Passing")),
    ]
    matchups.push({ name: "High Pressing", opponentEnabled: true, ...pat(atPatterns, "pressing"), conditions: cs, result: resolve(cs) })
  } else if (pressing === "Low") {
    const cs = [
      cond("Speed: mine > opp (neutralises)", skillSum(myAll, "Speed"), skillSum(oppAll, "Speed")),
      cond("Tackling: opp > mine (their advantage)", skillSum(myAll, "Tackling"), skillSum(oppAll, "Tackling")),
    ]
    matchups.push({ name: "Low Pressing", opponentEnabled: true, ...pat(atPatterns, "pressing"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "Pressing", opponentEnabled: false, ...pat(atPatterns, "pressing"), conditions: [], result: "na" })
  }

  // ── OFFSIDE TRAP ──────────────────────────────────────────────────────
  if (oppSettings.offside_trap) {
    const cs = [
      cond("DF Positioning vs my FW", skillSum(myDF, "Positioning"), skillSum(oppDF, "Positioning")),
      cond("DF Speed vs my FW Speed", skillSum(myDF, "Speed"), skillSum(oppDF, "Speed")),
    ]
    matchups.push({ name: "Offside Trap", opponentEnabled: true, ...pat(atPatterns, "offside_trap"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "Offside Trap", opponentEnabled: false, ...pat(atPatterns, "offside_trap"), conditions: [], result: "na" })
  }

  // ── COUNTER ATTACK ────────────────────────────────────────────────────
  if (oppSettings.counter_attack) {
    const cs = [
      cond("Speed (sum)", skillSum(myAll, "Speed"), skillSum(oppAll, "Speed")),
      cond("Passing (sum)", skillSum(myAll, "Passing"), skillSum(oppAll, "Passing")),
    ]
    matchups.push({ name: "Counter Attack", opponentEnabled: true, ...pat(atPatterns, "counter_attack"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "Counter Attack", opponentEnabled: false, ...pat(atPatterns, "counter_attack"), conditions: [], result: "na" })
  }

  // ── HIGH BALLS ────────────────────────────────────────────────────────
  if (oppSettings.high_balls) {
    const cs = [
      cond("Heading (sum)", skillSum(myAll, "Heading"), skillSum(oppAll, "Heading")),
      cond("Strength (sum)", skillSum(myAll, "Strength"), skillSum(oppAll, "Strength")),
    ]
    matchups.push({ name: "High Balls", opponentEnabled: true, ...pat(atPatterns, "high_balls"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "High Balls", opponentEnabled: false, ...pat(atPatterns, "high_balls"), conditions: [], result: "na" })
  }

  // ── ONE-ON-ONES ───────────────────────────────────────────────────────
  if (oppSettings.one_on_ones) {
    const oppAttack = [...oppMF, ...oppFW]
    const myDefend  = [...myDF,  ...myMF]
    const cs = [
      cond(
        "Tech+Str (opp MF/FW) vs Tck+Str (my DF/MF)",
        skillAvg(myDefend, "Tackling", "Strength"),
        skillAvg(oppAttack, "Technique", "Strength")
      ),
    ]
    matchups.push({ name: "One-on-Ones", opponentEnabled: true, ...pat(atPatterns, "one_on_ones"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "One-on-Ones", opponentEnabled: false, ...pat(atPatterns, "one_on_ones"), conditions: [], result: "na" })
  }

  // ── KEEPING STYLE ─────────────────────────────────────────────────────
  const keeping = oppSettings.keeping
  if (keeping === "Stand In") {
    const cs = [cond("Ref+Han (opp GK) vs Hea+Fin (my FW)", skillAvg(myFW, "Heading", "Finishing"), skillAvg(oppGK, "Reflexes", "Handling"))]
    matchups.push({ name: "Keeping (Stand In)", opponentEnabled: true, ...pat(atPatterns, "keeping"), conditions: cs, result: resolve(cs) })
  } else if (keeping === "Rushing Out" || keeping === "Rush Out") {
    const cs = [cond("Agi+Cro (opp GK) vs Hea+Tec (my FW)", skillAvg(myFW, "Heading", "Technique"), skillAvg(oppGK, "Agility", "Out of Area"))]
    matchups.push({ name: "Keeping (Rush Out)", opponentEnabled: true, ...pat(atPatterns, "keeping"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "Keeping Style", opponentEnabled: false, ...pat(atPatterns, "keeping"), conditions: [], result: "na" })
  }

  // ── MARKING ───────────────────────────────────────────────────────────
  const marking = oppSettings.marking
  if (marking === "Zonal") {
    const oppDM = [...oppDF, ...oppMF]
    const myMF_ = [...myMF,  ...myFW]
    const cs = [cond("Spd+Tck (opp DF/MF) vs Pos+Spd (my MF/FW)", skillAvg(myMF_, "Positioning", "Speed"), skillAvg(oppDM, "Speed", "Tackling"))]
    matchups.push({ name: "Zonal Marking", opponentEnabled: true, ...pat(atPatterns, "zonal_marking"), conditions: cs, result: resolve(cs) })
  } else if (marking === "Man to Man" || marking === "Man-to-Man") {
    const oppDM = [...oppDF, ...oppMF]
    const myMF_ = [...myMF,  ...myFW]
    const cs = [cond("Str+Tck (opp DF/MF) vs Pos+Str (my MF/FW)", skillAvg(myMF_, "Positioning", "Strength"), skillAvg(oppDM, "Strength", "Tackling"))]
    matchups.push({ name: "Man-to-Man Marking", opponentEnabled: true, ...pat(atPatterns, "man_marking"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "Marking", opponentEnabled: false, ...pat(atPatterns, "zonal_marking"), conditions: [], result: "na" })
  }

  // ── LONG SHOTS ────────────────────────────────────────────────────────
  if (oppSettings.long_shots) {
    const oppAtt = [...oppMF, ...oppFW]
    const cs = [cond("Fin+Tec (opp MF/FW) vs Agi_GK+Pos_DF (mine)", (skillAvg(myGK, "Agility") + skillAvg(myDF, "Positioning")) / 2, skillAvg(oppAtt, "Finishing", "Technique"))]
    matchups.push({ name: "Long Shots", opponentEnabled: true, ...pat(atPatterns, "long_shots"), conditions: cs, result: resolve(cs) })
  } else {
    matchups.push({ name: "Long Shots", opponentEnabled: false, ...pat(atPatterns, "long_shots"), conditions: [], result: "na" })
  }

  // ── FIRST TIME SHOTS ──────────────────────────────────────────────────
  if (oppSettings.first_time) {
    const hasThreeFwds = oppFW.length >= 3
    if (!hasThreeFwds) {
      matchups.push({ name: "First Time Shots", opponentEnabled: false, ...pat(atPatterns, "first_time"), conditions: [], result: "na" })
    } else {
      const cs = [cond("Fin+Hea (opp FW) vs Ref_GK+Hea_DF (mine)", (skillAvg(myGK, "Reflexes") + skillAvg(myDF, "Heading")) / 2, skillAvg(oppFW, "Finishing", "Heading"))]
      matchups.push({ name: "First Time Shots", opponentEnabled: true, ...pat(atPatterns, "first_time"), conditions: cs, result: resolve(cs) })
    }
  } else {
    matchups.push({ name: "First Time Shots", opponentEnabled: false, ...pat(atPatterns, "first_time"), conditions: [], result: "na" })
  }

  return matchups
}

export function detectArchetype(players: PlayerWithPos[]): "speed" | "strength" {
  if (!players.length) return "speed"
  const avgSpeed    = players.reduce((s, p) => s + (p.skills["Speed"]    ?? 0), 0) / players.length
  const avgStrength = players.reduce((s, p) => s + (p.skills["Strength"] ?? 0), 0) / players.length
  return avgSpeed > avgStrength ? "speed" : "strength"
}

// Re-export type alias so consumers don't need to import from types/index
export type { ATPatternRecord } from "@/types"
