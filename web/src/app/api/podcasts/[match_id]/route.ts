import { createClient } from "@supabase/supabase-js"
import { NextResponse } from "next/server"

function db() {
  return createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  )
}

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ match_id: string }> },
) {
  const { match_id: roundKey } = await params
  const { data, error } = await db()
    .from("round_reports")
    .select("source_doc, podcast_script")
    .eq("round_key", decodeURIComponent(roundKey))
    .single()

  if (error || !data) {
    return NextResponse.json({ error: "Not found" }, { status: 404 })
  }
  return NextResponse.json(data)
}
