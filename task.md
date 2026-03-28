# Bot Team Scraper & Dashboard Tasks

- `[x]` **Phase 1: Database Setup**
  - `[x]` Create `bot_opportunities.sql` schema so the user can easily run it in their Supabase dashboard to create the new table.

- `[x]` **Phase 2: Scraper Implementation (`pmanager-scrape`)**
  - `[x]` Create `src/scrapers/bot_team.py` with logic to loop through all countries and leagues in `classificacao.asp`.
  - `[x]` Implement BOT team detection on `classificacao.asp` (`<b>` tags = Human, Normal text = BOT).
  - `[x]` Extract the team's roster from `ver_equipa.asp?equipa={ID}&vjog=1` and check `Quality` directly from the roster table.
  - `[x]` If `Quality in ['Excellent', 'Formidable', 'World Class']`, navigate to `comprar_jog_lista.asp` to get `asking_price` and `estimated_value`.
  - `[x]` Apply filter logic: `asking_price < estimated_value` and save targets.
  
- `[x]` **Phase 3: Integration & Main Script**
  - `[x]` Update `src/services/supabase_client.py` to include `upsert_bot_opportunities`.
  - `[x]` Create `main_bot_scout.py` to orchestrate scraping and database insertion.
  - `[x]` Verify script functionally extracts targets and iterates properly using 'Next' arrows.

- `[x]` **Phase 4: Frontend Development**
  - `[x]` Initialize Next.js project in `web` folder.
  - `[x]` Set up Tailwind CSS for a premium aesthetic (Glassmorphism, dark mode).
  - `[x]` Integrate `@supabase/supabase-js`.
  - `[x]` Build the DataTable / Grid UI to display players and link nicely to their PManager URLs.
  - `[x]` Run frontend locally to ensure data loads and the UI is robust.
