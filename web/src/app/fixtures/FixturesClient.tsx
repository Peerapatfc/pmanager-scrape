"use client"

import { useState } from "react"
import { CalendarDays, Check, ChevronRight, RefreshCw, Search, Shield, Zap, Activity } from "lucide-react"
import type { UpcomingFixture, FixtureAnalysis, ATPatternRecord } from "@/types"
import {
  calculateATMatchups,
  detectArchetype,
  type PlayerWithPos,
  type ATMatchup,
  type ATResult,
} from "@/lib/atCalculations"

interface Props {
  fixtures: UpcomingFixture[]
  analysisMap: Record<string, FixtureAnalysis>
  myPlayers: PlayerWithPos[]
  season: string
  myTeamName: string
  scoutingCoverage: Record<string, { scouted: number; total: number }>
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso: string | null): string {
  if (!iso) return "TBD"
  const hasTimezone = iso.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(iso)
  const d = new Date(hasTimezone ? iso : iso + "Z")
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Bangkok",
  })
}

function resultBadge(result: string | undefined) {
  if (!result) return null
  const r = result.trim()
  if (!r) return null
  const [a, b] = r.split(/[-:]/).map(Number)
  const color = isNaN(a) || isNaN(b)
    ? "text-neutral-400"
    : a > b ? "text-emerald-400" : a < b ? "text-red-400" : "text-yellow-400"
  return <span className={`text-xs font-bold ${color}`}>{r}</span>
}

function ATResultBadge({ result }: { result: ATResult }) {
  const map: Record<ATResult, { label: string; cls: string }> = {
    win:     { label: "WIN",     cls: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" },
    lose:    { label: "LOSE",    cls: "bg-red-500/20 text-red-300 border-red-500/30" },
    partial: { label: "PARTIAL", cls: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30" },
    na:      { label: "N/A",     cls: "bg-neutral-700/40 text-neutral-400 border-neutral-600/30" },
  }
  const { label, cls } = map[result]
  return (
    <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${cls}`}>
      {label}
    </span>
  )
}

function archetypeIcon(archetype: "speed" | "strength") {
  return archetype === "speed"
    ? <Zap size={14} className="text-yellow-400 inline" />
    : <Shield size={14} className="text-blue-400 inline" />
}

function sourceBadge(source: string) {
  const styles: Record<string, string> = {
    scout:   "bg-emerald-950 text-emerald-400 border border-emerald-900/50",
    db:      "bg-emerald-500/20 text-emerald-400",
    est:     "bg-yellow-500/20 text-yellow-400",
    est_low: "bg-red-500/20 text-red-400",
    hidden:  "bg-stone-900 text-stone-500",
  }
  const label = source === "est_low" ? "EST" : source.toUpperCase()
  return (
    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${styles[source] ?? "bg-neutral-700 text-neutral-400"}`}>
      {label}
    </span>
  )
}

// Build oppSettings object from AT patterns for calculateATMatchups
function buildOppSettings(analysis: FixtureAnalysis) {
  const p = analysis.at_patterns
  const mostCommon = (key: string) => p[key]?.most_common_setting
  const isEnabled  = (key: string) => (p[key]?.enabled_count ?? 0) > 0

  return {
    pressing:         isEnabled("pressing") ? mostCommon("pressing") : undefined,
    offside_trap:     isEnabled("offside_trap"),
    counter_attack:   isEnabled("counter_attack"),
    high_balls:       isEnabled("high_balls"),
    one_on_ones:      isEnabled("one_on_ones"),
    marking:          isEnabled("marking") ? mostCommon("marking") : undefined,
    keeping:          mostCommon("keeping") ?? undefined,
    first_time_shots: isEnabled("first_time"),
    long_shots:       isEnabled("long_shots"),
  }
}

// ── Sub-components ────────────────────────────────────────────────────────────

const AT_LABEL: Record<string, string> = {
  keeping:       "Keeping Style",
  offside_trap:  "Offside Trap",
  counter_attack:"Counter Attack",
  high_balls:    "High Balls",
  one_on_ones:   "One on Ones",
  first_time:    "First Time Shots",
  long_shots:    "Long Shots",
  marking:       "Marking",
  pressing:      "Pressing",
}

function PatternBar({ pattern, label }: { pattern: ATPatternRecord; label: string }) {
  const pct = pattern.total_matches > 0
    ? Math.round((pattern.enabled_count / pattern.total_matches) * 100)
    : 0
  const actPct = pattern.enabled_count > 0
    ? Math.round((pattern.activated_count / pattern.enabled_count) * 100)
    : 0

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-neutral-300">
        <span>{label}</span>
        <span className="text-neutral-400">
          {pattern.enabled_count}/{pattern.total_matches} enabled
          {pattern.most_common_setting && (
            <span className="ml-1 text-cyan-400">· {pattern.most_common_setting}</span>
          )}
        </span>
      </div>
      <div className="h-1.5 bg-neutral-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-rose-500 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      {pattern.enabled_count > 0 && (
        <div className="text-[10px] text-neutral-500">
          Activated when enabled: {actPct}%
        </div>
      )}
    </div>
  )
}

