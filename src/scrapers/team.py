"""
Team info scraper for PManager.org.

Extracts financial and squad statistics from the manager's own team
information page (``/info.asp``).
"""

import re
from typing import Any

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.core.utils import clean_currency
from src.scrapers.base import BaseScraper


class TeamInfoScraper(BaseScraper):
    """Scrapes the manager's team information page."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_value(self, soup: BeautifulSoup, label_text: str) -> str:
        """Extract the table-cell value that follows a label cell.

        Args:
            soup: Parsed HTML tree to search.
            label_text: Exact text content of the label cell to locate.

        Returns:
            Text content of the value cell, or ``"N/A"`` if not found.
        """
        element = soup.find(string=re.compile(re.escape(label_text)))
        if element:
            parent_td = element.find_parent("td")
            if parent_td:
                value_td = parent_td.find_next_sibling("td")
                if value_td:
                    return value_td.get_text(strip=True, separator=" ")
        return "N/A"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_team_info(self) -> dict[str, Any]:
        """Scrape all team information from ``/info.asp``.

        Returns:
            Dictionary containing raw string values for each field plus
            ``*_int`` float versions for numeric currency fields. Example keys:
            ``team_name``, ``available_funds``, ``available_funds_int``,
            ``wages_sum``, ``wages_sum_int``, ``players_count``, etc.
        """
        logger.info("Navigating to Team Info page...")
        self.page.goto(f"{self.base_url}/info.asp")
        self.page.wait_for_load_state("networkidle")

        try:
            self.page.wait_for_selector("table.table_border", timeout=5000)
        except Exception as e:
            logger.debug("Timeout waiting for team info table: %s", e)

        content = self.page.content()
        soup = BeautifulSoup(content, "html.parser")

        info: dict[str, Any] = {}

        info["manager"] = self._extract_value(soup, "Manager")
        info["team_name"] = self._extract_value(soup, "Name")
        info["available_funds"] = self._extract_value(soup, "Available Funds")
        info["financial_situation"] = self._extract_value(soup, "Financial Situation")
        info["wage_average"] = self._extract_value(soup, "Wage Average")
        info["wages_sum"] = self._extract_value(soup, "Wages Sum")
        info["wage_roof"] = self._extract_value(soup, "Wage Roof of Club")
        info["academy"] = self._extract_value(soup, "Academy")
        info["players_count"] = self._extract_value(soup, "Players")
        info["age_average"] = self._extract_value(soup, "Age Average")
        info["players_value"] = self._extract_value(soup, "Players Value")
        info["team_reputation"] = self._extract_value(soup, "Team Reputation")
        info["current_division"] = self._extract_value(soup, "Current Division")
        info["fan_club_size"] = self._extract_value(soup, "Fan Club Size")

        # Parse numeric currency fields (strip any trailing "+X" bonus amounts)
        currency_fields = [
            "available_funds",
            "wages_sum",
            "wage_roof",
            "players_value",
            "wage_average",
        ]
        for key in currency_fields:
            if key in info and info[key] != "N/A":
                raw_val = info[key].split("+")[0].strip()
                info[f"{key}_int"] = clean_currency(raw_val)

        return info
