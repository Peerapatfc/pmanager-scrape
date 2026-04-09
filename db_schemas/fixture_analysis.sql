-- db_schemas/fixture_analysis.sql

CREATE TABLE upcoming_fixtures (
    match_id        TEXT PRIMARY KEY,
    match_date      TIMESTAMPTZ,
    match_type      TEXT,
    home_team_id    TEXT,
    home_team_name  TEXT,
    away_team_id    TEXT,
    away_team_name  TEXT,
    result          TEXT,
    season          TEXT,
    scraped_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_upcoming_fixtures_season ON upcoming_fixtures(season);
CREATE INDEX idx_upcoming_fixtures_date   ON upcoming_fixtures(match_date);

CREATE TABLE fixture_analysis (
    opponent_team_id    TEXT PRIMARY KEY,
    opponent_team_name  TEXT,
    season              TEXT,
    formation_history   JSONB DEFAULT '[]'::jsonb,
    predicted_formation TEXT,
    predicted_style     TEXT,
    at_patterns         JSONB DEFAULT '{}'::jsonb,
    opponent_players    JSONB DEFAULT '[]'::jsonb,
    team_archetype      TEXT,
    analyzed_at         TIMESTAMPTZ DEFAULT NOW()
);
