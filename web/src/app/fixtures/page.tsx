import { supabase } from "@/lib/supabase"
import type { UpcomingFixture, FixtureAnalysis, OpponentPlayer } from "@/types"
import type { PlayerWithPos } from "@/lib/atCalculations"
import FixturesClient from "./FixturesClient"

export const revalidate = 60

async function getFixtures(season: string): Promise<UpcomingFixture[]> {
  const { data, error } = await supabase
    .from("upcoming_fixtures")
    .select("*")
    .eq("season", season)
    .order("match_date")
  if (error) {
    console.error("Failed to fetch upcoming_fixtures:", error.message)
    return []
  }
  return data ?? []
}

async function getAllAnalyses(): Promise<Record<string, FixtureAnalysis>> {
  const { data, error } = await supabase
    .from("fixture_analysis")
    .select("*")
  if (error) {
    console.error("Failed to fetch fixture_analysis:", error.message)
    return {}
  }
  const map: Record<string, FixtureAnalysis> = {}
  for (const row of data ?? []) {
    map[row.opponent_team_id] = row as FixtureAnalysis
  }
  return map
}

async function getMyTeamName(): Promise<string> {
  const { data } = await supabase.from("team_info").select("team_name").limit(1).single()
  return data?.team_name ?? ""
}

async function getMyPlayers(): Promise<PlayerWithPos[]> {
  // Fetch squad membership
  const { data: squadData, error: squadError } = await supabase
    .from("my_squad")
    .select("player_id, position")
  if (squadError) {
    console.error("Failed to fetch my_squad:", squadError.message)
    return []
  }
  if (!squadData?.length) return []

  // Fetch player skills separately (avoid PostgREST join ambiguity)
  const ids = squadData.map((r) => r.player_id)
  const { data: playersData, error: playersError } = await supabase
    .from("players")
    .select("id, skills")
    .in("id", ids)
  if (playersError) {
    console.error("Failed to fetch player skills:", playersError.message)
    return []
  }

  const skillsMap = new Map(
    (playersData ?? []).map((p) => [p.id, (p.skills as Record<string, number>) ?? {}])
  )

  return squadData.map((row) => ({
    position: row.position as string,
    skills: skillsMap.get(row.player_id) ?? {},
  }))
}

type ScoutedData = {
  name: string
  position: string
  age: number
  quality: string
  skills: Record<string, number>
}

async function getScoutedPlayerSkills(
  teamIds: string[]
): Promise<Map<string, Map<string, ScoutedData>>> {
  if (!teamIds.length) return new Map()

  const { data: scoutRows, error: scoutError } = await supabase
    .from("opponent_scout_results")
    .select("player_id, team_id, player_name, position")
    .in("team_id", teamIds)
  if (scoutError) {
    console.error("Failed to fetch opponent_scout_results:", scoutError.message)
    return new Map()
  }
  if (!scoutRows?.length) return new Map()

  const playerIds = [...new Set(scoutRows.map((r) => r.player_id))]
  const { data: playerRows, error: playerError } = await supabase
    .from("players")
    .select("id, age, quality, skills")
    .in("id", playerIds)
  if (playerError) {
    console.error("Failed to fetch players for scout enrichment:", playerError.message)
    return new Map()
  }

  const playerMap = new Map((playerRows ?? []).map((p) => [p.id, p]))

  const result = new Map<string, Map<string, ScoutedData>>()
  for (const row of scoutRows) {
    if (!result.has(row.team_id)) result.set(row.team_id, new Map())
    const pd = playerMap.get(row.player_id)
    result.get(row.team_id)!.set(row.player_id, {
      name:     row.player_name ?? "",
      position: row.position ?? "",
      age:      pd?.age ?? 0,
      quality:  pd?.quality ?? "",
      skills:   (pd?.skills as Record<string, number>) ?? {},
    })
  }
  return result
}

function enrichAnalysisMap(
  analysisMap: Record<string, FixtureAnalysis>,
  scoutedMap: Map<string, Map<string, ScoutedData>>
): {
  enrichedMap: Record<string, FixtureAnalysis>
  scoutingCoverage: Record<string, { scouted: number; total: number }>
} {
  const scoutingCoverage: Record<string, { scouted: number; total: number }> = {}
  const enrichedMap: Record<string, FixtureAnalysis> = {}

  for (const [teamId, analysis] of Object.entries(analysisMap)) {
    const teamScout = scoutedMap.get(teamId)
    if (!teamScout) {
      enrichedMap[teamId] = analysis
      continue
    }

    const lineupIds = new Set<string>()
    let scoutedCount = 0

    const enrichedPlayers: OpponentPlayer[] = (analysis.opponent_players ?? []).map((p) => {
      lineupIds.add(p.id)
      if (p.source === "db") return p
      const sd = teamScout.get(p.id)
      if (sd && Object.keys(sd.skills).length > 0) {
        scoutedCount++
        return { ...p, skills: sd.skills, source: "scout" as const }
      }
      return p
    })

    const hiddenPlayers: OpponentPlayer[] = []
    for (const [playerId, sd] of teamScout.entries()) {
      if (!lineupIds.has(playerId)) {
        hiddenPlayers.push({
          id:       playerId,
          name:     sd.name,
          position: sd.position,
          age:      sd.age,
          quality:  sd.quality,
          skills:   {},
          source:   "hidden",
        })
      }
    }

    scoutingCoverage[teamId] = { scouted: scoutedCount, total: enrichedPlayers.length }
    enrichedMap[teamId] = {
      ...analysis,
      opponent_players: [...enrichedPlayers, ...hiddenPlayers],
    }
  }

  return { enrichedMap, scoutingCoverage }
}

export default async function FixturesPage() {
  const season = process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "99"

  const [fixtures, rawAnalysisMap, myPlayers, myTeamName] = await Promise.all([
    getFixtures(season),
    getAllAnalyses(),
    getMyPlayers(),
    getMyTeamName(),
  ])

  const opponentTeamIds = Object.keys(rawAnalysisMap)
  const scoutedMap = await getScoutedPlayerSkills(opponentTeamIds)
  const { enrichedMap, scoutingCoverage } = enrichAnalysisMap(rawAnalysisMap, scoutedMap)

  return (
    <FixturesClient
      fixtures={fixtures}
      analysisMap={enrichedMap}
      myPlayers={myPlayers}
      season={season}
      myTeamName={myTeamName}
      scoutingCoverage={scoutingCoverage}
    />
  )
}
