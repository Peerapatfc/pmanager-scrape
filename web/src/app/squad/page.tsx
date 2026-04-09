import { createClient } from "@supabase/supabase-js";
import SquadClient from "./SquadClient";

export const revalidate = 300; // re-fetch every 5 minutes

export interface SquadPlayer {
  player_id: string;
  position: string;
  synced_at: string;
  name: string;
  age: number | null;
  quality: string | null;
  potential: string | null;
  skills: Record<string, number>;
}

async function getSquad(): Promise<SquadPlayer[]> {
  const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );

  const { data, error } = await supabase
    .from("my_squad")
    .select(
      "player_id, position, synced_at, players(name, age, quality, potential, skills)"
    )
    .order("position");

  if (error) {
    console.error("Failed to fetch squad:", error.message);
    return [];
  }

  return (data ?? []).map((row: any) => ({
    player_id: row.player_id,
    position: row.position,
    synced_at: row.synced_at,
    name: row.players?.name ?? "Unknown",
    age: row.players?.age ?? null,
    quality: row.players?.quality ?? null,
    potential: row.players?.potential ?? null,
    skills: row.players?.skills ?? {},
  }));
}

export default async function SquadPage() {
  const players = await getSquad();
  return <SquadClient players={players} />;
}