function ATMatchupRow({ m }: { m: ATMatchup }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border border-neutral-700/50 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-white/5 transition-colors text-left"
        onClick={() => setOpen(o => !o)}
      >
        <div className="flex items-center gap-2">
          <ChevronRight
            size={14}
            className={`text-neutral-400 transition-transform ${open ? "rotate-90" : ""}`}
          />
          <span className="text-sm text-neutral-200">{m.name}</span>
          {!m.opponentEnabled && (
            <span className="text-[10px] text-neutral-500">not used</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-[10px] text-neutral-500">
          <span>{m.enabledCount}/{m.totalMatches}</span>
          <ATResultBadge result={m.result} />
        </div>
      </button>
      {open && m.conditions.length > 0 && (
        <div className="px-3 pb-3 space-y-1 border-t border-neutral-700/50 bg-neutral-800/30">
          {m.conditions.map((c, i) => (
            <div key={i} className="flex items-center justify-between text-xs py-1">
              <span className="text-neutral-400 truncate max-w-[55%]">{c.label}</span>
              <div className="flex items-center gap-2">
                <span className={c.myWins ? "text-emerald-400 font-bold" : "text-neutral-400"}>
                  Me: {c.myValue}
                </span>
                <span className="text-neutral-600">vs</span>
                <span className={!c.myWins ? "text-red-400 font-bold" : "text-neutral-400"}>
                  Opp: {c.oppValue}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function AnalysisPanel({
  fixture,
  analysis,
  myPlayers,
  season,
  oppId,
  scoutingCoverage,
}: {
  fixture: UpcomingFixture
  analysis: FixtureAnalysis | null
  myPlayers: PlayerWithPos[]
  season: string
  oppId: string | null
  scoutingCoverage: Record<string, { scouted: number; total: number }>
}) {
  const [triggering, setTriggering] = useState(false)
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null)
  const [scouting, setScouting] = useState(false)
  const [scoutMsg, setScoutMsg] = useState<string | null>(null)

  const coverage = oppId ? scoutingCoverage[oppId] : undefined

  async function handleTrigger() {
    if (!oppId) return
    setTriggering(true)
    setTriggerMsg(null)
    try {
      const res = await fetch("/api/match-prep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ opponent_team_id: oppId, season }),
      })
      const data = await res.json()
      setTriggerMsg(data.message ?? data.error ?? "Unknown response")
    } catch {
      setTriggerMsg("Request failed — check network.")
    } finally {
      setTriggering(false)
    }
  }

  async function handleScout() {
    if (!oppId) return
    setScouting(true)
    setScoutMsg(null)
    try {
      const res = await fetch("/api/scout-opponent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_id: oppId }),
      })
      const data = await res.json()
      setScoutMsg(data.message ?? data.error ?? "Unknown response")
    } catch {
      setScoutMsg("Request failed — check network.")
    } finally {
      setTimeout(() => setScouting(false), 10000)
    }
  }

  // AT matchups
  const lineupPlayers = (analysis?.opponent_players ?? []).filter(p => p.source !== "hidden")
  const hiddenPlayers = (analysis?.opponent_players ?? []).filter(p => p.source === "hidden")

  const matchups: ATMatchup[] = analysis
    ? calculateATMatchups(
        myPlayers,
        lineupPlayers.map(p => ({
          position: p.position,
          skills: p.skills,
        })),
        analysis.at_patterns,
        buildOppSettings(analysis)
      )
    : []

  const myArchetype = detectArchetype(myPlayers)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h2 className="text-lg font-bold text-white">
              {fixture.home_team_name} <span className="text-neutral-500">vs</span> {fixture.away_team_name}
            </h2>
            {coverage && coverage.scouted > 0 && (
              <span className="flex items-center gap-0.5 px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-900/50 text-[10px] font-medium">
                <Check size={9} />
                {coverage.scouted}/{coverage.total} scouted
              </span>
            )}
          </div>
          <div className="text-sm text-neutral-400 mt-0.5">
            {formatDate(fixture.match_date)} · {fixture.match_type}
            {fixture.result && (
              <span className="ml-2">{resultBadge(fixture.result)}</span>
            )}
          </div>
        </div>
        <button
          onClick={handleTrigger}
          disabled={triggering}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600/20 border border-rose-500/30 text-rose-300 hover:bg-rose-600/30 transition-colors text-xs font-medium disabled:opacity-50"
        >
          <RefreshCw size={12} className={triggering ? "animate-spin" : ""} />
          {triggering ? "Triggering…" : "Run Analysis"}
        </button>
      </div>

      {triggerMsg && (
        <div className="text-xs px-3 py-2 rounded-lg bg-neutral-800 text-neutral-300 border border-neutral-700">
          {triggerMsg}
        </div>
      )}

      {!analysis ? (
        <div className="text-neutral-500 text-sm py-8 text-center border border-neutral-700/50 rounded-xl">
          No analysis yet — click <span className="text-rose-300">Run Analysis</span> to generate.
        </div>
      ) : (
        <>
          {/* Formation + Archetype */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
              <div className="text-[10px] uppercase tracking-wider text-neutral-500 mb-1">Predicted Formation</div>
              <div className="text-base font-bold text-white">
                {analysis.predicted_formation ?? "Unknown"}
              </div>
              {analysis.predicted_style && (
                <div className="text-xs text-neutral-400 mt-0.5">{analysis.predicted_style}</div>
              )}
            </div>
            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
              <div className="text-[10px] uppercase tracking-wider text-neutral-500 mb-1">Team Archetype</div>
              <div className="flex items-center gap-1.5 text-base font-bold text-white">
                {archetypeIcon(analysis.team_archetype)}
                <span className="capitalize">{analysis.team_archetype}</span>
              </div>
              <div className="text-[10px] text-neutral-500 mt-0.5">
                Mine: {archetypeIcon(myArchetype)} <span className="capitalize">{myArchetype}</span>
              </div>
            </div>
          </div>

          {/* Formation history */}
          {analysis.formation_history?.length > 0 && (
            <div className="bg-white/5 rounded-xl p-3 border border-white/10">
              <div className="text-[10px] uppercase tracking-wider text-neutral-500 mb-2">Last {analysis.formation_history.length} Matches</div>
              <div className="flex flex-wrap gap-1.5">
                {analysis.formation_history.map((h, i) => (
                  <span key={i} className="px-2 py-0.5 rounded bg-neutral-700/60 text-xs text-neutral-300">
                    {h.formation ?? "?"} {h.style ? `· ${h.style}` : ""}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* AT Patterns */}
          <div>
            <div className="text-[10px] uppercase tracking-wider text-neutral-500 mb-2">AT Usage Patterns</div>
            <div className="space-y-2">
              {Object.entries(analysis.at_patterns).map(([key, pat]) => (
                <PatternBar
                  key={key}
                  label={AT_LABEL[key] ?? key.replace(/_/g, " ")}
                  pattern={pat as ATPatternRecord}
                />
              ))}
              {/* Fallback: show Keeping Style from matchup data when old analysis has no at_patterns.keeping */}
              {!analysis.at_patterns.keeping && analysis.team_archetype && (() => {
                const keepingMatchup = matchups.find(m => m.name.startsWith("Keeping"))
                if (!keepingMatchup) return null
                const setting = keepingMatchup.opponentEnabled
                  ? keepingMatchup.name.replace("Keeping ", "").replace(/[()]/g, "")
                  : "Not Defined"
                return (
                  <div key="keeping-fallback" className="space-y-1">
                    <div className="flex justify-between text-xs text-neutral-300">
                      <span>Keeping Style</span>
                      <span className="text-cyan-400">· {setting}</span>
                    </div>
                    <div className="h-1.5 bg-neutral-700 rounded-full overflow-hidden" />
                  </div>
                )
              })()}
              {Object.keys(analysis.at_patterns).length === 0 && (
                <p className="text-xs text-neutral-600">No AT data collected yet.</p>
              )}
            </div>
          </div>

          {/* AT Matchups */}
          {matchups.length > 0 && (
            <div>
              <div className="text-[10px] uppercase tracking-wider text-neutral-500 mb-2 flex items-center gap-1.5">
                <Activity size={12} />
                AT Matchup Analysis
              </div>
              <div className="space-y-1.5">
                {matchups.map((m, i) => (
                  <ATMatchupRow key={i} m={m} />
                ))}
              </div>
            </div>
          )}

          {/* Opponent Squad */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <div className="text-[10px] uppercase tracking-wider text-neutral-500">
                Opponent Squad
                {lineupPlayers.length > 0 && ` (${lineupPlayers.length} in lineup${hiddenPlayers.length > 0 ? ` + ${hiddenPlayers.length} bench` : ""})`}
              </div>
              {oppId && (
                <button
                  onClick={handleScout}
                  disabled={scouting}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-950/60 border border-blue-900/50 text-blue-400 hover:bg-blue-900/40 transition-colors text-[10px] font-medium disabled:opacity-50"
                >
                  <Search size={10} />
                  {scouting ? "Triggering…" : "Scout Opponent"}
                </button>
              )}
            </div>
            {scoutMsg && (
              <div className="text-xs px-3 py-2 rounded-lg bg-neutral-800 text-neutral-300 border border-neutral-700 mb-2">
                {scoutMsg}
              </div>
            )}
            {lineupPlayers.length === 0 && hiddenPlayers.length === 0 ? (
              <div className="text-xs text-neutral-600 text-center py-3 border border-neutral-800 rounded-lg">
                No squad data — click Scout Opponent to fetch.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-neutral-500 border-b border-neutral-700/50">
                      <th className="text-left py-1 pr-2">Pos</th>
                      <th className="text-left py-1 pr-2">Name</th>
                      <th className="text-left py-1 pr-2">Age</th>
                      <th className="text-left py-1 pr-2">Quality</th>
                      <th className="text-left py-1">Src</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lineupPlayers.map((p) => (
                      <tr key={p.id} className="border-b border-neutral-800/50 hover:bg-white/5">
                        <td className="py-1 pr-2 font-mono text-cyan-400">{p.position}</td>
                        <td className="py-1 pr-2 text-neutral-200 max-w-[140px] truncate">{p.name}</td>
                        <td className="py-1 pr-2 text-neutral-400">{p.age}</td>
                        <td className="py-1 pr-2 text-neutral-300">{p.quality}</td>
                        <td className="py-1">{sourceBadge(p.source)}</td>
                      </tr>
                    ))}
                    {hiddenPlayers.length > 0 && (
                      <tr>
                        <td colSpan={5} className="py-2">
                          <div className="flex items-center gap-2">
                            <div className="flex-1 border-t border-dashed border-neutral-700/50" />
                            <span className="text-[10px] text-neutral-600 whitespace-nowrap">
                              Squad · skills hidden ({hiddenPlayers.length})
                            </span>
                            <div className="flex-1 border-t border-dashed border-neutral-700/50" />
                          </div>
                        </td>
                      </tr>
                    )}
                    {hiddenPlayers.map((p) => (
                      <tr key={p.id} className="border-b border-neutral-800/30">
                        <td className="py-1 pr-2 font-mono text-neutral-500">{p.position}</td>
                        <td className="py-1 pr-2 text-neutral-500 max-w-[140px] truncate">{p.name}</td>
                        <td className="py-1 pr-2 text-neutral-600">{p.age || "—"}</td>
                        <td className="py-1 pr-2 text-neutral-600">{p.quality || "—"}</td>
                        <td className="py-1">{sourceBadge(p.source)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="text-[10px] text-neutral-600 text-right">
            Analyzed: {new Date(analysis.analyzed_at).toLocaleDateString("en-GB", { timeZone: "Asia/Bangkok" })}
          </div>
        </>
      )}
    </div>
  )
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function FixturesClient({ fixtures, analysisMap, myPlayers, season, myTeamName, scoutingCoverage }: Props) {
  const [selected, setSelected] = useState<UpcomingFixture | null>(
    fixtures.length > 0 ? fixtures[0] : null
  )

  // Derive opponent team id: the team that isn't ours
  function getOpponentId(fixture: UpcomingFixture): string | null {
    // Normalise names: trim + collapse non-breaking spaces for robust comparison
    const norm = (s: string | null | undefined) =>
      (s ?? "").trim().replace(/\u00a0/g, " ").toLowerCase()
    const myName = norm(myTeamName)
    if (myName && norm(fixture.home_team_name) === myName) return fixture.away_team_id ?? null
    if (myName && norm(fixture.away_team_name) === myName) return fixture.home_team_id ?? null
    // Fallback when myTeamName unavailable — prefer away, but never return null
    // if one side has data.
    return fixture.away_team_id ?? fixture.home_team_id ?? null
  }

  const selectedOppId = selected ? getOpponentId(selected) : null
  const selectedAnalysis = selectedOppId ? (analysisMap[selectedOppId] ?? null) : null

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center gap-3">
        <CalendarDays className="text-rose-400" size={24} />
        <div>
          <h1 className="text-2xl font-bold text-white">Match Prep</h1>
          <p className="text-sm text-neutral-400">Upcoming fixtures & opponent analysis · Season {season}</p>
        </div>
      </div>

      {fixtures.length === 0 ? (
        <div className="text-center py-16 text-neutral-500">
          <CalendarDays size={40} className="mx-auto mb-3 opacity-30" />
          <p>No upcoming fixtures found for season {season}.</p>
          <p className="text-xs mt-1">Run the Fixture Sync workflow to populate data.</p>
        </div>
      ) : (
        <div className="flex gap-5 items-start">
          {/* Left — fixture list */}
          <div className="w-72 shrink-0 space-y-1.5">
            {fixtures.map(f => {
              const oppId = getOpponentId(f)
              const hasAnalysis = oppId ? !!analysisMap[oppId] : false
              const isSelected = selected?.match_id === f.match_id

              return (
                <button
                  key={f.match_id}
                  onClick={() => setSelected(f)}
                  className={`w-full text-left px-3 py-2.5 rounded-xl border transition-all ${
                    isSelected
                      ? "bg-rose-600/20 border-rose-500/40 text-white"
                      : "bg-white/5 border-white/10 text-neutral-300 hover:bg-white/10"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium truncate">
                      {f.home_team_name} <span className="text-neutral-500">vs</span> {f.away_team_name}
                    </span>
                    {f.result && resultBadge(f.result)}
                  </div>
                  <div className="flex items-center justify-between mt-0.5">
                    <span className="text-[10px] text-neutral-500">{formatDate(f.match_date)}</span>
                    {hasAnalysis && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                        Analysed
                      </span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>

          {/* Right — analysis panel */}
          <div className="flex-1 min-w-0 bg-white/5 backdrop-blur border border-white/10 rounded-2xl p-5">
            {selected ? (
              <AnalysisPanel
                fixture={selected}
                analysis={selectedAnalysis}
                myPlayers={myPlayers}
                season={season}
                oppId={selectedOppId}
                scoutingCoverage={scoutingCoverage}
              />
            ) : (
              <div className="text-center py-12 text-neutral-500">
                Select a fixture to view analysis.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
