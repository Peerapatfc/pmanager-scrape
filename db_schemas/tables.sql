-- PManager Scraper: Supabase Tables
-- Run this in the Supabase SQL Editor

-- 1. Players (replaces "All Players" sheet)
CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY,
    name TEXT,
    position TEXT,
    age INTEGER,
    nationality TEXT,
    quality TEXT,
    potential TEXT,
    affected_quality TEXT,
    skills JSONB DEFAULT '{}'::jsonb,
    bids_count TEXT,
    bids_avg TEXT,
    deadline TEXT,
    url TEXT,
    last_transfer_price BIGINT DEFAULT 0,
    sale_to_bid_ratio REAL DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Transfer Listings (replaces "Transfer Info" sheet)
CREATE TABLE IF NOT EXISTS transfer_listings (
    id TEXT PRIMARY KEY,
    name TEXT,
    position TEXT,
    age INTEGER,
    quality TEXT,
    potential TEXT,
    estimated_value BIGINT DEFAULT 0,
    asking_price BIGINT DEFAULT 0,
    value_diff BIGINT DEFAULT 0,
    roi REAL DEFAULT 0,
    forecast_sell REAL DEFAULT 0,
    forecast_profit REAL DEFAULT 0,
    deadline TEXT,
    url TEXT,
    last_updated TIMESTAMPTZ DEFAULT now()
);

-- 3. Team Info (replaces "Team Info" sheet, single row)
CREATE TABLE IF NOT EXISTS team_info (
    id INTEGER PRIMARY KEY DEFAULT 1,
    team_name TEXT,
    manager TEXT,
    available_funds TEXT,
    financial_situation TEXT,
    wages_sum TEXT,
    wage_roof TEXT,
    academy TEXT,
    players_count TEXT,
    age_average TEXT,
    players_value TEXT,
    team_reputation TEXT,
    current_division TEXT,
    fan_club_size TEXT,
    recorded_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Bot Opportunities (undervalued players from BOT teams)
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
    last_evaluated_at TIMESTAMPTZ
);

-- 5. Opponent Scout Results — matched players from opponent team scouting sessions
CREATE TABLE IF NOT EXISTS opponent_scout_results (
    team_id            TEXT NOT NULL,
    player_id          TEXT NOT NULL,
    team_name          TEXT,
    player_name        TEXT,
    position           TEXT,
    age                INTEGER,
    quality            TEXT,
    player_link        TEXT,
    is_watchlist_match BOOLEAN DEFAULT FALSE,
    scouted_at         TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (team_id, player_id)
);

-- Migration: add age and quality columns if upgrading from an older schema
-- ALTER TABLE opponent_scout_results ADD COLUMN IF NOT EXISTS age INTEGER;
-- ALTER TABLE opponent_scout_results ADD COLUMN IF NOT EXISTS quality TEXT;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);
CREATE INDEX IF NOT EXISTS idx_players_age ON players(age);
CREATE INDEX IF NOT EXISTS idx_transfer_listings_deadline ON transfer_listings(deadline);
CREATE INDEX IF NOT EXISTS idx_transfer_listings_roi ON transfer_listings(roi);
