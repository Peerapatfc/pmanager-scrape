import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  )
}

export async function GET() {
  const { data, error } = await db()
    .from("league_match_results")
    .select("home_team, away_team")

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  const teams = new Set<string>()
  for (const row of data ?? []) {
    if (row.home_team) teams.add(row.home_team)
    if (row.away_team) teams.add(row.away_team)
  }

  return NextResponse.json({ teams: [...teams].sort() })
}
