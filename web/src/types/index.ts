/**
 * Shared TypeScript interfaces for pmanager-scrape dashboard.
 *
 * These types mirror the Supabase table schemas defined in db_schemas/ and
 * should be updated if any column is added, removed, or renamed.
 */

/** A player record from the `players` table. */
export interface Player {
  id: string;
  name: string;
  position: string;
  age: number;
  nationality?: string;
  quality: string;
  potential: string;
  affected_quality?: string;
  /** Dynamic skill attributes stored as JSONB. */
  skills: Record<string, number>;
  bids_count: number;
  bids_avg: number;
  last_transfer_price: number;
  sale_to_bid_ratio: number;
  deadline: string;
  url?: string;
}

/** A transfer market listing from the `transfer_listings` table. */
export interface Transfer {
  id: string;
  name?: string;
  position?: string;
  age?: number;
  quality?: string;
  potential?: string;
  estimated_value: number;
  asking_price: number;
  value_diff: number;
  roi: number;
  forecast_sell: number;
  forecast_profit: number;
  deadline: string;
  url: string;
  last_updated: string;
}

/** A BOT team player opportunity from the `bot_opportunities` table. */
export interface BotOpportunity {
  id: string;
  name?: string;
  position?: string;
  age?: number;
  team_name: string;
  quality: string;
  estimated_value: number;
  asking_price: number;
  value_diff: number;
  profit_margin: number;
  scraped_at: string;
  last_evaluated_at: string;
  url?: string;
}

/** A matched player from an opponent scout session (`opponent_scout_results` table). */
export interface OpponentScoutResult {
  team_id: string;
  player_id: string;
  team_name: string | null;
  player_name: string | null;
  position: string | null;
  player_link: string | null;
  scouted_at: string;
}

/** The single team info snapshot from the `team_info` table (id=1). */
export interface TeamInfo {
  id: number;
  team_name: string;
  manager?: string;
  available_funds?: string;
  wages_sum?: string;
  players_count?: string;
  current_division?: string;
  recorded_at?: string;
}
