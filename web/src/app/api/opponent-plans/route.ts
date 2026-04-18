import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  )
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const team_id = searchParams.get("team_id")
  if (!team_id) {
    return NextResponse.json({ error: "team_id is required" }, { status: 400 })
  }

  const { data, error } = await db()
    .from("opponent_plans")
    .select("id, team_id, team_name, plan_name, player_ids, at_settings, saved_at")
    .eq("team_id", team_id)
    .order("saved_at", { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function POST(req: Request) {
  const body = await req.json()
  const { team_id, team_name, plan_name, player_ids, at_settings } = body

  if (!team_id || !plan_name || !Array.isArray(player_ids) || !at_settings) {
    return NextResponse.json({ error: "Invalid payload" }, { status: 400 })
  }

  const { data, error } = await db()
    .from("opponent_plans")
    .insert({ team_id, team_name, plan_name, player_ids, at_settings })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data, { status: 201 })
}
