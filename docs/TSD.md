# Technical Specification Document (TSD)
## PManager Scraper & Analyzer

---

## 1. Technical Overview

| Aspect | Specification |
|--------|---------------|
| **Language** | Python 3.9+ |
| **Browser Engine** | Playwright (Chromium) |
| **Data Format** | JSON, CSV, Google Sheets |
| **Hosting** | Local machine / GitHub Actions |
| **Timezone** | Thailand (UTC+7) |

---

## 2. System Requirements

### 2.1 Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 2 GB | 4 GB |
| Storage | 100 MB | 500 MB |
| Network | 1 Mbps | 10 Mbps |

### 2.2 Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.9+ | Runtime |
| Chromium | Latest (via Playwright) | Browser automation |
| pip | Latest | Package management |

---

## 3. Installation Procedure

### 3.1 Local Setup

```bash
# 1. Clone repository
git clone https://github.com/Peerapatfc/pmanager-scrape.git
cd pmanager-scrape

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Create environment file
cp .env.example .env
# Edit .env with your credentials

# 5. Add Google credentials
# Place credentials.json in project root
```

### 3.2 GitHub Actions Setup

| Secret Name | Value |
|-------------|-------|
| `PM_USERNAME` | PManager username |
| `PM_PASSWORD` | PManager password |
| `GOOGLE_CREDENTIALS` | Base64-encoded credentials.json |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Target chat ID |

---

## 4. API Specifications

### 4.1 PManager.org Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/default.asp` | GET | Login page |
| `/procurar.asp` | GET | Player search with filters |
| `/comprar_jog_lista.asp?jg_id={id}` | GET | Player negotiation page |
| `/ver_jogador.asp?jog_id={id}` | GET | Player profile page |
| `/ver_equipa.asp?equipa={id}` | GET | Team roster page |
| `/marcos_jog.asp?jog_id={id}` | GET | Player transfer history |

### 4.2 Google Sheets API

**Scopes Required:**
- `https://www.googleapis.com/auth/spreadsheets`
- `https://www.googleapis.com/auth/drive`

**Operations:**

| Operation | Method | Description |
|-----------|--------|-------------|
| Read all records | `worksheet.get_all_records()` | Fetch existing data |
| Clear sheet | `worksheet.clear()` | Remove all content |
| Update cells | `worksheet.update(data, range)` | Write data batch |
| Resize | `worksheet.resize(rows)` | Adjust row count |

### 4.3 Telegram Bot API

**Base URL:** `https://api.telegram.org/bot{TOKEN}`

| Endpoint | Purpose |
|----------|---------|
| `/sendMessage` | Send text notification |
| `/getUpdates` | Poll for incoming commands |

**Send Message Payload:**
```json
{
    "chat_id": "-100123456789",
    "text": "Message content",
    "parse_mode": "Markdown"
}
```

---

## 5. Data Processing Specifications

### 5.1 Scraping Rules

| Rule | Value | Rationale |
|------|-------|-----------|
| Max pages per scenario | 150 | Prevent infinite loops |
| Wait timeout | 3000ms | Balance speed vs reliability |
| Rate limiting | None explicit | Playwright handles naturally |

### 5.2 Value Calculation Formulas

```python
# Buy Price: Best estimate of actual purchase cost
buy_price = asking_price if asking_price > 0 else bids_avg

# Value Difference: Raw profit margin
value_diff = estimated_value - buy_price

# ROI: Percentage return
roi = (value_diff / buy_price) * 100  # if buy_price > 0

# Forecast Sell: Conservative profit estimate
# Based on: Sell at 80% of half the estimated value
forecast_sell = (estimated_value / 2 * 0.8) - buy_price
```

### 5.3 Time Zone Conversion

```python
# PManager displays times in UTC
utc_now = datetime.utcnow()

# Convert to Thailand Time (UTC+7)
thailand_time = utc_now + timedelta(hours=7)

# Deadline parsing: "Today at 18:00" -> datetime
if "today" in deadline_str:
    deadline = utc_now.replace(hour=h, minute=m) + timedelta(hours=7)
elif "tomorrow" in deadline_str:
    deadline = (utc_now + timedelta(days=1)).replace(hour=h, minute=m) + timedelta(hours=7)
```

---

## 6. Security Specifications

### 6.1 Credential Management

| Credential | Storage Method | Access Pattern |
|------------|----------------|----------------|
| PManager login | `.env` file (local) / GitHub Secrets | Load at runtime |
| Google Service Account | `credentials.json` (local) / Base64 secret | Load from file |
| Telegram tokens | `.env` file / GitHub Secrets | Load at runtime |

### 6.2 Gitignore Rules

