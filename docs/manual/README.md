# PManager Official Game Manual

Complete reference manual for [PManager.org](https://pmanager.org) — a browser-based football management game. This manual covers all game mechanics, rules, and systems relevant to player management, transfers, finances, and competition.

> All currency values referenced in this manual are in **EURO**.

---

## Table of Contents

| # | Section | Topics |
|---|---------|--------|
| 1 | [Introduction](sections/section_01.md) | What is PManager, game overview |
| 2 | [Computer Requirements](sections/section_02.md) | Browser, Flash, JavaScript requirements |
| 3 | [Registration, Activation & Team Selection](sections/section_03.md) | Account creation, validation, team assignment |
| 4 | [User Interface](sections/section_04.md) | Navigation, menus, layout |
| 5 | [First Steps](sections/section_05.md) | Getting started as a new manager |
| 6 | [Strategies](sections/section_06.md) | Game strategy and approach |
| 7 | [Players](sections/section_07.md) | Player attributes, quality tiers, skills |
| 8 | [Training System](sections/section_08.md) | How training works, skill development |
| 9 | [The Squad & 2nd/3rd Teams](sections/section_09.md) | Squad management, multi-team setup |
| 10 | [Academy and Youth Players](sections/section_10.md) | Youth system, academy development |
| 11 | [Transfers](sections/section_11.md) | Transfer market, buying, selling, auctions |
| 12 | [Stadium](sections/section_12.md) | Stadium upgrades, capacity |
| 13 | [Tactics](sections/section_13.md) | Formations, tactical setups |
| 14 | [The Match](sections/section_14.md) | How matches are simulated |
| 15 | [Economy & Sponsors](sections/section_15.md) | Finances, income, sponsor contracts |
| 16 | [Team Staff](sections/section_16.md) | Coaches, physios, scouts |
| 17 | [Teams](sections/section_17.md) | Team overview and management |
| 18 | [The Manager & Job Center](sections/section_18.md) | Manager profile, job market |
| 19 | [Inactivity](sections/section_19.md) | What happens when managers go inactive |
| 20 | [Series System](sections/section_20.md) | League divisions and promotion/relegation |
| 21 | [Season Prizes](sections/section_21.md) | End-of-season rewards |
| 22 | [National Cup](sections/section_22.md) | Domestic cup competition |
| 23 | [Friendly Matches & Instant Matches](sections/section_23.md) | Friendlies and instant match feature |
| 24 | [PM Cups](sections/section_24.md) | Special cup competitions |
| 25 | [International Team Competitions](sections/section_25.md) | Cross-country tournaments |
| 26 | [National Federations & National Teams](sections/section_26.md) | Federation system, national team management |
| 27 | [PM Coins & PM Fan](sections/section_27.md) | Premium currency and fan subscription |
| 28 | [Community](sections/section_28.md) | Forums, messaging, social features |
| 29 | [Behavior](sections/section_29.md) | Code of conduct, fair play rules |
| 30 | [Manager's Certificate & Mentorship System](sections/section_30.md) | Certification exams, mentorship program |
| 31 | [PMDD](sections/section_31.md) | PM Daily Digest |
| 32 | [Game Administration](sections/section_32.md) | Admin tools, rule enforcement |
| 33 | [PManager Week](sections/section_33.md) | Weekly game events |
| 34 | [Denominations](sections/section_34.md) | Glossary of game terms and definitions |

---

## Key Sections for Scraper Development

These sections are most directly relevant to understanding the data scraped by **pmanager-scrape**:

| Section | Why It Matters |
|---------|---------------|
| [7 — Players](sections/section_07.md) | Defines quality tiers (World Class, Excellent, Formidable, etc.), positions, and skill attributes extracted by scrapers |
| [11 — Transfers](sections/section_11.md) | Explains the auction system, estimated value, asking price, bidding — the basis for ROI/profit calculations |
| [15 — Economy & Sponsors](sections/section_15.md) | Context for `available_funds` and financial data tracked in `team_info` |
| [17 — Teams](sections/section_17.md) | BOT (computer-controlled) teams — the target of `main_bot_scout.py` |
| [20 — Series System](sections/section_20.md) | League tree structure traversed by `BotTeamScraper` to discover BOT teams |
| [34 — Denominations](sections/section_34.md) | Glossary — useful for interpreting scraped field names and values |

---

## Related Project Files

| File | Description |
|------|-------------|
| [../../CLAUDE.md](../../CLAUDE.md) | Claude Code project guide — architecture, commands, conventions |
| [../pmanager_rules.md](../pmanager_rules.md) | Extracted game rules reference |
| [../pmanager_rules.json](../pmanager_rules.json) | Game rules in structured JSON format |
| [../BRD.md](../BRD.md) | Business Requirements Document |
| [../PRD.md](../PRD.md) | Product Requirements Document |
| [../SDD.md](../SDD.md) | System Design Document |
| [../TSD.md](../TSD.md) | Technical Specifications Document |
