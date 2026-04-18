-- Saved squad lineups (named formation + player slot assignments)
CREATE TABLE IF NOT EXISTS saved_lineups (
  id         TEXT        PRIMARY KEY DEFAULT gen_random_uuid()::text,
  name       TEXT        NOT NULL,
  formation_idx INT      NOT NULL,
  lineup     JSONB       NOT NULL,   -- (string | null)[] — player_id per slot
  saved_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
