# Planetarium Manager Scraper

A web scraper for finding high-value players on the Planetarium Manager transfer list with automated Google Sheets integration.

## Features

- **Automated Authentication**: Logs into the game securely.
- **Advanced Filtering**: Finds players with strict criteria.
- **Deep Extraction**: Visits individual negotiation pages to extract detailed attributes.
- **Dynamic Skill Extraction**: Automatically scrapes all skills (Primary, Secondary, Physical, Tertiary) for any position.
- **Opponent Scout**: Scrapes entire squads given a team ID.
- **Google Sheets Integration**: Upserts data (updates existing, adds new) to specific tabs.
- **Telegram Bot Control**: Trigger scrapers remotely via Telegram commands.
- **GitHub Actions**: Automated scheduling and manual dispatch support.

## Setup

### Local Development

1. **Install Python 3.x**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. **Configure Credentials**:
   - Rename `.env.example` to `.env`
   - Add your details:
     ```
     PM_USERNAME=...
     PM_PASSWORD=...
     TELEGRAM_BOT_TOKEN=...
     SCOUT_BOT_TOKEN=... (For dedicated scout bot)
     TELEGRAM_CHAT_ID=...
     GEMINI_API_KEY=...
     GITHUB_TOKEN=... (For triggering workflows)
     GITHUB_REPO=Peerapatfc/pmanager-scrape
     ```
4. **Google Sheets Setup**:
   - Place `credentials.json` in the root.

### GitHub Actions (Automated)

1. **Secrets Needed**: `PM_USERNAME`, `PM_PASSWORD`, `GOOGLE_CREDENTIALS_JSON`, `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
2. **Schedule**: Runs daily at 7:30 AM/PM Thailand.

## Usage

### 🕵️‍♂️ Scrapers

**1. Low Price Scraper** (Targets < 20k)
```bash
python main_low_price.py
```

**2. High Quality Scraper** (Targets Quality > 7)
```bash
python main_high_quality.py
```

**3. Young Potential Scraper** (Targets Age < 20, Potential > Good)
```bash
python main_young_potential.py
```

**4. Team Info Scraper** (Extracts Finances/Stadium)
```bash
python main_team_info.py
```

**5. All Transfer Scraper** (Deep Scan of "All" list)
```bash
python main_all_transfer.py
```

**6. Opponent Scout** (Scrape specific team)
```bash
python main_opponent_scout.py "https://www.pmanager.org/ver_equipa.asp?equipa=35126"
# OR
python main_opponent_scout.py 35126
```

### 🤖 Telegram Bots

**General Bot** (`telegram_bot.py`)
- Responds to `/scout <target>` by triggering the GitHub Action.

**Scout Bot** (`telegram_scout_bot.py`)
- Dedicated bot using `SCOUT_BOT_TOKEN`.
- Listens for `/scout` or raw URLs.
- Triggers `opponent_scout.yml` workflow.

## Output

Results are uploaded to **Google Sheets**:
- **High Quality**: "High Quality" tab
- **Low Price**: "Low Price" tab
- **Young Potential**: "Young Potential" tab
- **All Players**: "All Players" tab (Upsert Logic: Preserves history)
- **Team Info**: "Team Info" tab

## License

Private use only.
