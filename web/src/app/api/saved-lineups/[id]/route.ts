import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_KEY!,
  )
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const { error } = await db().from("saved_lineups").delete().eq("id", id)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return new NextResponse(null, { status: 204 })
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  const body = await req.json()
  const { name, formation_idx, lineup } = body

  const update: Record<string, unknown> = {}
  if (name != null) update.name = name
  if (formation_idx != null) update.formation_idx = formation_idx
  if (lineup != null) update.lineup = lineup

  const { data, error } = await db()
    .from("saved_lineups")
    .update(update)
    .eq("id", id)
    .select()
    .single()

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json(data)
}
