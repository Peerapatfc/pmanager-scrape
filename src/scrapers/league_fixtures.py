"""
Scraper for league fixture lists and AT match reports.

Produces records for the league_match_results table used by AT Trends.

Usage::

    with LeagueFixturesScraper() as scraper:
        scraper.login(username, password)
        fixtures = scraper.get_season_fixtures(season=99)
        report   = scraper.get_match_report("19501929")
"""

from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.scrapers.base import BaseScraper

# ── Stats-tab label → (field_name, value_type) ───────────────────────────────
_LABEL_MAP: dict[str, tuple[str, str]] = {
    "Formation":        ("formation",       "str"),
    "Style":            ("style",           "str"),
    "Offside Trap":     ("offside_trap",     "bool"),
    "Tackling":         ("tackling",         "str"),
    "Pressing":         ("pressing",         "str"),
    "Counter Attack":   ("counter_attack",   "bool"),
    "One-on-Ones":      ("one_on_ones",      "bool"),
    "Marking":          ("marking",          "str"),
    "High Balls":       ("high_balls",       "bool"),
    "Keeping Style":    ("keeping_style",    "str"),
    "First Time Shots": ("first_time",       "bool"),
    "Long Shots":       ("long_shots",       "bool"),
    "Possession":       ("possession",       "pct"),
    "Shots":            ("shots",            "int"),
    "Shots on Goal":    ("shots_on_goal",    "int"),
    "Effectiveness":    ("effectiveness",    "pct"),
    "Short Passes (%)": ("short_passes_pct", "pct"),
    "Long Passes (%)":  ("long_passes_pct",  "pct"),
    "Fouls":            ("fouls",            "int"),
}

_AT_FIELDS = {
    "offside_trap", "tackling", "pressing", "counter_attack",
    "one_on_ones", "marking", "high_balls", "first_time", "long_shots",
}

_STATS_FIELDS = {
    "possession", "shots", "shots_on_goal", "effectiveness",
    "short_passes_pct", "long_passes_pct", "fouls",
}


def _coerce(raw: str, vtype: str) -> Any:
    raw = raw.strip()
    if vtype == "bool":
        return raw.lower() == "yes"
    if vtype == "pct":
        try:
            return float(raw.rstrip("%"))
        except ValueError:
            return None
    if vtype == "int":
        try:
            return int(raw.replace(",", ""))
        except ValueError:
            return None
    return raw


def _dmy_to_iso(dmy: str) -> str:
    """DD/MM/YYYY → YYYY-MM-DD"""
    d, m, y = dmy.split("/")
    return f"{y}-{m}-{d}"


def _safe_key(text: str) -> str:
    return re.sub(r"[^\w\-]", "_", text).strip("_") or "Unknown"


