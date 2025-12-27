# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.2.1] - 2025-12-27

### Changed
- **Team Info Scraper**: Added `main_team_info.py` to extract team stats/financials and **upload to Google Sheets**
- **All Transfer Scraper**: Added `scraper_all_transfer.py` to scrape ALL players with dynamic skills and **upsert logic** (updates existing players, adds new ones, keeps history)
- **AI Upgrade**: AI now considers **Available Funds** from Team Info sheet to suggest affordable comparisons
- **Workflow**: Renamed `both` option to `all` and added **Team Info Scraper** to the automated schedule
- **AI Strategy**: Updated AI prompt to "Ruthless Day Trader" focusing on immediate profit flips
- **Schedule**: Updated GitHub Actions to run **twice daily** (07:30 AM & 07:30 PM Thailand Time)
- **Environment**: Added AI credential variables to `.env.example`

## [1.2.0] - 2025-12-27

### Added
- **GitHub Actions Workflow**: Automated daily scraping at 7:30 AM Thailand time
  - Supports manual trigger with scraper type selection
  - Auto-installs Playwright browsers in CI environment
  - Uploads CSV results as artifacts (30-day retention)
- **Headless Mode Detection**: Scrapers automatically run in headless mode when in CI environment
- **Last Updated Timestamp**: Added `last_updated` column to CSV and Google Sheets output
- **Young Potential Scraper**: Added new scraper for players < 20 years old with high potential (> Good)
- **AI Transfer Assistant**: Added `ai_recommendation.py` to analyze results with Google Gemini and send daily "Best Deal" picks to Telegram
- Added `.env` support for Telegram and Gemini credentials
- Added `gspread` and `google-auth` to requirements.txt

### Changed
- **Sorting Logic**: Changed result sorting from ROI to **Value Difference** (Descending)
- **Timestamp**: `last_updated` column now uses Thailand Time (UTC+7) instead of UTC
- Updated README with GitHub Actions setup instructions
- Updated README with Google Sheets integration documentation

## [1.1.0] - 2025-12-25

### Added
- **Value Diff Column**: Added `value_diff` column to both scrapers
- **ROI Calculation**: Calculate Return on Investment percentage
- **Buy Price Logic**: Uses max of asking price and bids average for accurate ROI

## [1.0.0] - 2025-12-22

### Added
- **High Quality Scraper**: New scenario for players with Quality > Very Good (7)
- **Google Sheets Integration**: Auto-upload results to Google Sheets
- Separate output files for each scraper type

## [0.2.0] - 2025-12-21

### Added
- `.gitignore` file for version control
- `.env.example` template

## [0.1.0] - 2025-12-18

### Added
- Initial release
- **Low Price Scraper**: Find players with Age < 31, Price <= 20,000
- Auto-pagination through all search results
- Deep extraction of player negotiation data
- CSV export functionality
