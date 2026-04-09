import { supabase } from "@/lib/supabase"
import type { UpcomingFixture, FixtureAnalysis } from "@/types"
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

export default async function FixturesPage() {
  const season = process.env.NEXT_PUBLIC_CURRENT_SEASON ?? "99"

  const [fixtures, analysisMap, myPlayers, myTeamName] = await Promise.all([
    getFixtures(season),
    getAllAnalyses(),
    getMyPlayers(),
    getMyTeamName(),
  ])

  return (
    <FixturesClient
      fixtures={fixtures}
      analysisMap={analysisMap}
      myPlayers={myPlayers}
      season={season}
      myTeamName={myTeamName}
    />
  )
}
