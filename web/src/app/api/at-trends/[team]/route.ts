import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  )
}

type ATMap = Record<string, string | boolean | null>

function inc(obj: Record<string, number>, key: string | boolean | null) {
  const k = String(key ?? "unknown")
  obj[k] = (obj[k] ?? 0) + 1
}

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ team: string }> },
) {
  const { team: rawTeam } = await params
  const team = decodeURIComponent(rawTeam)

  const client = db()
  const [homeRes, awayRes] = await Promise.all([
    client.from("league_match_results").select("*").eq("home_team", team).order("match_date", { ascending: false }),
    client.from("league_match_results").select("*").eq("away_team", team).order("match_date", { ascending: false }),
  ])

  if (homeRes.error) return NextResponse.json({ error: homeRes.error.message }, { status: 500 })
  if (awayRes.error) return NextResponse.json({ error: awayRes.error.message }, { status: 500 })

  const seen = new Set<string>()
  const data = [...(homeRes.data ?? []), ...(awayRes.data ?? [])].filter((r) => {
    if (seen.has(r.game_id)) return false
    seen.add(r.game_id)
    return true
  }).sort((a, b) => (b.match_date ?? "").localeCompare(a.match_date ?? ""))

  if (!data.length) return NextResponse.json({ error: "No data for team" }, { status: 404 })

  const formations: Record<string, number> = {}
  const styles: Record<string, number> = {}
  const atFreq: Record<string, Record<string, number>> = {}
  const matches = []

  for (const row of data) {
    const isHome = row.home_team === team
    const at: ATMap = isHome ? (row.home_at ?? {}) : (row.away_at ?? {})
    const formation: string | null = isHome ? row.home_formation : row.away_formation
    const style: string | null = isHome ? row.home_style : row.away_style
    const hs: number = row.home_score ?? 0
    const as_: number = row.away_score ?? 0
    const won = isHome ? (hs > as_) : (as_ > hs)
    const drew = hs === as_
    const score = isHome ? `${hs}-${as_}` : `${as_}-${hs}`
    const opponent = isHome ? row.away_team : row.home_team

    if (formation) inc(formations, formation)
    if (style) inc(styles, style)

    for (const [k, v] of Object.entries(at)) {
      if (!atFreq[k]) atFreq[k] = {}
      inc(atFreq[k], v)
    }

    matches.push({
      game_id:    row.game_id,
      match_date: row.match_date,
      competition: row.competition,
      round_key:  row.round_key,
      opponent,
      home:       isHome,
      score,
      result:     drew ? "D" : won ? "W" : "L",
      formation,
      style,
      at,
    })
  }

  return NextResponse.json({
    team,
    match_count: data.length,
    formations,
    styles,
    at_frequencies: atFreq,
    matches,
  })
}
