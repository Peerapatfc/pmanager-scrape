import { supabase } from "@/lib/supabase"
import PodcastsClient from "./PodcastsClient"

export const revalidate = 60

export type PodcastRow = {
  match_id: string
  podcast_path: string | null
  home_score: number | null
  away_score: number | null
  script_generated_at: string | null
}

async function getPodcasts(): Promise<PodcastRow[]> {
  const { data, error } = await supabase
    .from("match_reports")
    .select("match_id, podcast_path, home_score, away_score, script_generated_at")
    .not("script_generated_at", "is", null)
    .order("script_generated_at", { ascending: false })

  if (error) {
    console.error("Failed to fetch match_reports:", error.message)
    return []
  }
  return (data ?? []) as PodcastRow[]
}

export default async function PodcastsPage() {
  const podcasts = await getPodcasts()
  return <PodcastsClient podcasts={podcasts} />
}
