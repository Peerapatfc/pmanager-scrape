"""
Squad scraper — reads the user's own squad from plantel.asp.

Extracts player IDs, positions, ages and all 12 skill values from the
squad table. Results are used to:
  1. Upsert player skills into the ``players`` table.
  2. Refresh ``my_squad`` membership.
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from src.config import config
from src.core.logger import logger
from src.scrapers.base import BaseScraper

# Maps the column order in the plantel.asp skills table to DB field names.
SKILL_COLUMNS: list[str] = [
    "Handling",    # Han
    "Out of Area", # Cro
    "Reflexes",    # Ref
    "Agility",     # Agi
    "Tackling",    # Tck
    "Heading",     # Hea
    "Passing",     # Pas
    "Positioning", # Pos
    "Finishing",   # Fin
    "Technique",   # Tec
    "Speed",       # Spe
    "Strength",    # Str
]


class SquadScraper(BaseScraper):
    """Scrapes the user's squad page and returns player + skill data."""

    def __init__(self, base_url: str = "https://www.pmanager.org") -> None:
        super().__init__(base_url=base_url)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape(self) -> list[dict[str, Any]]:
        """Login and scrape the squad page.

        Returns:
            List of player dicts. Each dict contains:
            ``player_id``, ``position``, ``age``, and one key per skill
            in :data:`SKILL_COLUMNS`.
        """
        self.start()
        try:
            self.login(config.PM_USERNAME, config.PM_PASSWORD)
            return self._parse_squad()
        finally:
            self.stop()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _parse_squad(self) -> list[dict[str, Any]]:
        """Navigate to plantel.asp and parse the skills table.

        Returns:
            List of player record dicts.
        """
        url = f"{self.base_url}/plantel.asp?equipa=2&filtro=1&pos=&sort="
        logger.info("Fetching squad page: %s", url)
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

        soup = BeautifulSoup(self.page.content(), "html.parser")
        rows = soup.select("tr.list1, tr.list2")
        logger.info("Found %d player rows in squad table", len(rows))

        players: list[dict[str, Any]] = []
        for row in rows:
            record = self._parse_row(row)
            if record:
                players.append(record)

        logger.info("Parsed %d valid squad players", len(players))
        return players

    def _parse_row(self, row: Any) -> dict[str, Any] | None:
        """Parse a single squad table row.

        Args:
            row: BeautifulSoup Tag for a ``<tr>`` row.

        Returns:
            Player record dict, or ``None`` if the row is malformed.
        """
        cells = row.find_all("td")
        # Expected layout: icon | position | name | age | country | 12 skills | squad | youth
        if len(cells) < 17:
            return None

        # Player ID and name (cell index 2)
        link = cells[2].find("a")
        if not link:
            return None
        href = link.get("href", "")
        match = re.search(r"jog_id=(\d+)", href)
        if not match:
            return None
        player_id = match.group(1)
        name = link.get_text(strip=True)

        # Position (cell index 1) — e.g. "GK", "D C", "M RC", "F L"
        # Use separator=" " so inner whitespace between bold tag and subtype is kept.
        position = cells[1].get_text(separator=" ", strip=True)

        # Age (cell index 3)
        try:
            age = int(cells[3].get_text(strip=True))
        except ValueError:
            age = None

        # Skills (cells 5 through 16)
        skills: dict[str, Any] = {}
        for i, skill_name in enumerate(SKILL_COLUMNS):
            raw = cells[5 + i].get_text(strip=True)
            try:
                skills[skill_name] = int(raw)
            except ValueError:
                skills[skill_name] = 0

        return {
            "player_id": player_id,
            "name": name,
            "position": position,
            "age": age,
            **skills,
        }
