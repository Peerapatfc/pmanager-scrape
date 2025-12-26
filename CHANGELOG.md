# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.2.0] - 2025-12-27

### Added
- **GitHub Actions Workflow**: Automated daily scraping at 7:30 AM Thailand time
  - Supports manual trigger with scraper type selection
  - Auto-installs Playwright browsers in CI environment
  - Uploads CSV results as artifacts (30-day retention)
- **Headless Mode Detection**: Scrapers automatically run in headless mode when in CI environment
- Added `gspread` and `google-auth` to requirements.txt

### Changed
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
