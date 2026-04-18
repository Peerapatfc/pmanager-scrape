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
  Bookmark,
  Trash2,
  X,
  Copy,
  Check,
  Shield,
} from "lucide-react";

import { supabase } from "@/lib/supabase";
import { PAGE_SIZE, DEBOUNCE_MS, POSITIONS } from "@/lib/constants";
import { formatDeadline, qualityColor } from "@/lib/utils";
import { FORMATIONS, slotToGroup } from "@/lib/formations";
import type { OpponentScoutResult, Player, SavedLineup } from "@/types";

// ── AT Matchup types & helpers ────────────────────────────────────────────────
interface MySquadPlayer { id: string; position: string; skills: Record<string, number> }

interface ATSettings {
  pressing: "None" | "High" | "Low"
  offside_trap: boolean
  counter_attack: boolean
  high_balls: boolean
  one_on_ones: boolean
  keeping: "Normal" | "Stand In" | "Rush Out"
  marking: "None" | "Zonal" | "Man to Man"
  long_shots: boolean
  first_time: boolean
  notes?: string
}

const DEFAULT_AT_SETTINGS: ATSettings = {
  pressing: "None",
  offside_trap: false,
  counter_attack: false,
  high_balls: false,
  one_on_ones: false,
  keeping: "Normal",
  marking: "None",
  long_shots: false,
  first_time: false,
}

interface OpponentPlan {
  id: string
  team_id: string
  team_name: string | null
  plan_name: string
  player_ids: string[]
  at_settings: ATSettings
  saved_at: string
}

function isATEnabled(label: string, s: ATSettings): boolean {
  switch (label) {
    case "Pressing – High":    return s.pressing === "High"
    case "Pressing – Low":     return s.pressing === "Low"
    case "Counter Attack":     return s.counter_attack
    case "Offside Trap":       return s.offside_trap
    case "High Balls":         return s.high_balls
    case "One on Ones":        return s.one_on_ones
    case "Keeping – Stand In": return s.keeping === "Stand In"
    case "Keeping – Rush Out": return s.keeping === "Rush Out"
    case "Marking – Zonal":    return s.marking === "Zonal"
    case "Marking – Man to Man": return s.marking === "Man to Man"
    case "Long Shots":         return s.long_shots
    case "First Time Shots":   return s.first_time
    default: return false
  }
}

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

interface ATCondition {
  label: string
  mine: number
  theirs: number
  wins: boolean
}

interface ATMatchup {
  label: string;
  mine: number | null;
  theirs: number | null;
  /** true=win, false=lose, null=N/A */
  result: boolean | null;
  partial?: boolean;
  /** Per-condition breakdown — only present for multi-condition ATs */
  conditions?: ATCondition[];
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

  function row(label: string, conditions: { label: string; mine: number; theirs: number; lowerIsBetter?: boolean }[]): ATMatchup {
    const res = multi(conditions);
    const mine = conditions[0].mine;
    const theirs = conditions[0].theirs;
    const conds: ATCondition[] = conditions.map(c => ({
      label: c.label,
      mine: c.mine,
      theirs: c.theirs,
      wins: c.lowerIsBetter ? c.mine < c.theirs : c.mine > c.theirs,
    }))
    if (typeof res === "object") return { label, mine, theirs, result: false, partial: true, conditions: conds };
    return { label, mine, theirs, result: res, conditions: conds };
  }

  function single(label: string, mine: number | null, theirs: number | null): ATMatchup {
    if (mine === null || theirs === null) return { label, mine, theirs, result: null };
    return { label, mine, theirs, result: mine > theirs };
  }

