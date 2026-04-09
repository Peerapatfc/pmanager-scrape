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

  // Fetch squad membership first
  const { data: squadData, error: squadError } = await supabase
    .from("my_squad")
    .select("player_id, position, synced_at")
    .order("position");

  if (squadError) {
    console.error("Failed to fetch my_squad:", squadError.message);
    return [];
  }
  if (!squadData?.length) return [];

  // Fetch player profiles separately to avoid PostgREST join ambiguity
  const ids = squadData.map((r) => r.player_id);
  const { data: playersData, error: playersError } = await supabase
    .from("players")
    .select("id, name, age, quality, potential, skills")
    .in("id", ids);

  if (playersError) {
    console.error("Failed to fetch players:", playersError.message);
    return [];
  }

  const playersMap = new Map((playersData ?? []).map((p) => [p.id, p]));

  return squadData.map((row) => {
    const player = playersMap.get(row.player_id);
    return {
      player_id: row.player_id,
      position: row.position,
      synced_at: row.synced_at,
      name: player?.name ?? "Unknown",
      age: player?.age ?? null,
      quality: player?.quality ?? null,
      potential: player?.potential ?? null,
      skills: (player?.skills as Record<string, number>) ?? {},
    };
  });
}

export default async function SquadPage() {
  const players = await getSquad();
  return <SquadClient players={players} />;
}
