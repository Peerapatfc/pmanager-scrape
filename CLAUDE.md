# CLAUDE.md — pmanager-scrape

Project guide for Claude Code. Read this before modifying any file.

---

## Project Overview

**pmanager-scrape** is a player scouting and market analysis platform for [PManager.org](https://pmanager.org) — a browser-based football management game. It automates:

- Scraping the global transfer market and calculating ROI / profit metrics
- Discovering BOT (AI-controlled) teams and extracting undervalued players from their rosters
- Sending Telegram alerts with the best buy opportunities
- Displaying all data in a Next.js web dashboard backed by Supabase

---

## Architecture

```
pmanager-scrape/
│
├── Python backend          # Scrapers + services (Playwright, BeautifulSoup)
├── src/                    # Modular source: scrapers/, services/, core/, config.py
│
├── Next.js frontend        # Dashboard at web/
│   └── web/src/app/        # App Router pages + client components
│
├── Supabase (PostgreSQL)   # Cloud database — 4 tables
│
└── GitHub Actions          # Scheduled automation (.github/workflows/)
```

**Data flow:**
1. Python scripts scrape PManager.org (Playwright browser automation)
2. Data is upserted to Supabase via `supabase-py`
3. Next.js dashboard reads from Supabase via `@supabase/supabase-js`
4. GitHub Actions trigger scripts on a schedule (cron)
5. `ai_recommendation.py` sends Telegram alerts for top opportunities

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Scraping | Python 3.9+, Playwright (headless), BeautifulSoup4 |
| Data | Pandas, NumPy |
| Database | Supabase (PostgreSQL) via `supabase-py` |
| Notifications | Telegram Bot API |
| Frontend | Next.js 16, React 19, TypeScript 5 |
| Styling | Tailwind CSS v4, Glassmorphism design |
| Icons | Lucide React |
| DB Client | `@supabase/supabase-js` v2 |
| Package Manager | pnpm 10 (frontend) |
| CI/CD | GitHub Actions |

---

## Project Structure

```
pmanager-scrape/
├── src/
│   ├── config.py                   # Central config — reads .env, validates vars
│   ├── core/
│   │   ├── logger.py               # Logging setup (console with timestamps)
│   │   └── utils.py                # clean_currency(), parse_deadline()
│   ├── scrapers/
│   │   ├── base.py                 # BaseScraper — Playwright login + navigation
│   │   ├── transfer.py             # TransferScraper — market listings
│   │   └── bot_team.py             # BotTeamScraper — BOT team discovery + evaluation
│   └── services/
│       ├── supabase_client.py      # SupabaseManager — all DB operations
│       └── telegram.py             # TelegramBot — send_message() with retry
│
├── main_all_transfer.py            # Scrape full transfer market → Supabase
├── main_bot_scout.py               # Discover BOT teams → bot_opportunities table
├── main_bot_evaluate.py            # Evaluate bot players in batches (continuous)
├── ai_recommendation.py            # Filter top deals → Telegram alert
├── update_final_prices.py          # Hourly: update sale prices in players table
├── main_opponent_scout.py          # Analyze opponent teams
├── main_team_info.py               # Update team_info table (funds, roster, etc.)
│
├── web/                            # Next.js dashboard
│   ├── src/app/
│   │   ├── page.tsx                # Dashboard home (stat cards)
│   │   ├── players/                # All player records
│   │   ├── transfers/              # Transfer market listings
│   │   └── bot-opportunities/      # BOT team targets + profit margins
│   └── src/lib/supabase.ts         # Supabase browser client
│
├── db_schemas/                     # SQL CREATE TABLE statements (reference only)
├── docs/                           # BRD.md, PRD.md, SDD.md, TSD.md
├── .github/workflows/              # GitHub Actions cron jobs
├── .env.example                    # Template for required env vars
├── requirements.txt                # Python deps
└── CHANGELOG.md                    # Version history
```

---

## Environment Setup

### Backend — `.env` (copy from `.env.example`)

```env
# PManager Game Credentials
PM_USERNAME=your_username
PM_PASSWORD=your_password

# Supabase (Primary Data Store)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key        # Service role key (NOT anon key)

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_main_bot_token
SCOUT_BOT_TOKEN=your_scout_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional
GITHUB_TOKEN=your_pat                     # For triggering workflows via API
GITHUB_REPO=Peerapatfc/pmanager-scrape
GEMINI_API_KEY=your_key                   # Reserved, not currently used
```

### Frontend — `web/.env.local`

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key    # Anon/public key for browser client
```

> Note: The backend uses the **service role key** (bypasses RLS). The frontend uses the **anon key** (respects RLS).

---

## Key Scripts & Commands

### Python backend

```bash
# Install deps (once)
pip install -r requirements.txt
playwright install chromium

# Run main transfer market scrape
python main_all_transfer.py

# Run BOT team discovery (slow — traverses all countries/leagues, top 2 divisions)
python main_bot_scout.py

# Run BOT player evaluation (continuous batches until all evaluated)
python main_bot_evaluate.py

# Send Telegram alerts for top trade opportunities
python ai_recommendation.py

# Update final sale prices (run hourly)
python update_final_prices.py

# Update team info snapshot
python main_team_info.py

# Sync my squad from plantel.asp → my_squad table
python main_squad_sync.py

# Sync upcoming fixtures → fixtures table
python main_fixtures_sync.py

# Run match prep analysis
python main_match_prep.py
```

### Frontend

```bash
cd web
pnpm install     # Install deps
pnpm dev         # Dev server at http://localhost:3000
pnpm build       # Production build
pnpm start       # Start production server
```

---

## Database Schema (Supabase)

### `players` — All tracked player profiles

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PK | Player ID from PManager |
| `name` | TEXT | Player name |
| `position` | TEXT | Position (GK, DF, MF, FW) |
| `age` | INT | Player age |
| `quality` | TEXT | Quality tier (World Class, Excellent, etc.) |
| `potential` | TEXT | Potential rating |
| `skills` | JSONB | Dynamic skill attributes |
| `bids_count` | INT | Number of bids received |
| `bids_avg` | FLOAT | Average bid amount |
| `last_transfer_price` | FLOAT | Most recent sale price |
| `sale_to_bid_ratio` | FLOAT | Sale price / average bid |
| `deadline` | TIMESTAMPTZ | Auction end time |

### `transfer_listings` — Current transfer market opportunities

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PK | Player ID |
| `estimated_value` | FLOAT | Game's estimated player value |
| `asking_price` | FLOAT | Seller's asking price |
| `value_diff` | FLOAT | Estimated value − asking price |
| `roi` | FLOAT | (Est. value − asking price) / asking price |
| `forecast_sell` | FLOAT | (Est. value / 2) × 0.8 |
| `forecast_profit` | FLOAT | Forecast sell − asking price |
| `deadline` | TIMESTAMPTZ | Auction end time |
| `url` | TEXT | Direct link to negotiation page |
| `last_updated` | TIMESTAMPTZ | When this row was last scraped |

### `bot_opportunities` — Undervalued players from BOT teams

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PK | Player ID |
| `team_name` | TEXT | BOT team name |
| `quality` | TEXT | Quality tier |
| `estimated_value` | FLOAT | Estimated value |
| `asking_price` | FLOAT | Current asking price |
| `value_diff` | FLOAT | Estimated value − asking price |
| `profit_margin` | FLOAT | Profit margin percentage |
| `scraped_at` | TIMESTAMPTZ | When discovered |
| `last_evaluated_at` | TIMESTAMPTZ | Last evaluation time (used for batch ordering) |

### `team_info` — Single-row team snapshot (id=1)

| Column | Type | Description |
|--------|------|-------------|
| `team_name` | TEXT | Manager's team name |
| `available_funds` | FLOAT | Current budget |
| `wages_sum` | FLOAT | Total wage bill |
| `players_count` | INT | Roster size |
| `current_division` | TEXT | League/division |
| `recorded_at` | TIMESTAMPTZ | Snapshot timestamp |

### `my_squad` — Current squad players

| Column | Type | Description |
|--------|------|-------------|
| `player_id` | TEXT PK | FK → players.id |
| `position` | TEXT | Full position string (e.g. "D C", "M RC") |
| `synced_at` | TIMESTAMPTZ | Last sync time |

### `saved_lineups` — Named lineup saves

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PK | UUID |
| `name` | TEXT | Lineup name |
| `formation_idx` | INT | Formation index |
| `lineup` | JSONB | `(string \| null)[]` — player_id per slot |
| `saved_at` | TIMESTAMPTZ | Save time |

### `opponent_plans` — Saved tactical plans per opponent

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT PK | UUID |
| `team_id` | TEXT | Opponent team ID (indexed) |
| `team_name` | TEXT | Opponent team name |
| `plan_name` | TEXT | Plan label |
| `player_ids` | JSONB | `string[]` — selected opponent player IDs |
| `at_settings` | JSONB | AT configuration object |
| `saved_at` | TIMESTAMPTZ | Save time |

---

## GitHub Actions Workflows

| Workflow | File | Schedule | Purpose |
|----------|------|----------|---------|
| Bot Scout | `bot_scout.yml` | Fri 4 AM UTC | Full league traversal for BOT teams |
| Bot Evaluate | `bot_evaluate.yml` | Daily 2 AM UTC | Evaluate batch of ~2,200 players |
| Scraper | `scraper.yml` | Scheduled | Full transfer market scrape |
| Market Analysis | `market_analysis.yml` | Scheduled | Generate Telegram alerts |
| Final Prices | `final_prices.yml` | Hourly | Update historical sale prices |
| Opponent Scout | `opponent_scout.yml` | Manual | Analyze specific opponents |

All workflows use `SUPABASE_URL`, `SUPABASE_KEY`, `PM_USERNAME`, `PM_PASSWORD`, and Telegram tokens stored as GitHub Secrets.

---

## Frontend Dashboard Pages

**Adding a new page:** Create `page.tsx` + `*Client.tsx`, then add nav links in BOTH the desktop `<aside>` and mobile `<header>` in `web/src/app/layout.tsx`.

**Shared TypeScript utilities and shared React components** both go in `web/src/lib/` (no `components/` directory).

| Route | Component | Data Source | Description |
|-------|-----------|-------------|-------------|
| `/` | `page.tsx` | Supabase count queries | Stat cards, navigation |
| `/players` | `PlayersClient.tsx` | `players` table | All player profiles, sortable |
| `/transfers` | `TransfersClient.tsx` | `transfer_listings` table | Market with ROI calculator |
| `/bot-opportunities` | `BotOpportunitiesClient.tsx` | `bot_opportunities` table | BOT targets, filtering/sorting/pagination |
| `/squad` | `SquadClient.tsx` | `my_squad` + `players` + `saved_lineups` API | Squad builder with formation slots + saved lineups |
| `/opponent-scout` | `OpponentScoutClient.tsx` | `opponent_plans` + `my_squad` | AT matchup analysis vs opponents |
| `/fixtures` | `FixturesClient.tsx` | `fixtures` | Upcoming fixtures |

All data is fetched server-side in `page.tsx` files and passed to `*Client.tsx` components for client-side interactivity (filtering, sorting, pagination).

---

## Coding Conventions

### Python

- **Config:** Always import from `src.config` — never hardcode credentials or use `os.getenv()` directly outside `config.py`.
- **Logging:** Use the logger from `src.core.logger` — never use `print()` in scraper or service code.
- **Type coercion:** Before any Supabase upsert, convert NumPy types to native Python (`int()`, `float()`, `str()`) — the Supabase client rejects `np.int64` etc.
- **Batch size:** Upsert in batches of 500 rows maximum to stay within Supabase free-tier limits.
- **Browser automation:** Use `BaseScraper` from `src.scrapers.base` — it handles Playwright setup and login. Never create a new Playwright instance from scratch.
- **Currency parsing:** Use `clean_currency()` from `src.core.utils` to parse formatted money strings.
- **Deadline parsing:** Use `parse_deadline()` from `src.core.utils` for auction deadline strings.

### TypeScript / Next.js

- **App Router only** — all pages use `app/` directory (no `pages/`).
- **Server/Client split:** Fetch data in server components (`page.tsx`), pass to `*Client.tsx` for interactivity.
- **Supabase client:** Import from `@/lib/supabase` — do not create new clients inline.
- **Styling:** Tailwind CSS utility classes only — no separate CSS files. Follow existing glassmorphism patterns (backdrop-blur, bg-white/10, etc.).
- **Icons:** Lucide React only (`import { IconName } from 'lucide-react'`).
- **API routes:** CRUD operations live in `web/src/app/api/<resource>/route.ts` (collection) and `web/src/app/api/<resource>/[id]/route.ts` (item). Use `SUPABASE_KEY` (service role) server-side — not the anon browser client.

---

## Common Tasks

### Add a new Python scraper

1. Create `src/scrapers/your_scraper.py` extending `BaseScraper`
2. Add a new entry script `main_your_scraper.py` at root
3. Add any new DB operations to `src/services/supabase_client.py`
4. If it needs a new table, add a SQL schema to `db_schemas/`
5. Add a GitHub Actions workflow in `.github/workflows/` if it should run on a schedule

### Extend an existing Supabase table

1. Write an `ALTER TABLE` statement and run it in the Supabase SQL editor
2. Update the corresponding schema file in `db_schemas/` for reference
3. Update `SupabaseManager` methods in `src/services/supabase_client.py` as needed
4. Update any TypeScript types or Supabase queries in the frontend if the table is displayed

### Add a new dashboard page

1. Create `web/src/app/your-page/page.tsx` — fetch data server-side from Supabase
2. Create `web/src/app/your-page/YourPageClient.tsx` — client component for interactivity
3. Add navigation link in the root layout or home page
4. Follow the existing pattern: server page fetches → passes props to client component

---

## Key Metrics & Business Logic

| Metric | Formula | Purpose |
|--------|---------|---------|
| ROI | `(estimated_value - asking_price) / asking_price` | Primary sort for transfer deals |
| Value Diff | `estimated_value - asking_price` | Absolute profit potential |
| Forecast Sell | `(estimated_value / 2) * 0.8` | Conservative resale estimate |
| Forecast Profit | `forecast_sell - asking_price` | Expected net gain |
| Profit Margin | `(value_diff / asking_price) * 100` | BOT opportunity ranking |
| Sale-to-Bid Ratio | `last_transfer_price / bids_avg` | Historical overpay indicator |

**AI Recommendation filters** (in `ai_recommendation.py`):
- Budget: asking price ≤ 30M AND ≤ available team funds
- Profitability: forecast profit > 0
- Timing: auction deadline within 12 hours
- Output: top 15 opportunities sorted by forecast profit

**BOT player quality filter** (in `bot_team.py`):
- Accepted quality tiers: "Excellent", "Formidable", "World Class"
- Players below these tiers are skipped during evaluation

---

## Gotchas & Bugs to Avoid

**Supabase PostgREST JOIN fails silently when FK column ≠ PK name:** If the FK column (`player_id`) differs from the PK (`id`), the implicit join returns empty results with no error. Fix: two separate queries, merge with a JS `Map`.

**BeautifulSoup `get_text(strip=True)` collapses inter-tag whitespace:** `<b>D</b> RL` → `"DRL"`. Always use `get_text(separator=" ", strip=True)` when tags and adjacent text must be space-separated.

**Position group detection must use `startsWith()`:** Positions scraped from plantel.asp may lack spaces (`"DRL"` not `"D RL"`). Use `p.startsWith("D")` not `split(" ")[0] === "D"`.

**`parse_deadline()` — PManager deadlines are UTC (GMT+0):** PManager displays deadline strings (e.g. `"Today at 14:30"`) in UTC, not local time. The scraper saves them as-is to the DB. The frontend `formatDeadline()` treats stored values as UTC (appends `Z`) and converts to Bangkok time (UTC+7) for display. Do NOT append `+07:00` to stored deadline strings — that would shift the displayed time by −7 hours.

**AT matchup `result` field is ternary, not boolean:** `computeATMatchup()` returns `result: true | false | null` (null = no data) and `partial: boolean`. Never coerce to bool — `partial` rows display differently from wins/losses.

**`config.validate()` requires Supabase creds:** Scripts that only scrape + send Telegram (no DB writes) must call `config.validate_telegram()` plus manually check `PM_USERNAME`/`PM_PASSWORD` instead. Never call `config.validate()` in a Supabase-free script.

**`src/services/gsheets.py`:** A Google Sheets integration (`SheetManager`) exists but is not part of the main scraper pipeline. Not imported by any entry script — only used if Google Sheets export is needed. Omitted from the project structure above intentionally (optional / legacy).

**ruff lint failures to watch for:**
- F401 — unused imports (e.g. `from typing import Any` left in after refactoring)
- I001 — import block must be sorted: stdlib → third-party → local, with blank lines between groups
- W291/W293 — trailing whitespace or whitespace-only blank lines
