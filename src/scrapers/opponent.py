"""
Opponent team scraper for PManager.org.

Extracts all player IDs from a given opponent team page so that their
profiles can be analysed for scouting purposes.
"""

import re
from typing import Any

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.scrapers.base import BaseScraper


class OpponentScraper(BaseScraper):
    """Scrapes the squad listing of an opponent team page."""

    def get_team_players(self, team_url: str) -> list[str]:
        """Extract all player IDs from an opponent team's squad page.

        Args:
            team_url: Full URL of the team page (e.g.
                ``https://www.pmanager.org/ver_equipa.asp?equipa=12345``).

        Returns:
            Deduplicated list of player ID strings found in the squad table.
        """
        logger.info("Navigating to team page: %s", team_url)
        self.page.goto(team_url)
        self.page.wait_for_load_state("networkidle")

        content = self.page.content()
        soup = BeautifulSoup(content, "html.parser")

        player_ids: list[str] = []
        rows = soup.find_all("tr", class_=["list1", "list2"])
        logger.info("Found %d rows in squad table.", len(rows))

        for row in rows:
            link = row.find("a", href=re.compile(r"ver_jogador\.asp\?jog_id="))
            if link:
                href = link["href"]
                try:
                    pid = href.split("jog_id=")[-1]
                    player_ids.append(pid)
                except IndexError:
                    continue

        unique_ids = list(set(player_ids))
        logger.info("Found %d unique players in team.", len(unique_ids))
        return unique_ids