```gitignore
.env
credentials.json
*.csv
team_info.json
__pycache__/
```

### 6.3 Security Practices

- ✅ Credentials never committed to repository
- ✅ Service account has minimal required permissions
- ✅ Telegram bot can restrict to specific chat IDs
- ⚠️ No rate limiting implemented (relies on Playwright pacing)

---

## 7. Search Scenarios Configuration

### 7.1 Default Scenarios

| Name | URL Parameters | Purpose |
|------|----------------|---------|
| **High Quality** | `qual_op=>` `qual=7` | Players with quality > 7 |
| **Low Price** | `pre_op=<=` `pre=20000` | Budget players under 20k |
| **Young Potential** | `idd_op=<` `idd=20` `prog_op=>` `prog=6` | Young players with potential > 6 |
| **Recent Listings** | Default URL (no filters) | All currently listed players |

### 7.2 URL Parameter Reference

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| `pos` | Position filter | 0=All, 1=GK, 2=DEF, etc. |
| `idd` | Age | Any, numeric |
| `idd_op` | Age operator | `<`, `>`, `<=`, `>=` |
| `pre` | Max price | Any, numeric |
| `qual` | Quality rating | 1-10 |
| `prog` | Potential rating | 1-10 |

---

## 8. GitHub Actions Workflow

### 8.1 Scheduled Run (Cron)

```yaml
name: Scheduled Scrape

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Create credentials
        run: echo "${{ secrets.GOOGLE_CREDENTIALS }}" | base64 -d > credentials.json
      
      - name: Run scraper
        env:
          PM_USERNAME: ${{ secrets.PM_USERNAME }}
          PM_PASSWORD: ${{ secrets.PM_PASSWORD }}
          CI: true
        run: python main_all_transfer.py
      
      - name: Run recommendations
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python ai_recommendation.py
```

### 8.2 On-Demand Opponent Scout

```yaml
name: Opponent Scout

on:
  workflow_dispatch:
    inputs:
      scout_target:
        description: 'Team ID or URL to scout'
        required: true

jobs:
  scout:
    runs-on: ubuntu-latest
    steps:
      # ... similar setup steps
      - name: Run scout
        run: python main_opponent_scout.py "${{ github.event.inputs.scout_target }}"
```

---

## 9. Monitoring & Logging

### 9.1 Console Output Format

```
Starting All Transfer Players Scraper...
Logging in as user123...
Login submitted.

Running 4 search scenarios...

--- Scenario: High Quality ---
Navigating to Custom Search: https://...
Scraping page 1...
  Found 25 players on page 1.
...

Total Unique Players found from all scenarios: 150
Extracting details for 150 players...
[50/150] Scraping ID: 123456...

Successfully scraped 150 players. Calculating values...
Saved results to transfer_targets_all.csv
Uploading to 'All Players' sheet (Attributes Only)...
✓ Uploaded 150 rows (Merged) to Google Sheets: All Players
```

### 9.2 Error Logging

| Error Type | Log Format |
|------------|------------|
| Scrape failure | `Error scraping {player_id}: {exception}` |
| Login failure | `Login failed: {exception}` + raise |
| Sheet upload failure | `✗ Failed to upload to Google Sheets: {exception}` |
| Telegram failure | `Failed to send: {response.text}` |

---

## 10. Performance Metrics

### 10.1 Typical Execution Times

| Operation | Duration |
|-----------|----------|
| Login | ~3 seconds |
| Search (per page) | ~2 seconds |
| Player details (per player) | ~4 seconds |
| Sheet upload | ~5 seconds |
| Full run (150 players) | ~15-20 minutes |

### 10.2 Resource Usage

| Resource | Typical Usage |
|----------|---------------|
| Memory (browser) | ~300-500 MB |
| Network (per run) | ~50-100 MB |
| GitHub Actions minutes | ~20 minutes/run |

---

## 11. Troubleshooting Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| Login fails | Changed PManager UI | Update selectors in `login()` |
| Empty results | No matching players | Adjust search filters |
| Sheet API 403 | Expired credentials | Regenerate service account |
| Telegram not sending | Invalid chat ID | Verify bot is in chat |
| Playwright timeout | Slow network | Increase timeout values |
| Deadline parse error | New date format | Update `parse_deadline()` regex |

---

## 12. Future Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| **Rate limiting** | Add delays between requests | Medium |
| **Error recovery** | Resume from last processed player | Medium |
| **Multi-league support** | Scrape from different leagues | Low |
| **Price history tracking** | Track price changes over time | Medium |
| **Machine learning** | Predict player value trends | Low |
| **Web dashboard** | Visual interface for monitoring | Low |
