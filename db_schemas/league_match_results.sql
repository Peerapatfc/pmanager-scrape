-- league_match_results: per-match structured data for all matches in a round
-- Populated by main_import_round.py from manually assembled source documents.
-- Enables AT trend analysis (Option C) and round-level querying.

CREATE TABLE league_match_results (
    game_id          TEXT PRIMARY KEY,              -- PManager game ID (e.g. "19501929")
    round_key        TEXT,                           -- "{date}___{safe_competition}" FK to round_reports
    match_date       DATE,
    competition      TEXT,
    home_team        TEXT NOT NULL,
    away_team        TEXT NOT NULL,
    home_score       INT,
    away_score       INT,
    home_formation   TEXT,
    away_formation   TEXT,
    home_style       TEXT,
    away_style       TEXT,
    home_at          JSONB NOT NULL DEFAULT '{}',   -- {marking, pressing, first_time, high_balls, ...}
    away_at          JSONB NOT NULL DEFAULT '{}',
    stats            JSONB NOT NULL DEFAULT '{}',   -- {possession_home, shots_home, shots_on_goal_home, ...}
    goalscorers      JSONB NOT NULL DEFAULT '[]',   -- [{player, team, minute}]
    imported_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_league_results_round ON league_match_results (round_key);
CREATE INDEX idx_league_results_date  ON league_match_results (match_date);
CREATE INDEX idx_league_results_comp  ON league_match_results (competition);