class LeagueFixturesScraper(BaseScraper):
    """Scrapes PManager league fixtures and match reports for AT trend analysis."""

    # ── Fixtures list ─────────────────────────────────────────────────────────

    def get_season_fixtures(
        self,
        season: int,
        div: int = 1,
        serie: int = 1,
        pages: int = 3,
    ) -> list[dict[str, Any]]:
        """Return all played fixtures (with game_id) for the given season.

        Only rows with a "Match Report" link are included (i.e. match already played).
        """
        fixtures: list[dict[str, Any]] = []
        for pid in range(1, pages + 1):
            url = (
                f"{self.base_url}/calendario.asp"
                f"?action=global&div={div}&serie={serie}"
                f"&epoca={season}&sg=&vf=0&pid={pid}"
            )
            logger.info("Fixtures page %d/%d ...", pid, pages)
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
            soup = BeautifulSoup(self.page.content(), "html.parser")
            batch = self._parse_fixtures_page(soup)
            fixtures.extend(batch)
            logger.info("  page %d: %d played fixtures", pid, len(batch))
        return fixtures

    def _parse_fixtures_page(self, soup: BeautifulSoup) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        current_round: int | None = None

        table = soup.find("table", class_="table_border")
        if not table:
            return results

        for row in table.find_all("tr", class_=["list1", "list2"]):
            cols = row.find_all("td")
            if len(cols) < 7:
                continue

            round_text = cols[0].get_text(strip=True)
            if round_text.isdigit():
                current_round = int(round_text)

            date_raw   = cols[1].get_text(strip=True)
            home_team  = cols[2].get_text(separator=" ", strip=True)
            away_team  = cols[4].get_text(separator=" ", strip=True)
            result_raw = cols[5].get_text(strip=True)

            report_link = cols[6].find("a")
            if not report_link:
                continue  # not yet played

            href = report_link.get("href", "")
            gid_m = re.search(r"jogo_id=(\d+)", href)
            if not gid_m:
                continue
            game_id = gid_m.group(1)

            score_m   = re.search(r"(\d+)\s*[-–]\s*(\d+)", result_raw)
            home_score = int(score_m.group(1)) if score_m else None
            away_score = int(score_m.group(2)) if score_m else None

            try:
                date_iso = _dmy_to_iso(date_raw)
            except (ValueError, IndexError):
                date_iso = None

            results.append({
                "game_id":    game_id,
                "round_num":  current_round,
                "date":       date_iso,
                "home_team":  home_team,
                "away_team":  away_team,
                "home_score": home_score,
                "away_score": away_score,
            })

        return results

    # ── Match report ──────────────────────────────────────────────────────────

    def get_match_report(self, game_id: str) -> dict[str, Any] | None:
        """Scrape relatorio.asp and return a dict ready for league_match_results upsert."""
        url = f"{self.base_url}/relatorio.asp?jogo_id={game_id}"
        logger.info("Match report game_id=%s", game_id)
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        soup = BeautifulSoup(self.page.content(), "html.parser")
        return self._parse_report(game_id, soup)

    def _parse_report(self, game_id: str, soup: BeautifulSoup) -> dict[str, Any] | None:
        # 1. JSON blob → team names, date, goals
        blob = self._extract_json_blob(soup)
        if not blob:
            logger.warning("No JSON blob found for game_id=%s", game_id)
            return None

        match     = blob.get("match", {})
        home_obj  = match.get("homeTeam", {})
        away_obj  = match.get("awayTeam", {})
        home_id   = home_obj.get("id")
        away_id   = away_obj.get("id")
        home_team = home_obj.get("name", "")
        away_team = away_obj.get("name", "")

        raw_date   = match.get("info", {}).get("date", "")
        match_date = raw_date[:10] if raw_date else None  # "2026-05-30T08:00:00Z" → "2026-05-30"

        # Count goals from events (typeId == 7)
        home_score = sum(1 for e in match.get("events", []) if e.get("typeId") == 7 and e.get("teamId") == home_id)
        away_score = sum(1 for e in match.get("events", []) if e.get("typeId") == 7 and e.get("teamId") == away_id)

        # Player id → name map for goalscorer labels
        player_map: dict[int, str] = {}
        for side_key in ("homeFormation", "awayFormation"):
            for p in match.get(side_key, {}).get("startingEleven", []):
                player_map[p["playerId"]] = p["playerName"]
            for p in match.get(side_key, {}).get("substitutions", []):
                player_map[p["playerId"]] = p["playerName"]

        goalscorers = [
            {
                "player": player_map.get(ev["playerId"], str(ev["playerId"])),
                "minute": ev.get("timeInMinutes"),
                "team":   home_team if ev.get("teamId") == home_id else away_team,
            }
            for ev in match.get("events", [])
            if ev.get("typeId") == 7
        ]

        competition = self._extract_competition(soup)

        # 2. Stats tab → formations, styles, AT flags, match stats
        home_formation = away_formation = None
        home_style     = away_style     = None
        home_at: dict[str, Any] = {}
        away_at: dict[str, Any] = {}
        stats:   dict[str, Any] = {}

        stats_div = soup.find("div", attrs={"id": "stats"})
        if stats_div:
            for row in stats_div.find_all("tr"):
                label_td = next(
                    (td for td in row.find_all("td") if "cabecalhos" in td.get("class", [])),
                    None,
                )
                if not label_td:
                    continue
                label   = label_td.get_text(strip=True)
                mapping = _LABEL_MAP.get(label)
                if not mapping:
                    continue

                field_name, vtype = mapping

                # Collect value divs from all tds (skip the label td itself)
                value_divs = [
                    div
                    for td in row.find_all("td")
                    for div in td.find_all("div", class_="comentarios")
                ]
                if len(value_divs) < 2:
                    continue

                # Strip non-breaking space before any trailing img-link text
                home_raw = value_divs[0].get_text(separator=" ", strip=True).split("\xa0")[0].strip()
                away_raw = value_divs[1].get_text(separator=" ", strip=True).split("\xa0")[0].strip()

                if field_name == "formation":
                    home_formation = home_raw
                    away_formation = away_raw
                elif field_name == "style":
                    home_style = home_raw
                    away_style = away_raw
                elif field_name in _AT_FIELDS:
                    home_at[field_name] = _coerce(home_raw, vtype)
                    away_at[field_name] = _coerce(away_raw, vtype)
                elif field_name in _STATS_FIELDS:
                    stats[f"home_{field_name}"] = _coerce(home_raw, vtype)
                    stats[f"away_{field_name}"] = _coerce(away_raw, vtype)

        return {
            "game_id":        game_id,
            "match_date":     match_date,
            "competition":    competition,
            "home_team":      home_team,
            "away_team":      away_team,
            "home_score":     home_score,
            "away_score":     away_score,
            "home_formation": home_formation,
            "away_formation": away_formation,
            "home_style":     home_style,
            "away_style":     away_style,
            "home_at":        home_at,
            "away_at":        away_at,
            "stats":          stats,
            "goalscorers":    goalscorers,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_json_blob(self, soup: BeautifulSoup) -> dict[str, Any] | None:
        """Extract the pm-match-report JSON embedded via fsReady() in a <script> tag."""
        marker = '"pm-match-report",'
        for script in soup.find_all("script"):
            text = script.string or ""
            if marker not in text:
                continue
            idx = text.index(marker) + len(marker)
            while idx < len(text) and text[idx].isspace():
                idx += 1
            try:
                data, _ = json.JSONDecoder().raw_decode(text, idx)
                return data
            except (json.JSONDecodeError, ValueError):
                logger.warning("JSON decode failed for match blob")
        return None

    def _extract_competition(self, soup: BeautifulSoup) -> str:
        """Extract competition name from the match type cell.

        Match type cell text: "League (Thailand) - Thai League , 12 round"
        """
        for td in soup.find_all("td", class_="team_players"):
            text = td.get_text(strip=True)
            if "League" in text and "round" in text:
                m = re.search(r"-\s+(.+?)\s*,", text)
                if m:
                    return m.group(1).strip()
        return "Thai League"
