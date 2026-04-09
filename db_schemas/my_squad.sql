-- my_squad: tracks which players are currently in the user's squad.
-- Synced from plantel.asp by main_squad_sync.py.
-- Skills live in the existing players.skills JSONB column (no duplication).

CREATE TABLE my_squad (
  player_id  TEXT PRIMARY KEY REFERENCES players(id),
  position   TEXT NOT NULL,   -- full position string, e.g. "GK", "D C", "M RC", "F L"
  synced_at  TIMESTAMPTZ DEFAULT now()
);
