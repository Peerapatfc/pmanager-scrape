# Business Requirements Document (BRD)
## PManager Scraper & Analyzer

---

## 1. Executive Summary

**Project Name:** PManager Scraper & Analyzer  
**Version:** 1.0  
**Date:** January 12, 2026  

This project automates player scouting and transfer market analysis for the online football manager game [PManager.org](https://www.pmanager.org). It enables managers to identify profitable transfer opportunities through data-driven insights and real-time notifications.

---

## 2. Business Objectives

| Objective | Description |
|-----------|-------------|
| **Time Savings** | Reduce manual scouting time from hours to minutes |
| **Profit Maximization** | Identify undervalued players with high ROI potential |
| **Competitive Advantage** | React faster to market opportunities with real-time alerts |
| **Data-Driven Decisions** | Replace intuition with algorithmic analysis |

---

## 3. Stakeholders

| Role | Responsibilities |
|------|------------------|
| **Manager (User)** | Configures parameters, reviews recommendations, executes transfers |
| **System (Automation)** | Scrapes data, calculates metrics, sends notifications |

---

## 4. Business Requirements

### 4.1 Core Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| BR-001 | System must scrape transfer market data from PManager.org | High |
| BR-002 | System must calculate financial metrics (ROI, Value Diff) | High |
| BR-003 | System must filter players by budget and profitability | High |
| BR-004 | System must send notifications for top opportunities | High |
| BR-005 | System must store player data for historical tracking | Medium |
| BR-006 | System must run automatically on a schedule | Medium |

### 4.2 User Requirements

| ID | Requirement | Description |
|----|-------------|-------------|
| UR-001 | **Budget Filtering** | Only show players affordable within current funds |
| UR-002 | **Deadline Awareness** | Prioritize players with auctions ending within 12 hours |
| UR-003 | **Profit Threshold** | Only recommend players with positive forecast profit |
| UR-004 | **Opponent Scouting** | Check if opponent players are already on watchlist |
| UR-005 | **Mobile Notifications** | Receive Telegram alerts for quick action |

---

## 5. Success Criteria

| Metric | Target |
|--------|--------|
| **Scraping Accuracy** | 95%+ data extraction success rate |
| **Notification Latency** | < 5 minutes from scrape to alert |
| **ROI Prediction** | 70%+ of recommendations result in profitable trades |
| **System Uptime** | 99% availability for scheduled runs |

---

## 6. Constraints

| Type | Constraint |
|------|------------|
| **Technical** | Dependent on PManager.org website structure (HTML changes may break scraper) |
| **Rate Limiting** | Must avoid aggressive scraping to prevent IP blocking |
| **Authentication** | Requires valid PManager.org credentials |

---

## 7. Assumptions

1. PManager.org website structure remains relatively stable
2. User has valid Google Cloud service account for Sheets API
3. User has active Telegram bot for notifications
4. Scheduled runs via GitHub Actions or local cron
