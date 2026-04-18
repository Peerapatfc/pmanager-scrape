import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_KEY!,
  )
}

export async function GET() {
  const { data, error } = await db()
    .from("saved_lineups")
    .select("id, name, formation_idx, lineup, saved_at")
    .order("saved_at", { ascending: false })

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}

export async function POST(req: Request) {
  const body = await req.json()
  const { name, formation_idx, lineup } = body

  if (!name || formation_idx == null || !Array.isArray(lineup)) {
    return NextResponse.json({ error: "Invalid payload" }, { status: 400 })
  }

  const { data, error } = await db()
    .from("saved_lineups")
    .insert({ name, formation_idx, lineup })
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data, { status: 201 })
}
