# Product Requirement Document (PRD)
**Project Name:** PManager Open Market Scraper & Analyzer
**Version:** 1.0

## 1. Introduction
This document outlines the functional and non-functional requirements for the PManager Scraper tool suite.

## 2. Features

### 2.1 Transfer Market Scraping
*   **Search Scenarios:** The system must support scraping specific market segments:
    *   High Quality Players (Quality > 7)
    *   Low Price Deals (Price < 20,000)
    *   Young Potential (Age < 20, High Potential)
*   **Data Extraction:** Must extract: ID, Name, Age, Position, Attributes, Estimated Value, Asking Price, Deadline.

### 2.2 Financial Analysis
*   **ROI Calculation:** Calculate Return on Investment `((Estimated - BuyPrice) / BuyPrice) * 100`.
*   **Forecast Sell Price:** Estimate sale price using the formula `(Estimated Value / 2) * 0.8`.
*   **Value Diff:** Calculate absolute profit potential.

### 2.3 Historical Data Tracking
*   **Sale Price Tracking:** The system must visit the history page of players after their auction ends to record the `last_transfer_price`.
*   **Sale/Bid Ratio:** Calculate `last_transfer_price / bids_avg` to benchmark the market heat.

### 2.4 Data Persistence
*   **Google Sheets (All Players):** A master database acting as a historical record. Must use "Upsert" logic (Update if exists, Insert if new). Columns must include `sale_to_bid_ratio` and `bids_avg`.
*   **Google Sheets (Transfer Info):** A view of current active market opportunities.

### 2.5 Alerting
*   **Telegram Bot:** Send notifications for players meeting criteria:
    *   High calculated profit.
    *   Deadline within 12 hours.
    *   Buy price within team budget.

## 3. User Flows
1.  **Daily Scrape:** User/Cron runs `main_all_transfer.py` -> Scrapes Market -> Updates Sheets.
2.  **Hourly Update:** Cron runs `update_final_prices.py` -> Checks expired auctions -> Scrapes Final Price -> Updates Sheets.
3.  **Decision:** User checks Telegram/Sheets -> Logs into Game -> Places Bid.

## 4. Requirements
*   **Performance:** Scraper should handle ~150 pages of results without crashing.
*   **Reliability:** Must handle login sessions and reconnect if dropped.
*   **Environment:** Run on Windows Local and GitHub Actions (Ubuntu).
