-- Saved tactical plans for opponent teams
CREATE TABLE IF NOT EXISTS opponent_plans (
  id          TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
  team_id     TEXT        NOT NULL,
  team_name   TEXT,
  plan_name   TEXT        NOT NULL,
  player_ids  JSONB       NOT NULL,   -- string[] — selected player IDs for this plan
  at_settings JSONB       NOT NULL,   -- ATSettings object — opponent's AT configuration
  saved_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_opponent_plans_team_id ON opponent_plans(team_id);