  const results: ATMatchup[] = [
    row("Pressing – High", [
      { label: "Speed",   mine: a(myAll, "Speed"),   theirs: a(oppAll, "Speed") },
      { label: "Passing", mine: a(myAll, "Passing"), theirs: a(oppAll, "Passing") },
    ]),
    row("Pressing – Low", [
      { label: "Speed (lower = better)", mine: a(myAll, "Speed"),    theirs: a(oppAll, "Speed"),    lowerIsBetter: true },
      { label: "Tackling",               mine: a(myAll, "Tackling"), theirs: a(oppAll, "Tackling") },
    ]),
    row("Counter Attack", [
      { label: "Speed",   mine: a(myAll, "Speed"),   theirs: a(oppAll, "Speed") },
      { label: "Passing", mine: a(myAll, "Passing"), theirs: a(oppAll, "Passing") },
    ]),
    row("Offside Trap", [
      { label: "DF Positioning vs FW", mine: a(myD, "Positioning"), theirs: a(oppF, "Positioning") },
      { label: "DF Speed vs FW",       mine: a(myD, "Speed"),       theirs: a(oppF, "Speed") },
    ]),
    row("High Balls", [
      { label: "Heading",  mine: a(myAll, "Heading"),  theirs: a(oppAll, "Heading") },
      { label: "Strength", mine: a(myAll, "Strength"), theirs: a(oppAll, "Strength") },
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

function ATResultRow({ label, mine, theirs, result, partial, conditions }: ATMatchup) {
  return (
    <div className="bg-neutral-900 rounded text-xs overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-1.5">
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
      {/* Condition breakdown — only shown when partial */}
      {partial && conditions && (
        <div className="px-3 pb-2 space-y-0.5 border-t border-neutral-800/60 pt-1.5">
          {conditions.map(c => (
            <div key={c.label} className="flex items-center gap-2 text-[10px]">
              <span className="text-neutral-600 w-40 shrink-0">{c.label}</span>
              <span className={`font-mono w-8 text-right shrink-0 ${c.wins ? "text-emerald-400" : "text-neutral-400"}`}>
                {c.mine.toFixed(1)}
              </span>
              <span className="text-neutral-700 shrink-0">vs</span>
              <span className={`font-mono w-8 shrink-0 ${!c.wins ? "text-red-400/80" : "text-neutral-500"}`}>
                {c.theirs.toFixed(1)}
              </span>
              <span className={`font-bold ${c.wins ? "text-emerald-500" : "text-red-500"}`}>
                {c.wins ? "✓" : "✗"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function FormationVisual({
  players,
  dbRows,
}: {
  players: MySquadPlayer[]
  dbRows: OpponentScoutResult[]
}) {
  const gk = players.filter(p => posG(p.position) === "GK")
  const d  = players.filter(p => posG(p.position) === "D")
  const m  = players.filter(p => posG(p.position) === "M")
  const f  = players.filter(p => posG(p.position) === "F")
  const formation = [d.length, m.length, f.length].filter(Boolean).join("-")

  const getShortName = (id: string) => {
    const name = dbRows.find(r => r.player_id === id)?.player_name
    if (!name) return id.slice(-4)
    const parts = name.trim().split(" ")
    return parts.length > 1 ? parts[parts.length - 1] : parts[0]
  }

  const rows = [
    { key: "f",  players: f,  dot: "bg-orange-500 border-orange-400",  text: "text-orange-300"  },
    { key: "m",  players: m,  dot: "bg-blue-500 border-blue-400",      text: "text-blue-300"    },
    { key: "d",  players: d,  dot: "bg-emerald-600 border-emerald-400",text: "text-emerald-300" },
    { key: "gk", players: gk, dot: "bg-yellow-600 border-yellow-400",  text: "text-yellow-300"  },
  ].filter(r => r.players.length > 0)

  if (rows.length === 0) return null

  return (
    <div className="bg-emerald-950/15 border border-emerald-900/25 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-emerald-900/20">
        <span className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500">Formation</span>
        {formation && <span className="text-sm font-bold text-emerald-400 font-mono">{formation}</span>}
      </div>
      <div className="p-4 space-y-4" style={{ background: "linear-gradient(180deg, rgba(20,83,45,0.12) 0%, rgba(20,83,45,0.05) 100%)" }}>
        {rows.map(({ key, players: grp, dot, text }) => (
          <div key={key} className="flex justify-center items-start gap-3 flex-wrap">
            {grp.map(p => (
              <div key={p.id} className="flex flex-col items-center gap-1">
                <div className={`w-9 h-9 rounded-full border-2 ${dot} flex items-center justify-center`}>
                  <span className="text-[9px] font-bold text-white leading-none text-center">
                    {(p.position ?? "?").replace(/\s+/g, "").slice(0, 4)}
                  </span>
                </div>
                <span className={`text-[9px] font-medium ${text} max-w-[56px] truncate text-center`}>
                  {getShortName(p.id)}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function OpponentTacticsPanel({
  teamId,
  teamName,
  dbRows,
  playerDbMap,
  mySquad,
}: {
  teamId: string
  teamName: string
  dbRows: OpponentScoutResult[]
  playerDbMap: Map<string, Player>
  mySquad: MySquadPlayer[]
}) {
  const availablePlayerIds = useMemo(() => {
    const ids = dbRows.map(r => r.player_id).filter(id => playerDbMap.has(id))
    return ids.sort((a, b) => {
      const posA = (dbRows.find(r => r.player_id === a)?.position ?? playerDbMap.get(a)?.position ?? "").trim().toUpperCase()
      const posB = (dbRows.find(r => r.player_id === b)?.position ?? playerDbMap.get(b)?.position ?? "").trim().toUpperCase()
      const groupA = posA.startsWith("GK") ? 0 : posA.startsWith("D") ? 1 : posA.startsWith("M") ? 2 : 3
      const groupB = posB.startsWith("GK") ? 0 : posB.startsWith("D") ? 1 : posB.startsWith("M") ? 2 : 3
      return groupA - groupB
    })
  }, [dbRows, playerDbMap])

  const [selectedIds, setSelectedIds] = useState<Set<string>>(
    () => new Set(availablePlayerIds.slice(0, 11))
  )
  const [atSettings, setAtSettings] = useState<ATSettings>(DEFAULT_AT_SETTINGS)
  const [plans, setPlans] = useState<OpponentPlan[]>([])
  const [saveName, setSaveName] = useState("")
  const [saving, setSaving] = useState(false)
  const [activePlanId, setActivePlanId] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Our lineup selector
  const [savedLineups, setSavedLineups] = useState<SavedLineup[]>([])
  const [selectedLineupId, setSelectedLineupId] = useState<string>("")  // "" = full squad

  useEffect(() => {
    fetch(`/api/opponent-plans?team_id=${encodeURIComponent(teamId)}`)
      .then(r => r.ok ? r.json() : [])
      .then(setPlans)
      .catch(() => {})
    fetch("/api/saved-lineups")
      .then(r => r.ok ? r.json() : [])
      .then(setSavedLineups)
      .catch(() => {})
  }, [teamId])

  // Build our effective players: either from a saved lineup (with slot positions) or full mySquad
  const effectiveMyPlayers = useMemo((): MySquadPlayer[] => {
    if (!selectedLineupId) return mySquad
    const saved = savedLineups.find(l => l.id === selectedLineupId)
    if (!saved) return mySquad
    const slots = FORMATIONS[saved.formation_idx]?.slots ?? []
    const squadMap = new Map(mySquad.map(p => [p.id, p]))
    return saved.lineup.flatMap((playerId, i) => {
      if (!playerId) return []
      const player = squadMap.get(playerId)
      if (!player) return []
      return [{ ...player, position: slotToGroup(slots[i] ?? "CM") }]
    })
  }, [selectedLineupId, savedLineups, mySquad])

  const selectedOppPlayers = useMemo(() =>
    dbRows
      .filter(r => selectedIds.has(r.player_id) && playerDbMap.has(r.player_id))
      .map(r => {
        const p = playerDbMap.get(r.player_id)!
        return { id: r.player_id, position: r.position ?? p.position ?? "M C", skills: p.skills ?? {} } as MySquadPlayer
      }),
    [selectedIds, dbRows, playerDbMap]
  )

  // Our ATs vs their lineup: my team attacks, they defend
  const ourATResults = useMemo(() => computeATMatchup(effectiveMyPlayers, selectedOppPlayers as unknown as Player[]), [effectiveMyPlayers, selectedOppPlayers])
  // Their ATs vs our defense: they attack, we defend
  const theirATResults = useMemo(() => computeATMatchup(selectedOppPlayers as unknown as Player[], effectiveMyPlayers as unknown as Player[]), [selectedOppPlayers, effectiveMyPlayers])

  const defenseScore = useMemo(() => {
    // theirATResults: their attack vs our defense — theirWins=true means they beat us
    const beats  = theirATResults.filter(r => r.result === true && !r.partial).length
    const partial = theirATResults.filter(r => r.partial === true).length
    const countered = theirATResults.filter(r => r.result === false && !r.partial).length
    const dangerATs = theirATResults.filter(r => r.result === true && !r.partial).map(r => r.label)
    const counteredATs = theirATResults.filter(r => r.result === false && !r.partial).map(r => r.label)
    return { beats, partial, countered, dangerATs, counteredATs }
  }, [theirATResults])

  const matchupScore = useMemo(() => {
    const wins = ourATResults.filter(r => r.result === true).length
    const partials = ourATResults.filter(r => r.partial === true).length
    const losses = ourATResults.filter(r => r.result === false && !r.partial).length
    const recommended = ourATResults.filter(r => r.result === true).map(r => r.label)
    const avoid = ourATResults.filter(r => r.result === false && !r.partial && r.result !== null).map(r => r.label)
    return { wins, partials, losses, recommended, avoid }
  }, [ourATResults])

  const skillComparison = useMemo(() => {
    type Group = "GK" | "D" | "M" | "F"
    const GROUP_SKILLS: Record<Group, string[]> = {
      GK: ["Reflexes", "Handling", "Agility", "Out of Area"],
      D:  ["Tackling", "Positioning", "Speed", "Strength"],
      M:  ["Passing", "Technique", "Speed", "Stamina"],
      F:  ["Finishing", "Heading", "Technique", "Speed"],
    }
    const groups: Group[] = ["GK", "D", "M", "F"]
    return groups.map(g => {
      const myG = effectiveMyPlayers.filter(p => posG(p.position) === g)
      const oppG = selectedOppPlayers.filter(p => posG(p.position) === g)
      const skills = GROUP_SKILLS[g].map(s => ({
        skill: s,
        mine: avgSk(myG, s),
        theirs: avgSk(oppG as unknown as MySquadPlayer[], s),
      }))
      return { group: g, skills, myCount: myG.length, oppCount: oppG.length }
    }).filter(g => g.myCount > 0 || g.oppCount > 0)
  }, [effectiveMyPlayers, selectedOppPlayers])

  const atConflicts = useMemo(() => {
    const warnings: string[] = []
    if (atSettings.offside_trap && atSettings.counter_attack)
      warnings.push("Offside Trap + Counter Attack — contradictory (high line vs deep defend)")
    if (atSettings.pressing === "High" && atSettings.keeping === "Rush Out")
      warnings.push("High Pressing + Keeping Rush Out — GK rushes out while team presses high")
    if (atSettings.high_balls && atSettings.one_on_ones)
      warnings.push("High Balls + One on Ones — conflicting attacking approaches")
    return warnings
  }, [atSettings])

  const qualityDist = useMemo(() => {
    const ORDER = ["World Class", "Excellent", "Formidable", "Good", "Average", "Poor"]
    const counts: Record<string, number> = {}
    selectedOppPlayers.forEach(p => {
      const q = playerDbMap.get(p.id)?.quality ?? "Unknown"
      counts[q] = (counts[q] ?? 0) + 1
    })
    return Object.entries(counts).sort((a, b) => {
      const ia = ORDER.indexOf(a[0])
      const ib = ORDER.indexOf(b[0])
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib)
    })
  }, [selectedOppPlayers, playerDbMap])

  const threatPlayers = useMemo(() => {
    const ATTACK_SKILLS = ["Finishing", "Technique", "Speed", "Heading", "Strength"]
    return [...selectedOppPlayers]
      .map(p => ({
        ...p,
        name: dbRows.find(r => r.player_id === p.id)?.player_name ?? p.id,
        threatScore: ATTACK_SKILLS.reduce((s, k) => s + (p.skills[k] ?? 0), 0) / ATTACK_SKILLS.length,
      }))
      .sort((a, b) => b.threatScore - a.threatScore)
      .slice(0, 3)
  }, [selectedOppPlayers, dbRows])

  function handleCopy() {
    const d = selectedOppPlayers.filter(p => posG(p.position) === "D").length
    const m = selectedOppPlayers.filter(p => posG(p.position) === "M").length
    const f = selectedOppPlayers.filter(p => posG(p.position) === "F").length
    const formation = [d, m, f].filter(Boolean).join("-")
    const lines: string[] = [
      `vs ${teamName}${formation ? ` [${formation}]` : ""}`,
      `Matchup: ${matchupScore.wins}W / ${matchupScore.partials}P / ${matchupScore.losses}L`,
    ]
    if (matchupScore.recommended.length > 0)
      lines.push(`✓ Enable: ${matchupScore.recommended.join(", ")}`)
    if (matchupScore.avoid.length > 0)
      lines.push(`✗ Avoid: ${matchupScore.avoid.join(", ")}`)
    if (threatPlayers.length > 0)
      lines.push(`▲ Watch: ${threatPlayers.map((p, i) => `#${i + 1} ${p.name} (${p.threatScore.toFixed(1)})`).join(", ")}`)
    if (atSettings.notes?.trim())
      lines.push(`Notes: ${atSettings.notes.trim()}`)
    navigator.clipboard.writeText(lines.join("\n")).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  function togglePlayer(id: string) {
    setSelectedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
    setActivePlanId(null)
  }

  function loadPlan(plan: OpponentPlan) {
    setSelectedIds(new Set(plan.player_ids))
    setAtSettings(plan.at_settings)
    setActivePlanId(plan.id)
    setSaveName(plan.plan_name)
  }

  async function savePlan() {
    if (!saveName.trim()) return
    setSaving(true)
    try {
      const res = await fetch("/api/opponent-plans", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          team_id: teamId,
          team_name: teamName,
          plan_name: saveName.trim(),
          player_ids: Array.from(selectedIds),
          at_settings: atSettings,
        }),
      })
      if (res.ok) {
        const newPlan: OpponentPlan = await res.json()
        setPlans(prev => [newPlan, ...prev])
        setActivePlanId(newPlan.id)
      }
    } finally {
      setSaving(false)
    }
  }

  async function deletePlan(id: string) {
    await fetch(`/api/opponent-plans/${id}`, { method: "DELETE" })
    setPlans(prev => prev.filter(p => p.id !== id))
    if (activePlanId === id) setActivePlanId(null)
  }

  const hasSkillData = selectedOppPlayers.some(p => Object.keys(p.skills).length > 0)

  return (
    <div className="mt-3 border border-neutral-700/50 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-2 px-4 py-2 bg-neutral-800/60 border-b border-neutral-700/50">
        <Swords size={12} className="text-orange-400" />
        <span className="text-[10px] font-bold uppercase tracking-widest text-neutral-400">
          Tactical Analysis vs {teamName}
        </span>
        {mySquad.length < 11 && (
          <span className="text-[9px] text-yellow-500/80 italic">Set starting 11 on Squad page for best results</span>
        )}
        {!hasSkillData && selectedOppPlayers.length > 0 && (
          <span className="text-[9px] text-red-500/80 italic">Opponent skill data sparse — results may be inaccurate</span>
        )}
      </div>

      <div className="p-4 space-y-4">

        {/* ── Our lineup selector ───────────────────────────────────── */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold shrink-0">Our Lineup:</span>
          <select
            value={selectedLineupId}
            onChange={e => setSelectedLineupId(e.target.value)}
            className="bg-neutral-900 border border-neutral-700 text-xs rounded px-2 py-1 text-neutral-300 outline-none focus:border-orange-500 transition-colors"
          >
            <option value="">Full Squad ({mySquad.length} players)</option>
            {savedLineups.map(l => (
              <option key={l.id} value={l.id}>
                {l.name} — {FORMATIONS[l.formation_idx]?.name ?? `Formation ${l.formation_idx}`}
              </option>
            ))}
          </select>
          {selectedLineupId && (
            <span className="text-[10px] text-emerald-500/70 italic">
              {effectiveMyPlayers.length} players from saved lineup
            </span>
          )}
        </div>

        {/* ── Saved plans ──────────────────────────────────────────── */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold shrink-0">Plans:</span>
          {plans.length === 0 && (
            <span className="text-[10px] text-neutral-600 italic">No saved plans yet</span>
          )}
          {plans.map(plan => (
            <span
              key={plan.id}
              className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                activePlanId === plan.id
                  ? "bg-orange-500/20 border-orange-500/40 text-orange-300"
                  : "bg-neutral-800 border-neutral-700 text-neutral-400"
              }`}
            >
              <button onClick={() => loadPlan(plan)} className="hover:text-orange-300 transition-colors">
                {plan.plan_name}
              </button>
              <button
                onClick={() => deletePlan(plan.id)}
                className="text-neutral-600 hover:text-red-400 transition-colors ml-0.5"
                aria-label={`Delete plan ${plan.plan_name}`}
              >
                <Trash2 size={10} />
              </button>
            </span>
          ))}
          <div className="flex flex-col gap-1.5 ml-auto w-full sm:w-auto">
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                placeholder="Plan name…"
                value={saveName}
                onChange={e => setSaveName(e.target.value)}
                onKeyDown={e => e.key === "Enter" && savePlan()}
                className="bg-neutral-950 border border-neutral-700 text-xs rounded px-2 py-1 text-neutral-200 outline-none focus:border-orange-500 w-28 transition-colors"
              />
              <button
                onClick={savePlan}
                disabled={saving || !saveName.trim()}
                className="flex items-center gap-1 px-2.5 py-1 bg-orange-500/20 border border-orange-500/40 text-orange-400 rounded-lg text-xs font-semibold hover:bg-orange-500/30 disabled:opacity-40 transition-colors"
              >
                {saving ? <Loader2 size={11} className="animate-spin" /> : <Bookmark size={11} />}
                Save
              </button>
              <button
                onClick={handleCopy}
                disabled={selectedOppPlayers.length === 0}
                title="Copy plan summary to clipboard"
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold border transition-colors disabled:opacity-40 ${
                  copied
                    ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-400"
                    : "bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-500"
                }`}
              >
                {copied ? <Check size={11} /> : <Copy size={11} />}
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <textarea
              placeholder="Pre-match notes…"
              value={atSettings.notes ?? ""}
              onChange={e => { setAtSettings(prev => ({ ...prev, notes: e.target.value })); setActivePlanId(null) }}
              rows={2}
              className="bg-neutral-950 border border-neutral-700 text-xs rounded px-2 py-1 text-neutral-300 outline-none focus:border-orange-500 resize-none w-full transition-colors placeholder:text-neutral-600"
            />
          </div>
        </div>

        {/* ── Opponent lineup selection ─────────────────────────────── */}
        <div>
          <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold mb-2">
            Opponent Lineup — {selectedIds.size} of {availablePlayerIds.length} selected (click to toggle)
          </div>
          <div className="flex flex-wrap gap-1.5">
            {availablePlayerIds.map(id => {
              const row = dbRows.find(r => r.player_id === id)
              const p = playerDbMap.get(id)
              const selected = selectedIds.has(id)
              const posCode = (row?.position ?? p?.position ?? "?").replace(/\s+/g, "")
              return (
                <button
                  key={id}
                  onClick={() => togglePlayer(id)}
                  className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium border transition-colors ${
                    selected
                      ? "bg-blue-500/15 border-blue-500/40 text-blue-200"
                      : "bg-neutral-800 border-neutral-700 text-neutral-500 opacity-50 hover:opacity-70"
                  }`}
                >
                  <span className="text-[9px] font-mono text-neutral-500 shrink-0">{posCode}</span>
                  {row?.player_name ?? p?.name ?? id}
                  {!selected && <X size={9} className="ml-0.5 shrink-0" />}
                </button>
              )
            })}
            {availablePlayerIds.length === 0 && (
              <span className="text-[10px] text-neutral-600 italic">No players in DB for this team</span>
            )}
          </div>
        </div>

        {/* ── Formation Visual ─────────────────────────────────────── */}
        {selectedOppPlayers.length > 0 && (
          <FormationVisual players={selectedOppPlayers as unknown as MySquadPlayer[]} dbRows={dbRows} />
        )}

        {/* ── Quality Distribution ─────────────────────────────────── */}
        {qualityDist.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold shrink-0">Quality:</span>
            {qualityDist.map(([q, count]) => (
              <span key={q} className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-current/20 text-[11px] font-medium bg-neutral-900 ${qualityColor(q)}`}>
                {q}
                <span className="font-bold font-mono">{count}</span>
              </span>
            ))}
          </div>
        )}

        {/* ── Opponent AT settings ──────────────────────────────────── */}
        <div>
          <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold mb-2">
            Opponent AT Settings
          </div>
          <div className="flex flex-wrap gap-2 items-center">
            {/* Pressing select */}
            <label className="flex items-center gap-1.5">
              <span className="text-[10px] text-neutral-500">Pressing</span>
              <select
                value={atSettings.pressing}
                onChange={e => { setAtSettings(prev => ({ ...prev, pressing: e.target.value as ATSettings["pressing"] })); setActivePlanId(null) }}
                className="bg-neutral-900 border border-neutral-700 text-xs rounded px-2 py-1 text-neutral-300 outline-none focus:border-orange-500 transition-colors"
              >
                <option value="None">None</option>
                <option value="High">High</option>
                <option value="Low">Low</option>
              </select>
            </label>
            {/* Keeping select */}
            <label className="flex items-center gap-1.5">
              <span className="text-[10px] text-neutral-500">Keeping</span>
              <select
                value={atSettings.keeping}
                onChange={e => { setAtSettings(prev => ({ ...prev, keeping: e.target.value as ATSettings["keeping"] })); setActivePlanId(null) }}
                className="bg-neutral-900 border border-neutral-700 text-xs rounded px-2 py-1 text-neutral-300 outline-none focus:border-orange-500 transition-colors"
              >
                <option value="Normal">Normal</option>
                <option value="Stand In">Stand In</option>
                <option value="Rush Out">Rush Out</option>
              </select>
            </label>
            {/* Marking select */}
            <label className="flex items-center gap-1.5">
              <span className="text-[10px] text-neutral-500">Marking</span>
              <select
                value={atSettings.marking}
                onChange={e => { setAtSettings(prev => ({ ...prev, marking: e.target.value as ATSettings["marking"] })); setActivePlanId(null) }}
                className="bg-neutral-900 border border-neutral-700 text-xs rounded px-2 py-1 text-neutral-300 outline-none focus:border-orange-500 transition-colors"
              >
                <option value="None">None</option>
                <option value="Zonal">Zonal</option>
                <option value="Man to Man">Man to Man</option>
              </select>
            </label>
            {/* Boolean toggles */}
            {(
              [
                ["offside_trap",  "Offside Trap"],
                ["counter_attack","Counter Attack"],
                ["high_balls",    "High Balls"],
                ["one_on_ones",   "One on Ones"],
                ["long_shots",    "Long Shots"],
                ["first_time",    "First Time Shots"],
              ] as [keyof ATSettings, string][]
            ).map(([key, label]) => (
              <button
                key={key}
                onClick={() => { setAtSettings(prev => ({ ...prev, [key]: !prev[key] })); setActivePlanId(null) }}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors ${
                  atSettings[key]
                    ? "bg-red-500/15 border-red-500/40 text-red-300"
                    : "bg-neutral-800 border-neutral-700 text-neutral-500 hover:border-neutral-600"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* ── AT Conflict Warnings ─────────────────────────────────── */}
        {atConflicts.length > 0 && (
          <div className="space-y-1">
            {atConflicts.map(w => (
              <div key={w} className="flex items-start gap-2 px-3 py-1.5 bg-yellow-500/8 border border-yellow-500/25 rounded-lg">
                <AlertCircle size={12} className="text-yellow-400 shrink-0 mt-0.5" />
                <span className="text-[11px] text-yellow-400/90">{w}</span>
              </div>
            ))}
          </div>
        )}

        {/* ── Matchup Score + Recommendations ─────────────────────── */}
        {selectedOppPlayers.length > 0 && (
          <div className="space-y-2">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {/* Our ATs vs their defense */}
              <div className="flex flex-wrap items-center gap-2 p-3 bg-neutral-950/60 rounded-xl border border-neutral-800">
                <span className="text-[10px] text-emerald-500/70 uppercase tracking-wider font-semibold shrink-0 w-full">Our Attack</span>
                <span className="px-2 py-0.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-sm font-bold">{matchupScore.wins}W</span>
                <span className="px-2 py-0.5 rounded-lg bg-yellow-500/15 border border-yellow-500/30 text-yellow-400 text-sm font-bold">{matchupScore.partials}P</span>
                <span className="px-2 py-0.5 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-sm font-bold">{matchupScore.losses}L</span>
              </div>
              {/* Their ATs vs our defense */}
              <div className="flex flex-wrap items-center gap-2 p-3 bg-neutral-950/60 rounded-xl border border-neutral-800">
                <span className="text-[10px] text-red-500/70 uppercase tracking-wider font-semibold shrink-0 w-full">Their Attack</span>
                <span className="px-2 py-0.5 rounded-lg bg-red-500/15 border border-red-500/30 text-red-400 text-sm font-bold">{defenseScore.beats} Beat Us</span>
                <span className="px-2 py-0.5 rounded-lg bg-yellow-500/15 border border-yellow-500/30 text-yellow-400 text-sm font-bold">{defenseScore.partial}P</span>
                <span className="px-2 py-0.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-sm font-bold">{defenseScore.countered} Countered</span>
              </div>
            </div>
            <div className="space-y-1.5">
              {matchupScore.recommended.length > 0 && (
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] text-emerald-500/70 uppercase tracking-wider font-semibold shrink-0">Enable:</span>
                  {matchupScore.recommended.map(label => (
                    <span key={label} className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-[11px] font-medium">
                      {label}
                    </span>
                  ))}
                </div>
              )}
              {matchupScore.avoid.length > 0 && (
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] text-red-500/70 uppercase tracking-wider font-semibold shrink-0">Avoid:</span>
                  {matchupScore.avoid.map(label => (
                    <span key={label} className="px-2 py-0.5 rounded bg-red-500/10 border border-red-500/25 text-red-400 text-[11px] font-medium">
                      {label}
                    </span>
                  ))}
                </div>
              )}
              {defenseScore.dangerATs.length > 0 && (
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] text-orange-500/70 uppercase tracking-wider font-semibold shrink-0 flex items-center gap-1"><Shield size={9} /> Danger if they use:</span>
                  {defenseScore.dangerATs.map(label => (
                    <span key={label} className="px-2 py-0.5 rounded bg-orange-500/10 border border-orange-500/25 text-orange-400 text-[11px] font-medium">
                      {label}
                    </span>
                  ))}
                </div>
              )}
              {defenseScore.counteredATs.length > 0 && (
                <div className="flex flex-wrap gap-1.5 items-center">
                  <span className="text-[10px] text-emerald-500/70 uppercase tracking-wider font-semibold shrink-0 flex items-center gap-1"><Shield size={9} /> We counter:</span>
                  {defenseScore.counteredATs.map(label => (
                    <span key={label} className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-[11px] font-medium">
                      {label}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Threat Players ───────────────────────────────────────── */}
        {threatPlayers.length > 0 && (
          <div>
            <div className="text-[10px] text-red-400/70 uppercase tracking-wider font-semibold mb-1.5">
              Threat Players
            </div>
            <div className="flex flex-wrap gap-2">
              {threatPlayers.map((p, i) => (
                <div key={p.id} className="flex items-center gap-2 px-3 py-1.5 bg-neutral-900 border border-red-500/20 rounded-lg">
                  <span className="text-[10px] font-bold text-red-500/60">#{i + 1}</span>
                  <span className="text-xs font-medium text-neutral-200">{p.name}</span>
                  <span className="text-[10px] font-mono text-neutral-500 bg-neutral-800 px-1.5 py-0.5 rounded">
                    {(p.position ?? "?").replace(/\s+/g, "")}
                  </span>
                  <span className="text-[10px] font-bold text-red-400 font-mono">{p.threatScore.toFixed(1)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Skill Comparison by Line ─────────────────────────────── */}
        {skillComparison.length > 0 && (
          <div>
            <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold mb-1.5">
              Skill Comparison by Line
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              {skillComparison.map(({ group, skills, myCount, oppCount }) => (
                <div key={group} className="bg-neutral-900 rounded-lg p-2.5 border border-neutral-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold text-neutral-300">{group}</span>
                    <span className="text-[9px] text-neutral-600 font-mono">{myCount}v{oppCount}</span>
                  </div>
                  <div className="space-y-1.5">
                    {skills.map(({ skill, mine, theirs }) => {
                      const max = Math.max(mine, theirs, 1)
                      const iWin = mine >= theirs
                      return (
                        <div key={skill}>
                          <div className="flex justify-between text-[9px] mb-0.5">
                            <span className="text-neutral-500">{skill}</span>
                            <span className="font-mono">
                              <span className={iWin ? "text-emerald-400" : "text-neutral-400"}>{mine.toFixed(0)}</span>
                              <span className="text-neutral-700 mx-0.5">·</span>
                              <span className={!iWin ? "text-red-400" : "text-neutral-500"}>{theirs.toFixed(0)}</span>
                            </span>
                          </div>
                          <div className="flex gap-px h-1">
                            <div className="flex-1 bg-neutral-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${iWin ? "bg-emerald-500" : "bg-neutral-500"}`}
                                style={{ width: `${(mine / max) * 100}%` }}
                              />
                            </div>
                            <div className="flex-1 bg-neutral-800 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ml-auto ${!iWin ? "bg-red-500" : "bg-neutral-600"}`}
                                style={{ width: `${(theirs / max) * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── AT results (two columns) ──────────────────────────────── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* Our ATs */}
          <div>
            <div className="text-[10px] text-emerald-500/70 uppercase tracking-wider font-semibold mb-1.5">
              Our Tactics vs Their Lineup
            </div>
            <div className="space-y-px">
              {ourATResults.map(row => <ATResultRow key={row.label} {...row} />)}
            </div>
          </div>

          {/* Their ATs — swap mine/theirs for readability: "their score vs our defense" */}
          <div>
            <div className="text-[10px] text-red-500/70 uppercase tracking-wider font-semibold mb-1.5">
              Their Tactics — Can We Counter?
            </div>
            <div className="space-y-px">
              {theirATResults.map(({ label, mine: theirScore, theirs: ourScore, result: theirWins, partial }) => {
                const enabled = isATEnabled(label, atSettings)
                // theirWins=true → they beat us; theirWins=false → we counter; partial → mixed
                return (
                  <div
                    key={label}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs transition-opacity ${
                      enabled ? "bg-neutral-900 opacity-100" : "bg-neutral-950/30 opacity-40"
                    }`}
                  >
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border mr-1 shrink-0 ${
                      enabled
                        ? "text-red-400 bg-red-500/10 border-red-500/25"
                        : "text-neutral-600 bg-neutral-800 border-neutral-700"
                    }`}>
                      {enabled ? "ON" : "OFF"}
                    </span>
                    <span className="text-neutral-400 w-32 shrink-0 text-[11px]">{label}</span>
                    {!enabled || theirWins === null ? (
                      <span className="text-neutral-600 italic text-[10px]">—</span>
                    ) : (
                      <>
                        <span className="font-mono text-[11px] text-neutral-500 w-8 text-right shrink-0">
                          {theirScore !== null ? theirScore.toFixed(1) : "—"}
                        </span>
                        <span className="text-neutral-600 text-[10px] shrink-0">vs</span>
                        <span className="font-mono text-[11px] text-neutral-300 w-8 shrink-0">
                          {ourScore !== null ? ourScore.toFixed(1) : "—"}
                        </span>
                        <span className={`ml-auto text-[10px] font-bold px-1.5 py-0.5 rounded border shrink-0 ${
                          partial
                            ? "text-yellow-400 bg-yellow-500/10 border-yellow-500/25"
                            : !theirWins
                            ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/25"
                            : "text-red-400 bg-red-500/10 border-red-500/25"
                        }`}>
                          {partial ? "~ Partial" : !theirWins ? "✓ Countered" : "✗ Beats Us"}
                        </span>
                      </>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
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
  const [filterTeamId, setFilterTeamId] = useState("");
  const [sortField, setSortField] = useState("scouted_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // My squad (for AT matchup)
  const [mySquad, setMySquad] = useState<MySquadPlayer[]>([]);
  const [atExpanded, setAtExpanded] = useState<Set<string>>(new Set());
  const [scoutedTeams, setScoutedTeams] = useState<{ team_id: string; team_name: string | null }[]>([]);

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

  // Fetch distinct scouted teams for quick-load dropdown
  useEffect(() => {
    async function fetchTeams() {
      const { data } = await supabase
        .from("opponent_scout_results")
        .select("team_id, team_name")
        .order("scouted_at", { ascending: false });
      if (!data) return;
      const seen = new Set<string>();
      const unique = (data as { team_id: string; team_name: string | null }[]).filter(r => {
        if (seen.has(r.team_id)) return false;
        seen.add(r.team_id);
        return true;
      });
      setScoutedTeams(unique);
    }
    fetchTeams();
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
  }, [filterPos, filterMatchOnly, filterTeamId, sortField, sortOrder]);

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
        if (filterTeamId) query = query.eq("team_id", filterTeamId);

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
  }, [debouncedSearch, filterPos, filterMatchOnly, filterTeamId, sortField, sortOrder, page]);

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
  const clearFilters = () => { setSearch(""); setFilterPos(""); setFilterMatchOnly(false); setFilterTeamId(""); };

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

          {scoutedTeams.length > 0 && (
            <div className="flex flex-col gap-1">
              <label className="text-[10px] uppercase tracking-wider font-semibold text-neutral-500 flex items-center gap-1">
                <Swords size={10} /> Team
              </label>
              <select
                aria-label="Filter by scouted team"
                className="bg-neutral-950 border border-neutral-700 text-sm rounded-lg px-3 py-2 text-neutral-200 outline-none focus:border-orange-500 transition-colors"
                value={filterTeamId}
                onChange={(e) => setFilterTeamId(e.target.value)}
              >
                <option value="">All Teams</option>
                {scoutedTeams.map(t => (
                  <option key={t.team_id} value={t.team_id}>
                    {t.team_name ?? `Team ${t.team_id}`}
                  </option>
                ))}
              </select>
            </div>
          )}

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

                    {/* Tactical analysis panel */}
                    {atExpanded.has(teamId) && (
                      <tr className="bg-neutral-950/40">
                        <td colSpan={COL_COUNT} className="px-4 pb-4">
                          <OpponentTacticsPanel
                            teamId={teamId}
                            teamName={teamName ?? `Team ${teamId}`}
                            dbRows={dbRows}
                            playerDbMap={playerDbMap}
                            mySquad={mySquad}
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
