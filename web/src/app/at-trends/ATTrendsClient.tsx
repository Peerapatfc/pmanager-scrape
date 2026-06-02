"use client"

import { useState, useEffect } from "react"
import { TrendingUp, ChevronRight } from "lucide-react"

// ── Types ─────────────────────────────────────────────────────────────────────

interface MatchEntry {
  game_id: string
  match_date: string
  competition: string
  opponent: string
  home: boolean
  score: string
  result: "W" | "D" | "L"
  formation: string | null
  style: string | null
  at: Record<string, string | boolean | null>
}

interface TeamATProfile {
  team: string
  match_count: number
  formations: Record<string, number>
  styles: Record<string, number>
  at_frequencies: Record<string, Record<string, number>>
  matches: MatchEntry[]
}

// ── AT display config ─────────────────────────────────────────────────────────

const BOOL_FLAGS = [
  "first_time",
  "high_balls",
  "long_shots",
  "one_on_ones",
  "offside_trap",
  "counter_attack",
] as const

const ENUM_FLAGS = ["marking", "pressing"] as const

function flagLabel(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
}

// ── Sub-components ────────────────────────────────────────────────────────────

function Bar({ count, total, color }: { count: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex items-center gap-2 min-w-0">
      <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-neutral-400 tabular-nums w-14 shrink-0">
        {count}/{total} ({pct}%)
      </span>
    </div>
  )
}

