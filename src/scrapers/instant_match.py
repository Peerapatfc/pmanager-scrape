"""Scraper for PManager Instant Match lobby (pvp_geral.asp).

Finds open (Pending, no opponent) games and returns them as a list of dicts.
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.scrapers.base import BaseScraper

_PVP_URL = "https://www.pmanager.org/pvp_geral.asp"

WEATHER_MAP = {
    "neve.gif": "Snow",
    "sol.gif": "Sun",
    "parcialmente.gif": "Partly Cloudy",
    "nublado.gif": "Cloudy",
    "chuva.gif": "Rain",
    "muitonublado.gif": "Very Cloudy",
}


@dataclass
class InstantMatch:
    match_id: str
    team_name: str
    team_id: str
    time: str
    weather: str
    division_title: str


class InstantMatchScraper(BaseScraper):
    """Scrapes open instant matches waiting for an opponent."""

    def get_open_matches(self) -> list[InstantMatch]:
        """Navigate to pvp_geral.asp and return all joinable Pending games."""
        logger.info("Fetching instant match lobby...")
        self.page.goto(_PVP_URL, wait_until="networkidle")

        # pvp_geral.asp defaults to "PM Arena" tab. Must click "Matches" tab
        # (ver_pagina(3,1)) to load #lista_jogos with open games.
        self.page.click("div.menu_pvp:has-text('Matches')")
        try:
            self.page.wait_for_selector("#lista_jogos table", timeout=15000)
        except Exception:
            logger.warning("No match list found after clicking Matches tab.")
            return []

        html = self.page.content()
        soup = BeautifulSoup(html, "html.parser")

        matches: list[InstantMatch] = []
        for row in soup.select("#lista_jogos table tr.list2"):
            cells = row.find_all("td")
            if len(cells) < 8:
                continue

            # Col 7 (index 7): Join Game link — only present for open games
            join_td = cells[7]
            if not join_td.get_text(strip=True):
                continue

            match_id = cells[0].get_text(strip=True)

            # Col 1: team img title (division) + flag + team link
            team_link = cells[1].find("a")
            team_name = team_link.get_text(strip=True) if team_link else "Unknown"
            team_href = team_link.get("href", "") if team_link else ""
            team_id = ""
            if "equipa=" in team_href:
                team_id = team_href.split("equipa=")[-1].split("&")[0]

            division_img = cells[1].find("img")
            division_title = division_img.get("title", "") if division_img else ""

            # Col 3 (index 3): opponent slot — must be empty (open game)
            opponent = cells[3].get_text(strip=True)
            if opponent:
                continue  # already has opponent

            # Col 6: status must be Pending
            status = cells[6].get_text(strip=True)
            if status.lower() != "pending":
                continue

            time_str = cells[4].get_text(strip=True)

            weather_img = cells[5].find("img")
            weather_src = weather_img.get("src", "") if weather_img else ""
            weather_file = weather_src.split("/")[-1]
            weather = WEATHER_MAP.get(weather_file, weather_img.get("title", "?") if weather_img else "?")

            matches.append(
                InstantMatch(
                    match_id=match_id,
                    team_name=team_name,
                    team_id=team_id,
                    time=time_str,
                    weather=weather,
                    division_title=division_title,
                )
            )

        logger.info("Found %d open instant match(es).", len(matches))
        return matches
