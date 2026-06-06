import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_KEY!,
  )
}

type Goal = { minute?: number; player_name?: string; team?: string }
type Report = {
  match_id: string
  home_score?: number
  away_score?: number
  goalscorers?: Goal[]
  home_formation?: string
  away_formation?: string
  home_style?: string
  away_style?: string
  home_at_settings?: Record<string, unknown>
  away_at_settings?: Record<string, unknown>
  player_ratings?: Record<string, number>
  man_of_match?: string
}
type Summary = { match_id: string; home: string; away: string; result: string }

function fmtAT(ats: Record<string, unknown>): string {
  const entries = Object.entries(ats)
  if (!entries.length) return "—"
  return entries.map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`).join(" | ")
}

function compileSourceDoc(
  competition: string,
  date: string,
  summaries: Summary[],
  reportMap: Map<string, Report>,
): string {
  const sections: string[] = []

  sections.push(
    [
      "# Match Day Source Document",
      "",
      `**Competition:** ${competition}  `,
      `**Date:** ${date}  `,
      `**Matches:** ${summaries.length}`,
    ].join("\n"),
  )

  const tableLines = [
    "## All Results This Matchday\n",
    "| Home | Score | Away |",
    "|------|-------|------|",
    ...summaries.map((s) => `| ${s.home ?? "?"} | **${s.result ?? "?"}** | ${s.away ?? "?"} |`),
  ]
  sections.push(tableLines.join("\n"))

  for (const s of summaries) {
    const r = reportMap.get(String(s.match_id))
    if (!r) continue

    const hs = r.home_score
    const as_ = r.away_score
    const score = hs != null && as_ != null ? `${hs}-${as_}` : s.result

    const lines: string[] = [`## ${s.home} ${score} ${s.away}\n`]

    const goals = r.goalscorers ?? []
    if (goals.length) {
      lines.push("### Goals\n")
      for (const g of goals) {
        const min = g.minute ? `${g.minute}'` : ""
        lines.push(`- ${min} **${g.player_name ?? "?"}** (${g.team ?? ""})`)
      }
      lines.push("")
    }

    lines.push("### Tactical\n")
    lines.push(`- **${s.home}:** ${r.home_formation ?? "?"} · ${r.home_style ?? "?"} | ATs: ${fmtAT(r.home_at_settings ?? {})}`)
    lines.push(`- **${s.away}:** ${r.away_formation ?? "?"} · ${r.away_style ?? "?"} | ATs: ${fmtAT(r.away_at_settings ?? {})}`)
    lines.push("")

    const ratings = r.player_ratings ?? {}
    const mom = r.man_of_match
    if (mom || Object.keys(ratings).length) {
      lines.push("### Standouts\n")
      if (mom) lines.push(`- **Man of the Match:** ${mom}`)
      const top = Object.entries(ratings)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
      for (const [name, rating] of top) {
        lines.push(`- ${name}: ${rating.toFixed(1)}`)
      }
      lines.push("")
    }

    sections.push(lines.join("\n"))
  }

  return sections.join("\n\n---\n\n")
}

export async function POST(
  _req: Request,
  { params }: { params: Promise<{ match_id: string }> },
) {
  try {
    const { match_id: roundKey } = await params
    const supabase = db()
    const key = decodeURIComponent(roundKey)

    const { data: round, error: roundErr } = await supabase
      .from("round_reports")
      .select("competition, date, match_summaries")
      .eq("round_key", key)
      .single()

    if (roundErr || !round) {
      return NextResponse.json({ error: roundErr?.message ?? "Round not found" }, { status: 404 })
    }

    const summaries: Summary[] = round.match_summaries ?? []
    const matchIds = summaries.map((s) => String(s.match_id))

    const { data: matchReports } = await supabase
      .from("match_reports")
      .select(
        "match_id, home_score, away_score, goalscorers, home_formation, away_formation, home_style, away_style, home_at_settings, away_at_settings, player_ratings, man_of_match",
      )
      .in("match_id", matchIds)

    const reportMap = new Map<string, Report>()
    for (const r of matchReports ?? []) {
      reportMap.set(String(r.match_id), r as Report)
    }

    const sourceDoc = compileSourceDoc(round.competition, round.date, summaries, reportMap)

    await supabase
      .from("round_reports")
      .update({ source_doc: sourceDoc })
      .eq("round_key", key)

    return NextResponse.json({ source_doc: sourceDoc })
  } catch (err) {
    return NextResponse.json({ error: String(err) }, { status: 500 })
  }
}
