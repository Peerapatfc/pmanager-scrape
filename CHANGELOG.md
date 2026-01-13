# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.2.0] - 2026-01-13
### Added
- **Formal Documentation**: Added BRD, PRD, SDD, and TSD in `docs/` folder.
- **Hourly Price Updater**: New script `update_final_prices.py` to scrape final sale prices for expired auctions.
- **Market Ratio**: Added `sale_to_bid_ratio` column to "All Players" sheet (`Last Price / Average Bid`).
- **GitHub Action**: Added `.github/workflows/final_prices.yml` for hourly automation.

### Changed
- **Optimized Scraping**: Removed history scraping from the main loop in `scraper_all_transfer.py` to improve speed.
- **Data Persistence**: `main_all_transfer.py` now saves `bids_avg` and `deadline` to the historical "All Players" sheet.
- **Refactoring**: Moved history scraping logic to a dedicated `get_player_history` method.

## [1.1.0] - 2026-01-07
### Added
- **AI Recommendations**: `ai_recommendation.py` now includes logic for filtering high-profit trades.
- **Telegram Integration**: Added alerts for top trade signals.

## [1.0.0] - 2025-12-25
### Initial Release
- Basic scraping functionality.
- Google Sheets integration.
- `main_all_transfer.py` active.
