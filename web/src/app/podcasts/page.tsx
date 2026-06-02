import { supabase } from "@/lib/supabase"
import PodcastsClient from "./PodcastsClient"

export const revalidate = 60

export type MatchSummary = {
  match_id: string
  home: string
  away: string
  result: string
}

export type RoundRow = {
  round_key: string
  date: string
  competition: string
  match_summaries: MatchSummary[]
  generated_at: string
}

async function getRounds(): Promise<RoundRow[]> {
  const { data, error } = await supabase
    .from("round_reports")
    .select("round_key, date, competition, match_summaries, generated_at")
    .order("date", { ascending: false })

  if (error) {
    console.error("Failed to fetch round_reports:", error.message)
    return []
  }
  return (data ?? []) as RoundRow[]
}

export default async function PodcastsPage() {
  const rounds = await getRounds()
  return <PodcastsClient rounds={rounds} />
}
