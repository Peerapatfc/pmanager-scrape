# Business Requirement Document (BRD)
**Project Name:** PManager Open Market Scraper & Analyzer
**Date:** 2026-01-13
**Version:** 1.0

## 1. Executive Summary
The PManager Scraper project aims to automate the scouting and trading process for the PManager online football management game. By leveraging automation, the user seeks to gain a competitive advantage through data-driven transfer market decisions, identifying undervalued players, and capitalizing on market inefficiencies (flipping).

## 2. Business Problem
*   **Manual Scouting is Inefficient:** The transfer market contains thousands of players. Manually checking each player's estimated value vs. asking price is time-consuming.
*   **Missed Opportunities:** Valuable players with low deadlines often go unnoticed due to the volume of listings.
*   **Lack of Historical Data:** It is difficult to know the "real" market price of a player without tracking historical sale prices versus scout estimates.

## 3. Business Goals
*   **Automate Data Collection:** Scrape the transfer market 24/7 (or on schedule) to build a comprehensive database of available players.
*   **Maximize ROI:** Identify players selling for significantly less than their estimated value to "flip" for profit.
*   **Real-Time Alerts:** Receive immediate notifications (Telegram) for high-potential trades ending soon.
*   **Market Intelligence:** Track final sale prices to understand the actual market value ratio compared to scout estimates.

## 4. Stakeholders
*   **Primary User:** The Manager (User) who runs the script and manages the football team.

## 5. Scope
*   **In-Scope:**
    *   Scraping active transfer listings.
    *   Extracting player attributes, asking price, and scout estimates.
    *   Calculating financial metrics (ROI, Profit).
    *   Scraping historical transfer data (final sale price).
    *   Google Sheets integration for data persistence.
    *   Telegram integration for alerts.
*   **Out-of-Scope:**
    *   Automated bidding (The bot does *not* place bids, only alerts).
    *   Game-playing automation (tactics, training).
