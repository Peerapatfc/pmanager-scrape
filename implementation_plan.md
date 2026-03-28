# Scrape BOT Team Players and Create Frontend Dashboard

This plan outlines the steps to build a specialized scraper that targets high-quality players from "BOT" teams listed with asking prices below their estimated transfer values, and to construct a modern web frontend to display those opportunities.

## Background Context
The existing scraper framework in `d:\Work\Meaw - Q\Scraper\pmanager-scrape` handles logins, navigation, and data extraction from `pmanager.org`. This tool will be extended to filter for players specifically from "BOT" teams. A new frontend application will be developed to visualize this data from Supabase.

## User Review Required

> [!IMPORTANT]
> Please review the open questions below to ensure the scraper and frontend correctly align with your Pmanager strategy. Once you provide the answers, I can begin execution.

## Proposed Changes

## Proposed Changes

### 1. Scraper Module (`pmanager-scrape`)

We will create a new bot scraping script that leverages the standings pages rather than the global transfer list.

#### [NEW] src/scrapers/bot_team.py
- **League Navigation**: Iterate through available countries and divisions (e.g., `classificacao.asp`).
- **Bot Identification**: Parse the league standings table. Teams with **bold text** are human managers; teams with **normal text** are BOT teams.
- **Roster Extraction**: For each BOT team found, visit their team page and extract all player IDs on their roster.
- **Player Evaluation**: For each player ID:
  - Visit the negotiation page (`comprar_jog_lista.asp`) to extract `asking_price` and `estimated_value`.
  - Visit the profile page (`ver_jogador.asp`) to extract `Quality`.
- **Filtering Logic**: 
  - `asking_price > 0` AND `asking_price < estimated_value`
  - `Quality` is strictly better than "Very Good" (e.g., "Excellent", "Exceptional", "World Class").

#### [NEW] main_bot_scout.py
- The command-line entry point to orchestrate `src/scrapers/bot_team.py` and subsequently push the matched "Bot Opportunities" into Supabase.

#### [MODIFY] src/services/supabase_client.py
- Optionally add a new method `upsert_bot_opportunities` if we want a separate table (or use the existing `transfer_listings` with a `is_bot_team` flag).

---

### 2. Frontend Application (`Pmanager` workspace)

Create a Vite + React web application with a rich aesthetic to visualize the bot team targets in real-time.

#### [NEW] d:\Work\Meaw - Q\Pmanager\frontend (Directory)
- Initialize a new Vite-React project.
- Integrate `@supabase/supabase-js`.
- Construct a modern, visually stunning dashboard (using CSS Variables, Glassmorphism, and dynamic hover animations).
- Key views:
  - Data table/grid displaying Player Name, Age, Position, Quality, BOT Team Name, Estimated Value, Asking Price, and Profit Margin.
  - Links directly to the player's Pmanager transfer page.

## Open Questions

> [!WARNING]
> I need your final confirmation on a couple of implementation specifics before I start coding.

1. **Quality Metric:** You specified quality "more than very good". Does this mean picking only "Excellent", "Exceptional", and "World Class"? What are the exact terms used in-game that are higher than "Very Good"? 
2. **Supabase Structure:** Should we add a new column like `is_bot_team` to your existing `transfer_listings` table, or do you want an entirely new table (e.g., `bot_opportunities`) just for these bot players?
3. **Execution Scope:** Do you want the scraper to loop through **all** countries and divisions automatically, or should it take a specific country code as an argument to save time?

## Verification Plan

### Automated Tests
- Run `main_bot_scout.py` locally and verify via logging that the filtering logic for Price, Quality, and Bot Team accurately matches the player's details on the website.
- Ensure Supabase successfully ingests the new or modified records without disrupting the generic `main_all_transfer.py` logic.

### Manual Verification
- Launch the Frontend dev server.
- Verify that data successfully loads from Supabase.
- Confirm the UI matches a premium design aesthetic with fully functional sorting for Profit/Quality.
- Validate the "Go to Player" links accurately route to `pmanager.org`.