function ResultBadge({ r }: { r: "W" | "D" | "L" }) {
  const cls =
    r === "W" ? "text-emerald-400 bg-emerald-400/10" :
    r === "D" ? "text-neutral-400 bg-white/5" :
    "text-red-400 bg-red-400/10"
  return (
    <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${cls}`}>{r}</span>
  )
}

function FormationPills({ formations, total }: { formations: Record<string, number>; total: number }) {
  const sorted = Object.entries(formations).sort((a, b) => b[1] - a[1])
  return (
    <div className="space-y-2">
      {sorted.map(([f, n]) => (
        <div key={f}>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-neutral-200 font-mono">{f}</span>
          </div>
          <Bar count={n} total={total} color="bg-sky-400" />
        </div>
      ))}
    </div>
  )
}

function ATSummary({ profile }: { profile: TeamATProfile }) {
  const n = profile.match_count
  const freq = profile.at_frequencies

  return (
    <div className="space-y-5">
      {/* Enum flags */}
      {ENUM_FLAGS.map((key) => {
        const vals = freq[key] ?? {}
        const sorted = Object.entries(vals).sort((a, b) => b[1] - a[1])
        if (!sorted.length) return null
        return (
          <div key={key}>
            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">{flagLabel(key)}</p>
            <div className="space-y-1.5">
              {sorted.map(([val, cnt]) => (
                <div key={val}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-neutral-300">{val}</span>
                  </div>
                  <Bar count={cnt} total={n} color="bg-violet-400" />
                </div>
              ))}
            </div>
          </div>
        )
      })}

      {/* Boolean flags */}
      <div>
        <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Tactical Flags</p>
        <div className="space-y-2">
          {BOOL_FLAGS.map((key) => {
            const vals = freq[key] ?? {}
            const onCount = (vals["true"] ?? 0)
            if (onCount === 0 && !vals["false"]) return null
            return (
              <div key={key} className="flex items-center gap-3">
                <span className="text-sm text-neutral-300 w-32 shrink-0">{flagLabel(key)}</span>
                <div className="flex-1">
                  <Bar count={onCount} total={n} color="bg-emerald-400" />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function MatchHistory({ matches }: { matches: MatchEntry[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-neutral-500 border-b border-white/10">
            <th className="pb-2 pr-3">Date</th>
            <th className="pb-2 pr-3">Opponent</th>
            <th className="pb-2 pr-3">Score</th>
            <th className="pb-2 pr-3">Formation</th>
            <th className="pb-2 pr-3">Marking</th>
            <th className="pb-2 pr-3">Pressing</th>
            <th className="pb-2 pr-3">HB</th>
            <th className="pb-2 pr-3">OO</th>
            <th className="pb-2 pr-3">LS</th>
            <th className="pb-2 pr-3">FT</th>
            <th className="pb-2 pr-3">OT</th>
            <th className="pb-2">CA</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {matches.map((m) => (
            <tr key={m.game_id} className="hover:bg-white/3">
              <td className="py-2 pr-3 text-neutral-400 tabular-nums">{m.match_date}</td>
              <td className="py-2 pr-3 text-neutral-200">{m.opponent}</td>
              <td className="py-2 pr-3">
                <div className="flex items-center gap-1.5">
                  <ResultBadge r={m.result} />
                  <span className="text-neutral-300 tabular-nums">{m.score}</span>
                </div>
              </td>
              <td className="py-2 pr-3 font-mono text-xs text-sky-300">{m.formation ?? "—"}</td>
              <td className="py-2 pr-3 text-xs text-neutral-300">{String(m.at.marking ?? "—")}</td>
              <td className="py-2 pr-3 text-xs text-neutral-300">{String(m.at.pressing ?? "—")}</td>
              {(["high_balls", "one_on_ones", "long_shots", "first_time", "offside_trap", "counter_attack"] as const).map((f) => (
                <td key={f} className="py-2 pr-3">
                  {m.at[f] === true
                    ? <span className="text-emerald-400 text-xs font-bold">ON</span>
                    : m.at[f] === false
                    ? <span className="text-neutral-600 text-xs">off</span>
                    : <span className="text-neutral-700 text-xs">—</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

export default function ATTrendsClient() {
  const [teams, setTeams] = useState<string[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [profile, setProfile] = useState<TeamATProfile | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetch("/api/at-trends")
      .then((r) => r.json())
      .then((d) => setTeams(d.teams ?? []))
      .catch(() => {})
  }, [])

  async function selectTeam(team: string) {
    if (team === selected) return
    setSelected(team)
    setProfile(null)
    setLoading(true)
    try {
      const res = await fetch(`/api/at-trends/${encodeURIComponent(team)}`)
      const data = await res.json()
      setProfile(res.ok ? data : null)
    } catch {
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-teal-400/10">
          <TrendingUp className="text-teal-400" size={24} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">AT Trends</h1>
          <p className="text-neutral-400 text-sm">
            {teams.length} team{teams.length !== 1 ? "s" : ""} tracked
          </p>
        </div>
      </div>

      <div className="flex gap-6 items-start">
        {/* Team list */}
        <div className="w-52 shrink-0 bg-white/5 border border-white/10 rounded-xl overflow-hidden">
          <div className="px-3 py-2 border-b border-white/10 text-xs text-neutral-500 uppercase tracking-wider">
            Teams
          </div>
          {teams.length === 0 && (
            <p className="px-3 py-4 text-xs text-neutral-600">No data yet — import a round first.</p>
          )}
          {teams.map((t) => (
            <button
              key={t}
              onClick={() => selectTeam(t)}
              className={`w-full flex items-center justify-between px-3 py-2.5 text-left text-sm transition-colors border-b border-white/5 last:border-0 ${
                t === selected
                  ? "bg-teal-400/10 text-teal-300"
                  : "text-neutral-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <span className="truncate">{t}</span>
              {t === selected && <ChevronRight size={14} className="shrink-0" />}
            </button>
          ))}
        </div>

        {/* Profile panel */}
        <div className="flex-1 min-w-0">
          {!selected && (
            <div className="flex items-center justify-center h-64 text-neutral-600">
              <p className="text-sm">Select a team to view AT history.</p>
            </div>
          )}

          {selected && loading && (
            <div className="flex items-center justify-center h-64 text-neutral-500">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin mx-auto mb-3" />
                <p className="text-sm">Loading...</p>
              </div>
            </div>
          )}

          {selected && !loading && !profile && (
            <div className="flex items-center justify-center h-64 text-neutral-600">
              <p className="text-sm">No data found for {selected}.</p>
            </div>
          )}

          {selected && !loading && profile && (
            <div className="space-y-6">
              {/* Team header */}
              <div className="flex items-center gap-4">
                <h2 className="text-xl font-bold text-white">{profile.team}</h2>
                <span className="text-sm text-neutral-500">{profile.match_count} match{profile.match_count !== 1 ? "es" : ""}</span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Formations */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-neutral-300 mb-4">Formations</h3>
                  {Object.keys(profile.formations).length > 0
                    ? <FormationPills formations={profile.formations} total={profile.match_count} />
                    : <p className="text-xs text-neutral-600">No formation data.</p>}
                </div>

                {/* AT Summary */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                  <h3 className="text-sm font-semibold text-neutral-300 mb-4">AT Settings</h3>
                  <ATSummary profile={profile} />
                </div>
              </div>

              {/* Match history */}
              <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-neutral-300 mb-4">Match History</h3>
                <MatchHistory matches={profile.matches} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
