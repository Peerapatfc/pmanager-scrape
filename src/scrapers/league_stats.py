"""
League-wide stats scraper.

Fetches standings, top scorers, top assists, average ratings,
man of the match, and top eleven from PManager's league stat pages.
All pages are scraped with the same authenticated browser session.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.scrapers.base import BaseScraper


class LeagueStatsScraper(BaseScraper):
    """Scrapes season-level league stats for inclusion in the podcast source doc."""

    # ------------------------------------------------------------------ #
    # Main entry                                                           #
    # ------------------------------------------------------------------ #

    def scrape_all(self) -> dict:
        """Scrape all stat pages and return a combined dict.

        Returns:
            {
              "standings":     list[dict],   # Position, Team, G, W, D, L, GS, GC, GD, Pts
              "top_scorers":   list[dict],   # Pos, Name, Team, Age, Position, MinPlayed, Goals
              "top_assists":   list[dict],   # Pos, Name, Team, Age, Position, MinPlayed, Assists
              "avg_ratings":   list[dict],   # Pos, Name, Team, Age, Position, MinPlayed, Rating
              "man_of_match":  list[dict],   # Pos, Name, Team, Age, Position, MinPlayed, Occasions
              "top_eleven_week":   list[dict],
              "top_eleven_season": list[dict],
            }
        """
        return {
            "standings":          self._scrape_standings(),
            "top_scorers":        self._scrape_table("m_marcadores.asp",   "Goals"),
            "top_assists":        self._scrape_table("m_assistencias.asp", "Top Assists"),
            "avg_ratings":        self._scrape_table("m_media.asp",        "Average Rating"),
            "man_of_match":       self._scrape_table("m_campo.asp",        "Occasions"),
            **self._scrape_top_eleven(),
        }

    # ------------------------------------------------------------------ #
    # Page scrapers                                                        #
    # ------------------------------------------------------------------ #

    def _scrape_standings(self) -> list[dict]:
        url = f"{self.base_url}/classificacao.asp"
        logger.info("Scraping standings: %s", url)
        self.page.goto(url, wait_until="domcontentloaded")
        soup = BeautifulSoup(self.page.content(), "html.parser")

        rows = []
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "Points" not in headers and "Pts" not in headers:
                continue
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all("td")]
                if len(cells) < 9:
                    continue
                rows.append({
                    "position": cells[0].rstrip("."),
                    "team":     cells[1] if len(cells) > 1 else "",
                    "played":   _safe_int(cells[2]),
                    "won":      _safe_int(cells[3]),
                    "drawn":    _safe_int(cells[4]),
                    "lost":     _safe_int(cells[5]),
                    "gf":       _safe_int(cells[6]),
                    "ga":       _safe_int(cells[7]),
                    "gd":       cells[8],
                    "points":   _safe_int(cells[9]) if len(cells) > 9 else None,
                })
            if rows:
                break

        logger.info("Standings: %d rows", len(rows))
        return rows

    def _scrape_table(self, path: str, stat_col: str) -> list[dict]:
        """Generic scraper for the 7-column stat tables (scorers, assists, etc.)."""
        url = f"{self.base_url}/{path}"
        logger.info("Scraping %s", url)
        self.page.goto(url, wait_until="domcontentloaded")
        soup = BeautifulSoup(self.page.content(), "html.parser")

        rows = []
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if "Name" not in headers and "name" not in " ".join(headers).lower():
                continue
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all("td")]
                if len(cells) < 6:
                    continue
                row: dict = {
                    "rank":     cells[0].rstrip("."),
                    "name":     cells[1],
                    "team":     cells[2],
                    "age":      _safe_int(cells[3]),
                    "position": cells[4],
                    "min_played": _safe_int(cells[5]),
                    stat_col:   _safe_float(cells[6]) if len(cells) > 6 else None,
                }
                rows.append(row)
            if rows:
                break

        logger.info("%s: %d rows", path, len(rows))
        return rows

    def _scrape_top_eleven(self) -> dict:
        url = f"{self.base_url}/onze_ideal.asp?action=0"
        logger.info("Scraping top eleven: %s", url)
        self.page.goto(url, wait_until="domcontentloaded")
        soup = BeautifulSoup(self.page.content(), "html.parser")

        # Page has two tables: Week and Season
        tables = soup.find_all("table")
        week_rows:   list[dict] = []
        season_rows: list[dict] = []

        for i, table in enumerate(tables[:2]):
            rows = []
            for tr in table.find_all("tr")[1:]:
                cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all("td")]
                if len(cells) < 4:
                    continue
                # columns: Name, Team, Age, Position, [MinPlayed], Average Rating
                rows.append({
                    "name":     cells[0],
                    "team":     cells[1],
                    "age":      _safe_int(cells[2]),
                    "position": cells[3],
                    "rating":   _safe_float(cells[-1]),
                })
            if i == 0:
                week_rows = rows
            else:
                season_rows = rows

        logger.info("Top Eleven — week: %d, season: %d", len(week_rows), len(season_rows))
        return {"top_eleven_week": week_rows, "top_eleven_season": season_rows}


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _safe_int(val: str) -> int | None:
    try:
        return int(val.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def _safe_float(val: str) -> float | None:
    try:
        return float(val.replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None
