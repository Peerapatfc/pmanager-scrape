CREATE TABLE round_reports (
  round_key        TEXT PRIMARY KEY,          -- "{date}___{safe_match_type}"
  date             TEXT        NOT NULL,
  competition      TEXT        NOT NULL,
  match_summaries  JSONB       NOT NULL DEFAULT '[]', -- [{home,away,result,match_id}]
  source_doc       TEXT,
  podcast_script   TEXT,
  generated_at     TIMESTAMPTZ DEFAULT NOW()
);
