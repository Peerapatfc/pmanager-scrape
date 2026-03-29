-- Deploy this in the Supabase SQL editor to create the new table for Bot Opportunities

CREATE TABLE IF NOT EXISTS bot_opportunities (
    id TEXT PRIMARY KEY,
    name TEXT,
    position TEXT,
    age INTEGER,
    quality TEXT,
    team_name TEXT,
    estimated_value BIGINT DEFAULT 0,
    asking_price BIGINT DEFAULT 0,
    value_diff BIGINT DEFAULT 0,
    profit_margin REAL DEFAULT 0,
    url TEXT,
    scraped_at TIMESTAMPTZ DEFAULT now(),
    last_evaluated_at TIMESTAMPTZ DEFAULT NULL
);

-- Indexes to help the dashboard and worker with fast sorting
CREATE INDEX IF NOT EXISTS idx_bot_opportunities_quality ON bot_opportunities(quality);
CREATE INDEX IF NOT EXISTS idx_bot_opportunities_profit ON bot_opportunities(profit_margin DESC);
CREATE INDEX IF NOT EXISTS idx_bot_opportunities_diff ON bot_opportunities(value_diff DESC);
CREATE INDEX IF NOT EXISTS idx_bot_opportunities_evaluated ON bot_opportunities(last_evaluated_at ASC NULLS FIRST);
