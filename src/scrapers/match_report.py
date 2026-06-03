"""
Post-match report scraper.

Scrapes relatorio.asp for the full match report including formation/style/ATs
(reusing MatchPrepScraper logic), plus goals, substitutions, player ratings,
man of match, and matchday context from the global calendar.
"""

from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.scrapers.base import BaseScraper

# Cup keywords in match_type to distinguish cup from league fixtures
_CUP_KEYWORDS = ("cup", "taca", "taça", "copa", "national", "knockout")


class MatchReportScraper(BaseScraper):
    """Scrapes full post-match data from relatorio.asp and global calendars."""

    # ------------------------------------------------------------------ #
    # Main entry                                                           #
    # ------------------------------------------------------------------ #

    def scrape(self, match_id: str, fixture: dict) -> dict:
        """Scrape full post-match report for one match.

        Args:
            match_id: PManager jogo_id (numeric string).
            fixture:  Row from upcoming_fixtures table (provides match_type,
                      result, home/away team IDs, home/away team names, season,
                      match_date).

        Returns:
            Dict matching the match_reports table schema.
        """
        url = f"{self.base_url}/relatorio.asp?jogo_id={match_id}"
        logger.info("Scraping match report: %s", url)
        self.page.goto(url, wait_until="domcontentloaded")

        # Capture screenshot before navigating away (full page for all stats)
        try:
            screenshot_bytes = self.page.screenshot(full_page=True)
        except Exception as exc:
            logger.warning("Screenshot failed for match %s: %s", match_id, exc)
            screenshot_bytes = None

        soup = BeautifulSoup(self.page.content(), "html.parser")

        report = self._parse_report(soup, match_id, fixture)
        report["league_matchday_results"] = self._scrape_matchday_context(fixture)
        # Prefixed with _ — pipeline writes this to disk, never upserted to DB
        report["_screenshot_bytes"] = screenshot_bytes
        return report

    # ------------------------------------------------------------------ #
    # Match report parsing                                                 #
    # ------------------------------------------------------------------ #

    def _parse_report(self, soup: BeautifulSoup, match_id: str, fixture: dict) -> dict:
        result_str = fixture.get("result", "")
        home_score, away_score = self._parse_score(result_str)

        report: dict = {
            "match_id":       match_id,
            "home_team_id":   fixture.get("home_team_id"),
            "away_team_id":   fixture.get("away_team_id"),
            "home_score":     home_score,
            "away_score":     away_score,
            "home_formation": None,
            "away_formation": None,
            "home_style":     None,
            "away_style":     None,
            "home_at_settings": {},
            "away_at_settings": {},
            "goalscorers":    [],
            "substitutions":  [],
            "player_ratings": {},
            "man_of_match":   None,
            "commentary":     "",
        }

        # Override team IDs if discoverable from page links
        page_home, page_away = self._extract_team_ids(soup)
        if page_home:
            report["home_team_id"] = page_home
        if page_away:
            report["away_team_id"] = page_away

        # Formations, styles, AT settings
        self._parse_stats_table(soup, report)

        # Commentary block (long text containing match narrative)
        commentary = self._extract_commentary(soup)
        report["commentary"] = commentary

        # Goals and substitutions from events table or commentary
        report["goalscorers"]   = self._parse_goals(soup, commentary)
        report["substitutions"] = self._parse_substitutions(soup, commentary)

        # Player ratings table
        report["player_ratings"] = self._parse_player_ratings(soup)

        # Man of match
        report["man_of_match"] = self._parse_man_of_match(soup, commentary)

        return report

    def _extract_team_ids(self, soup: BeautifulSoup) -> tuple[str | None, str | None]:
        home_id = away_id = None
        for link in soup.find_all("a", href=re.compile(r"ver_equipa\.asp\?equipa=")):
            m = re.search(r"equipa=(\d+)", link["href"])
            if not m:
                continue
            tid = m.group(1)
            if home_id is None:
                home_id = tid
            elif away_id is None:
                away_id = tid
                break
        return home_id, away_id

    def _parse_score(self, result_str: str) -> tuple[int | None, int | None]:
        """Parse '2-1', '2 - 1', '2:1' etc. → (2, 1)."""
        m = re.search(r"(\d+)\s*[-:]\s*(\d+)", result_str)
        if m:
            return int(m.group(1)), int(m.group(2))
        return None, None

    def _parse_stats_table(self, soup: BeautifulSoup, report: dict) -> None:
        """Fill formation, style, and AT settings from the stats table."""
        stats_table = None
        for table in soup.find_all("table"):
            if "Formation" in table.get_text():
                stats_table = table
                break
        if not stats_table:
            logger.warning("Stats table not found in match report %s", report["match_id"])
            return

        for row in stats_table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            label    = cells[0].get_text(strip=True).lower()
            home_val = cells[1].get_text(separator=" ", strip=True)
            away_val = cells[3].get_text(separator=" ", strip=True)

            if "formation" in label:
                report["home_formation"] = home_val
                report["away_formation"] = away_val
            elif "style" in label and "passing" not in label:
                report["home_style"] = home_val
                report["away_style"] = away_val
            elif "offside" in label:
                report["home_at_settings"]["offside_trap"] = home_val.lower() == "yes"
                report["away_at_settings"]["offside_trap"] = away_val.lower() == "yes"
            elif "pressing" in label:
                report["home_at_settings"]["pressing"] = home_val
                report["away_at_settings"]["pressing"] = away_val
            elif "counter" in label:
                report["home_at_settings"]["counter_attack"] = home_val.lower() == "yes"
                report["away_at_settings"]["counter_attack"] = away_val.lower() == "yes"
            elif "one" in label and label.count("one") >= 2:
                report["home_at_settings"]["one_on_ones"] = home_val.lower() == "yes"
                report["away_at_settings"]["one_on_ones"] = away_val.lower() == "yes"
            elif "marking" in label:
                report["home_at_settings"]["marking"] = home_val
                report["away_at_settings"]["marking"] = away_val
            elif "high ball" in label:
                report["home_at_settings"]["high_balls"] = home_val.lower() == "yes"
                report["away_at_settings"]["high_balls"] = away_val.lower() == "yes"
            elif "keeping" in label:
                report["home_at_settings"]["keeping"] = home_val
                report["away_at_settings"]["keeping"] = away_val
            elif "first time" in label:
                report["home_at_settings"]["first_time"] = home_val.lower() == "yes"
                report["away_at_settings"]["first_time"] = away_val.lower() == "yes"
            elif "long shot" in label:
                report["home_at_settings"]["long_shots"] = home_val.lower() == "yes"
                report["away_at_settings"]["long_shots"] = away_val.lower() == "yes"

    def _extract_commentary(self, soup: BeautifulSoup) -> str:
        """Find the longest text block (the match commentary narrative)."""
        best = ""
        for tag in soup.find_all(["td", "div", "p"]):
            txt = tag.get_text(separator=" ", strip=True)
            if len(txt) > len(best) and len(txt) > 200:
                best = txt
        # Strip the match-timeline minute-ticker ("Match Time: Match Start' 1' 2' 3' ...")
        best = re.sub(r"Match Time:\s+Match Start'(?:\s+\d+')+", "", best).strip()
        return best

    def _parse_goals_from_json(self, soup: BeautifulSoup) -> list[dict]:
        """Extract goalscorers from the pm-match-report JSON blob embedded in page scripts."""
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
            except (json.JSONDecodeError, ValueError):
                return []

            match    = data.get("match", {})
            home_obj = match.get("homeTeam", {})
            away_obj = match.get("awayTeam", {})
            home_id  = home_obj.get("id")
            _away_id = away_obj.get("id")
            home_nm  = home_obj.get("name", "")
            away_nm  = away_obj.get("name", "")

            player_map: dict[int, str] = {}
            for side in ("homeFormation", "awayFormation"):
                for p in match.get(side, {}).get("startingEleven", []):
                    player_map[p["playerId"]] = p["playerName"]
                for p in match.get(side, {}).get("substitutions", []):
                    player_map[p["playerId"]] = p["playerName"]

            goals = []
            for ev in match.get("events", []):
                if ev.get("typeId") != 7:
                    continue
                goals.append({
                    "team":        home_nm if ev.get("teamId") == home_id else away_nm,
                    "player_name": player_map.get(ev["playerId"], str(ev["playerId"])),
                    "minute":      ev.get("timeInMinutes"),
                })
            return goals

        return []

    def _parse_goals(self, soup: BeautifulSoup, commentary: str) -> list[dict]:
        """Extract goalscorer events — primary: JSON blob; fallback: commentary."""
        # Strategy 0: JSON blob (most reliable — avoids false matches on stats rows)
        goals = self._parse_goals_from_json(soup)
        if goals:
            return goals

        # Strategy 1 (original table scanning) was unreliable — it matched stats
        # rows ("Shots on Goal", "Goalkeeper") as goal events. Skipped.

        # Strategy 2: parse commentary for scorer patterns
        patterns = [
            r"(\d{1,3})['\"]?\s*[\:\-]?\s*([A-Z][a-zA-Z\s\-\.]+?)\s+(?:scored?|goal|golo)",
            r"goal\s+for\s+([A-Z][a-zA-Z\s]+)[\.\!]?\s+([A-Z][a-zA-Z\s\-\.]+)",
        ]
        for pat in patterns:
            for m in re.finditer(pat, commentary, re.IGNORECASE):
                grp = m.groups()
                if grp and len(grp) >= 2:
                    goals.append({
                        "team":        "",
                        "player_name": grp[1].strip() if not grp[0].isdigit() else grp[1].strip(),
                        "minute":      int(grp[0]) if grp[0].isdigit() else None,
                    })

        return goals

    def _parse_substitutions(self, soup: BeautifulSoup, commentary: str) -> list[dict]:
        """Extract substitution events."""
        subs: list[dict] = []

        # Strategy 1: events table with substitution/change rows
        for table in soup.find_all("table"):
            txt = table.get_text(separator=" ", strip=True).lower()
            if "substitut" in txt or "change" in txt or "substituição" in txt:
                for row in table.find_all("tr")[1:]:
                    row_txt = row.get_text(separator=" ", strip=True).lower()
                    if "substitut" in row_txt or "change" in row_txt or "saiu" in row_txt:
                        cells = row.find_all("td")
                        minute_m = re.search(r"(\d{1,3})['\"]", row.get_text())
                        minute = int(minute_m.group(1)) if minute_m else None
                        texts = [c.get_text(separator=" ", strip=True) for c in cells if c.get_text(strip=True)]
                        subs.append({
                            "team":   "",
                            "off":    texts[1] if len(texts) > 1 else "",
                            "on":     texts[2] if len(texts) > 2 else "",
                            "minute": minute,
                        })

        if subs:
            return subs

        # Strategy 2: commentary patterns
        for m in re.finditer(
            r"(\d{1,3})['\"]?\s*[\:\-]?\s*([A-Z][a-zA-Z\s\-\.]+?)\s+(?:replaced?|substituted?)\s+(?:by\s+)?([A-Z][a-zA-Z\s\-\.]+)",
            commentary,
            re.IGNORECASE,
        ):
            subs.append({
                "team":   "",
                "off":    m.group(2).strip(),
                "on":     m.group(3).strip(),
                "minute": int(m.group(1)) if m.group(1).isdigit() else None,
            })

        return subs

    def _parse_player_ratings(self, soup: BeautifulSoup) -> dict:
        """Extract player name → rating from ratings table if present."""
        ratings: dict[str, float] = {}

        for table in soup.find_all("table"):
            txt = table.get_text(separator=" ", strip=True)
            # Ratings tables typically have headers like "Player" and "Rating"
            if "rating" in txt.lower():
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue
                    player_name = cells[0].get_text(separator=" ", strip=True)
                    rating_txt  = cells[-1].get_text(strip=True)
                    try:
                        rating = float(rating_txt.replace(",", "."))
                        if 0 < rating <= 10 and player_name:
                            ratings[player_name] = rating
                    except ValueError:
                        continue
                if ratings:
                    break

        return ratings

    def _parse_man_of_match(self, soup: BeautifulSoup, commentary: str) -> str | None:
        """Extract man of the match from page or commentary."""
        # Look for "Man of the Match", "Best Player", "MVP" text
        patterns = [
            r"man\s+of\s+the\s+match[:\s]+([A-Z][a-zA-Z\s\-\.]+)",
            r"best\s+player[:\s]+([A-Z][a-zA-Z\s\-\.]+)",
            r"mvp[:\s]+([A-Z][a-zA-Z\s\-\.]+)",
            r"melhor\s+jogador[:\s]+([A-Z][a-zA-Z\s\-\.]+)",
        ]
        full_text = soup.get_text(separator=" ", strip=True) + " " + commentary
        for pat in patterns:
            m = re.search(pat, full_text, re.IGNORECASE)
            if m:
                return m.group(1).strip()[:60]
        return None

    # ------------------------------------------------------------------ #
    # Matchday context scraping                                            #
    # ------------------------------------------------------------------ #

    def _scrape_matchday_context(self, fixture: dict) -> list[dict]:
        """Scrape other match results from the same matchday.

        Uses global league calendar for league matches and the cup results
        page for cup matches.
        """
        match_type = (fixture.get("match_type") or "").lower()
        season = fixture.get("season", "")
        is_cup = any(kw in match_type for kw in _CUP_KEYWORDS)

        if is_cup:
            return self._scrape_cup_results(fixture)
        return self._scrape_league_global_results(season)

    def _scrape_league_global_results(self, season: str) -> list[dict]:
        """Scrape all league results from calendario.asp?action=global for the season."""
        url = f"{self.base_url}/calendario.asp?action=global&epoca={season}"
        logger.info("Fetching global league matchday results: %s", url)
        try:
            self.page.goto(url, wait_until="domcontentloaded")
            soup = BeautifulSoup(self.page.content(), "html.parser")
            return self._parse_global_fixture_table(soup)
        except Exception as exc:
            logger.warning("Failed to scrape global results: %s", exc)
            return []

    def _parse_global_fixture_table(self, soup: BeautifulSoup) -> list[dict]:
        """Parse the global fixture table into a list of {home_team, away_team, result}."""
        results: list[dict] = []
        table = soup.find("table", class_="table_border")
        if not table:
            tables = soup.find_all("table")
            table = tables[1] if len(tables) > 1 else (tables[0] if tables else None)
        if not table:
            logger.warning("No global fixture table found")
            return results

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 5:
                continue
            home_name   = cells[2].get_text(separator=" ", strip=True)
            away_name   = cells[4].get_text(separator=" ", strip=True)
            result_text = cells[5].get_text(strip=True).replace("\xa0", "") if len(cells) > 5 else ""
            if not result_text:
                continue

            # Extract match_id from "Match Report" link (cells[6] if present)
            match_id = None
            if len(cells) > 6:
                link = cells[6].find("a", href=re.compile(r"relatorio\.asp"))
                if link:
                    m = re.search(r"jogo_id=(\d+)", link.get("href", ""))
                    if m:
                        match_id = m.group(1)

            results.append({
                "home_team": home_name,
                "away_team": away_name,
                "result":    result_text,
                "match_id":  match_id,
            })

        logger.info("Scraped %d global matchday results", len(results))
        return results

    def _scrape_cup_results(self, fixture: dict) -> list[dict]:
        """Scrape cup round results via calendario_taca.asp → res_taca.asp."""
        logger.info("Detecting cup round from calendario_taca.asp")
        try:
            self.page.goto(f"{self.base_url}/calendario_taca.asp", wait_until="domcontentloaded")
            soup = BeautifulSoup(self.page.content(), "html.parser")
            cup_id, elim = self._find_cup_round(soup, fixture)
        except Exception as exc:
            logger.warning("Failed to fetch cup calendar: %s", exc)
            return []

        if cup_id is None or elim is None:
            logger.warning("Could not determine cup round for fixture %s", fixture.get("match_id"))
            return []

        url = f"{self.base_url}/res_taca.asp?id={cup_id}&elim={elim}"
        logger.info("Fetching cup round results: %s", url)
        try:
            self.page.goto(url, wait_until="domcontentloaded")
            soup = BeautifulSoup(self.page.content(), "html.parser")
            return self._parse_cup_results_table(soup)
        except Exception as exc:
            logger.warning("Failed to scrape cup results: %s", exc)
            return []

    def _find_cup_round(
        self, soup: BeautifulSoup, fixture: dict
    ) -> tuple[str | None, str | None]:
        """Find cup_id and elim from links on calendario_taca.asp.

        Returns (cup_id, elim) of the round that contains the current match.
        Falls back to the link with the highest elim number (latest round) if
        exact match is not found.
        """
        home_name = (fixture.get("home_team_name") or "").lower()
        away_name = (fixture.get("away_team_name") or "").lower()

        # Collect all res_taca.asp?id=X&elim=Y links
        links: list[tuple[str, str]] = []
        for a in soup.find_all("a", href=re.compile(r"res_taca\.asp\?id=\d+&elim=\d+")):
            m = re.search(r"id=(\d+)&elim=(\d+)", a["href"])
            if m:
                links.append((m.group(1), m.group(2)))

        if not links:
            return None, None

        # Try to find the round containing our match teams by visiting each round page
        # Sort descending by elim (check latest round first — most likely match round)
        links_sorted = sorted(links, key=lambda x: int(x[1]), reverse=True)
        for cup_id, elim in links_sorted:
            try:
                round_url = f"{self.base_url}/res_taca.asp?id={cup_id}&elim={elim}"
                self.page.goto(round_url, wait_until="domcontentloaded")
                round_soup = BeautifulSoup(self.page.content(), "html.parser")
                round_text = round_soup.get_text(separator=" ", strip=True).lower()
                if home_name in round_text or away_name in round_text:
                    logger.info("Found match in cup round %s (elim=%s)", cup_id, elim)
                    return cup_id, elim
            except Exception:
                continue

        # Fallback: highest elim (most recent round)
        return links_sorted[0]

    def _parse_cup_results_table(self, soup: BeautifulSoup) -> list[dict]:
        """Parse cup round results into [{home_team, away_team, result}]."""
        results: list[dict] = []
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                home_name   = cells[0].get_text(separator=" ", strip=True)
                result_text = cells[1].get_text(strip=True).replace("\xa0", "")
                away_name   = cells[2].get_text(separator=" ", strip=True)
                # Validate it looks like a score ("1-0", "2-1", etc.)
                if result_text and re.search(r"\d+\s*[-:]\s*\d+", result_text):
                    results.append({
                        "home_team": home_name,
                        "away_team": away_name,
                        "result":    result_text,
                    })
        logger.info("Scraped %d cup round results", len(results))
        return results
