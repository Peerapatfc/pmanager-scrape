-- match_reports: post-match data scraped from relatorio.asp
-- Populated by main_podcast_pipeline.py after each completed match.

CREATE TABLE match_reports (
    match_id                TEXT PRIMARY KEY,
    home_team_id            TEXT,
    away_team_id            TEXT,
    home_score              INT,
    away_score              INT,
    home_formation          TEXT,
    away_formation          TEXT,
    home_style              TEXT,
    away_style              TEXT,
    home_at_settings        JSONB DEFAULT '{}'::jsonb,
    away_at_settings        JSONB DEFAULT '{}'::jsonb,
    goalscorers             JSONB DEFAULT '[]'::jsonb,   -- [{team, player_name, minute}]
    substitutions           JSONB DEFAULT '[]'::jsonb,   -- [{team, off, on, minute}]
    player_ratings          JSONB DEFAULT '{}'::jsonb,   -- {player_name: rating_float}
    man_of_match            TEXT,
    commentary              TEXT,
    league_matchday_results JSONB DEFAULT '[]'::jsonb,   -- [{home_team, away_team, result}]
    podcast_path            TEXT,                        -- relative path to output dir
    script_generated_at     TIMESTAMPTZ,
    scraped_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_match_reports_script_generated ON match_reports (script_generated_at);
