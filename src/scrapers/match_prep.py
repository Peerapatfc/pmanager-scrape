# src/scrapers/match_prep.py
"""Scraper for fixture schedules, match reports (formation + ATs), and opponent rosters."""
import re
from datetime import datetime
from statistics import mean

from bs4 import BeautifulSoup

from src.core.logger import logger
from src.scrapers.base import BaseScraper
from src.services.supabase_client import SupabaseManager

SKILL_COLS = [
    "Handling", "Out of Area", "Reflexes", "Agility",
    "Tackling", "Heading", "Passing", "Positioning",
    "Finishing", "Technique", "Speed", "Strength",
]

# Commentary keywords that signal an AT activated for a team
AT_COMMENTARY_KEYS = {
    "pressing":       ["pressing", "press"],
    "offside_trap":   ["offside"],
    "counter_attack": ["counter-attack", "counter attack", "counter"],
    "high_balls":     ["high ball", "heading ability", "aerial plays"],
    "one_on_ones":    ["one-on-one", "one on one"],
    "marking":        ["marking style", "zonal", "man-to-man", "man to man"],
    "long_shots":     ["long shot", "long-shot"],
    "first_time":     ["first time", "first-time"],
    # Commentary uses "style is confusing" — never names the specific style
    "keeping":        ["rushing out", "rush out", "stand in", "style is confusing", "confusing the opposite"],
}


class MatchPrepScraper(BaseScraper):
    """Synchronous scraper for match prep data (extends BaseScraper)."""

    # ------------------------------------------------------------------ #
    # Fixture list                                                         #
    # ------------------------------------------------------------------ #

    def scrape_my_fixtures(self, season: str) -> list[dict]:
        """Scrape my team's fixture list for the given season."""
        url = f"{self.base_url}/calendario.asp?action=equipa&epoca={season}"
        logger.info("Fetching fixture list: %s", url)
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        soup = BeautifulSoup(self.page.content(), "html.parser")
        return self._parse_fixture_table(soup, season)

    def scrape_opponent_fixtures(self, team_id: str, season: str) -> list[dict]:
        """Scrape an opponent's fixture list to find recent match IDs."""
        url = f"{self.base_url}/calendario.asp?action=equipa&equipa={team_id}&epoca={season}"
        logger.info("Fetching opponent fixture list: %s", url)
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        soup = BeautifulSoup(self.page.content(), "html.parser")
        return self._parse_fixture_table(soup, season)

    def _parse_fixture_table(self, soup: BeautifulSoup, season: str) -> list[dict]:
        fixtures = []
        # The page has 2 tables: [0] season selector (1 cell), [1] fixtures (class table_border)
        table = soup.find("table", class_="table_border")
        if not table:
            # fallback: try second table if class not found
            tables = soup.find_all("table")
            logger.info("Found %d table(s) on fixture page (table_border not found)", len(tables))
            table = tables[1] if len(tables) > 1 else (tables[0] if tables else None)
        if not table:
            logger.warning("No fixture table found on page — check URL/login")
            return fixtures

        rows = table.find_all("tr")[1:]
        logger.info("Found %d data rows", len(rows))

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 5:
                logger.debug("Skipping row with %d cells: %s", len(cells), row.get_text(separator="|", strip=True)[:80])
                continue

            match_type  = cells[0].get_text(separator=" ", strip=True)
            date_str    = cells[1].get_text(strip=True)
            home_cell   = cells[2]
            # Columns: Match Type | Date | Home | vs | Away | Result | Match
            away_cell   = cells[4] if len(cells) > 4 else cells[2]
            # &nbsp; in result cell = upcoming match (no score yet)
            result_text = cells[5].get_text(strip=True).replace("\xa0", "") if len(cells) > 5 else ""

            # Match ID from "Match Report" link — search all cells (column may vary)
            match_id = None
            for cell in cells:
                link = cell.find("a", href=re.compile(r"jogo_id="))
                if link:
                    m = re.search(r"jogo_id=(\d+)", link["href"])
                    match_id = m.group(1) if m else None
                    break

            # Team IDs from name links — use ver_equipa.asp links specifically
            # to avoid matching equipa= parameters on match/calendar links.
            home_link = home_cell.find("a", href=re.compile(r"ver_equipa\.asp\?equipa="))
            away_link = away_cell.find("a", href=re.compile(r"ver_equipa\.asp\?equipa="))
            home_id = re.search(r"equipa=(\d+)", home_link["href"]).group(1) if home_link else None
            away_id = re.search(r"equipa=(\d+)", away_link["href"]).group(1) if away_link else None

            home_name = home_cell.get_text(separator=" ", strip=True)
            away_name = away_cell.get_text(separator=" ", strip=True)

            fixtures.append({
                "match_id":       match_id or f"{season}_{date_str}_{home_name}_{away_name}",
                "match_date":     self._parse_match_date(date_str),
                "match_type":     match_type,
                "home_team_id":   home_id,
                "home_team_name": home_name,
                "away_team_id":   away_id,
                "away_team_name": away_name,
                "result":         result_text,
                "season":         season,
            })

        # Deduplicate by match_id (last occurrence wins, preserving most recent scrape)
        seen: dict[str, dict] = {}
        for f in fixtures:
            seen[f["match_id"]] = f
        return list(seen.values())

    def _parse_match_date(self, date_str: str) -> str | None:
        """Parse '09/04/2026 @ 19:00' → ISO string with Z suffix."""
        try:
            dt = datetime.strptime(date_str.strip(), "%d/%m/%Y @ %H:%M")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            return None

    # ------------------------------------------------------------------ #
    # Match report scraping                                                #
    # ------------------------------------------------------------------ #

    def scrape_match_stats(self, match_id: str) -> dict:
        """Scrape Stats tab from relatorio.asp for one match."""
        url = f"{self.base_url}/relatorio.asp?jogo_id={match_id}"
        self.page.goto(url, wait_until="domcontentloaded")
        soup = BeautifulSoup(self.page.content(), "html.parser")
        return self._parse_match_stats(soup, match_id)

    def _parse_match_stats(self, soup: BeautifulSoup, match_id: str) -> dict:
        result = {
            "match_id":           match_id,
            "home_team_id":       None,  # extracted from match report General Info
            "away_team_id":       None,
            "home_formation":     None, "away_formation": None,
            "home_style":         None, "away_style":     None,
            "home_ats":           {},   "away_ats":       {},
            "commentary":         "",
        }

        # Extract home/away team IDs from General Info table (first two equipa= links)
        for link in soup.find_all("a", href=re.compile(r"ver_equipa\.asp\?equipa=")):
            m = re.search(r"equipa=(\d+)", link["href"])
            if not m:
                continue
            tid = m.group(1)
            if result["home_team_id"] is None:
                result["home_team_id"] = tid
            elif result["away_team_id"] is None:
                result["away_team_id"] = tid
                break

        # Find stats table (contains "Formation" header)
        stats_table = None
        for table in soup.find_all("table"):
            if "Formation" in table.get_text():
                stats_table = table
                break

        if stats_table:
            for row in stats_table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue
                label    = cells[0].get_text(strip=True).lower()
                home_val = cells[1].get_text(strip=True)
                away_val = cells[3].get_text(strip=True)  # cells[2] is a spacer column

                if "formation" in label:
                    result["home_formation"] = home_val
                    result["away_formation"] = away_val
                elif "style" in label:
                    result["home_style"] = home_val
                    result["away_style"] = away_val
                elif "offside" in label:
                    result["home_ats"]["offside_trap"] = home_val.lower() == "yes"
                    result["away_ats"]["offside_trap"] = away_val.lower() == "yes"
                elif "pressing" in label:
                    result["home_ats"]["pressing"] = home_val   # "High"/"Low"/"Normal"
                    result["away_ats"]["pressing"] = away_val
                elif "counter" in label:
                    result["home_ats"]["counter_attack"] = home_val.lower() == "yes"
                    result["away_ats"]["counter_attack"] = away_val.lower() == "yes"
                elif "one" in label and "one" in label[4:]:
                    result["home_ats"]["one_on_ones"] = home_val.lower() == "yes"
                    result["away_ats"]["one_on_ones"] = away_val.lower() == "yes"
                elif "marking" in label:
                    result["home_ats"]["marking"] = home_val  # "Zonal" | "Man to Man"
                    result["away_ats"]["marking"] = away_val
                elif "high ball" in label:
                    result["home_ats"]["high_balls"] = home_val.lower() == "yes"
                    result["away_ats"]["high_balls"] = away_val.lower() == "yes"
                elif "keeping" in label:
                    result["home_ats"]["keeping"] = home_val   # "Stand In"/"Rushing Out"/"Not Defined"
                    result["away_ats"]["keeping"] = away_val
                elif "first time" in label:
                    result["home_ats"]["first_time"] = home_val.lower() == "yes"
                    result["away_ats"]["first_time"] = away_val.lower() == "yes"
                elif "long shot" in label:
                    result["home_ats"]["long_shots"] = home_val.lower() == "yes"
                    result["away_ats"]["long_shots"] = away_val.lower() == "yes"

        # Commentary block
        for td in soup.find_all("td"):
            txt = td.get_text(separator=" ", strip=True)
            if len(txt) > 200 and "players" in txt.lower():
                result["commentary"] = txt
                break

        return result

    def parse_at_activation(self, commentary: str, team_name: str) -> dict[str, bool]:
        """Return {at_key: True/False} based on commentary keywords near team name."""
        text = commentary.lower()
        name = team_name.lower()
        out: dict[str, bool] = {}
        for at_key, keywords in AT_COMMENTARY_KEYS.items():
            # AT activated if keyword AND team name both appear in commentary
            activated = any(kw in text for kw in keywords) and name in text
            out[at_key] = activated
        return out

    # ------------------------------------------------------------------ #
    # Opponent roster                                                       #
    # ------------------------------------------------------------------ #

    def scrape_opponent_roster(self, team_id: str) -> list[dict]:
        """Scrape opponent player list from plantel.asp."""
        url = f"{self.base_url}/plantel.asp?equipa={team_id}&vjog=1"
        self.page.goto(url)
        soup = BeautifulSoup(self.page.content(), "html.parser")
        return self._parse_roster(soup)

    def _parse_roster(self, soup: BeautifulSoup) -> list[dict]:
        players: list[dict] = []
        table = soup.find("table")
        if not table:
            return players

        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            # Player ID from link
            player_link = row.find("a", href=re.compile(r"jogador"))
            if not player_link:
                continue
            m = re.search(r"jogador=(\d+)", player_link.get("href", ""))
            if not m:
                continue
            player_id = m.group(1)

            name     = cells[0].get_text(separator=" ", strip=True)
            position = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            try:
                age = int(cells[2].get_text(strip=True)) if len(cells) > 2 else 0
            except ValueError:
                age = 0
            quality = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            players.append({
                "id":       player_id,
                "name":     name,
                "position": position,
                "age":      age,
                "quality":  quality,
            })
        return players

    # ------------------------------------------------------------------ #
    # Enrichment                                                           #
    # ------------------------------------------------------------------ #

    def detect_archetype(self, known_players: list[dict]) -> str:
        """Return 'speed' if avg Speed > avg Strength across known players, else 'strength'."""
        speeds    = [p["skills"].get("Speed", 0)    for p in known_players if p.get("skills")]
        strengths = [p["skills"].get("Strength", 0) for p in known_players if p.get("skills")]
        if not speeds:
            return "speed"
        return "speed" if mean(speeds) > mean(strengths) else "strength"

    def enrich_roster(
        self,
        roster: list[dict],
        archetype: str,
        sm: SupabaseManager,
        skills_map: dict[str, dict] | None = None,
    ) -> list[dict]:
        """Add 'skills' and 'source' to each player dict."""
        enriched: list[dict] = []
        for player in roster:
            # Use pre-fetched skills map if provided (avoids per-player DB round-trips)
            if skills_map is not None and player["id"] in skills_map:
                player["skills"] = skills_map[player["id"]]
                player["source"] = "db"
                enriched.append(player)
                continue

            # Exact DB match by player ID (fallback when no skills_map)
            res = sm.client.table("players").select("skills").eq("id", player["id"]).execute()
            if res.data:
                player["skills"] = res.data[0]["skills"] or {}
                player["source"] = "db"
                enriched.append(player)
                continue

            # Proxy estimation
            pos = player.get("position", "M")
            pos_prefix = "GK" if pos.startswith("G") else pos[0].upper()

            proxies = sm.find_proxy_players(
                position_prefix=pos_prefix,
                age=player["age"],
                quality=player["quality"],
                archetype=archetype,
            )

            if proxies:
                avg_skills: dict[str, float] = {}
                for skill in SKILL_COLS:
                    vals = [p["skills"].get(skill, 0) for p in proxies if p.get("skills")]
                    avg_skills[skill] = round(mean(vals), 1) if vals else 0.0
                player["skills"] = avg_skills
                # est_low if we fell back to fewer than 3 on archetype-filtered pass
                player["source"] = "est"
            else:
                player["skills"] = {s: 0 for s in SKILL_COLS}
                player["source"] = "est_low"

            enriched.append(player)
        return enriched

    # ------------------------------------------------------------------ #
    # Full analysis orchestration                                          #
    # ------------------------------------------------------------------ #

    def build_analysis(
        self,
        opponent_team_id: str,
        season: str,
        my_team_name: str,
        sm: SupabaseManager,
    ) -> dict:
        """Fetch last 10 matches, scrape stats, enrich roster, return analysis dict."""
        logger.info("Building analysis for team %s, season %s", opponent_team_id, season)

        opp_fixtures = self.scrape_opponent_fixtures(opponent_team_id, season)

        # Extract opponent name from any fixture (upcoming or past)
        opponent_team_name = ""
        for f in opp_fixtures:
            is_home_f = f.get("home_team_id") == opponent_team_id
            candidate = f["home_team_name"] if is_home_f else f["away_team_name"]
            if candidate:
                opponent_team_name = candidate
                break

        # Completed = has a numeric match_id (match report link present), not our fallback
        completed = [f for f in opp_fixtures if str(f.get("match_id", "")).isdigit()]

        # Pre-season: no completed matches yet — fall back to previous season
        if not completed:
            prev_season = str(int(season) - 1)
            logger.info(
                "No completed fixtures in season %s — trying previous season %s",
                season, prev_season,
            )
            prev_fixtures = self.scrape_opponent_fixtures(opponent_team_id, prev_season)
            completed = [f for f in prev_fixtures if str(f.get("match_id", "")).isdigit()]
            if not opponent_team_name:
                for f in prev_fixtures:
                    is_home_f = f.get("home_team_id") == opponent_team_id
                    candidate = f["home_team_name"] if is_home_f else f["away_team_name"]
                    if candidate:
                        opponent_team_name = candidate
                        break

        recent_10 = completed[-10:]
        logger.info(
            "Found %d completed fixtures for team %s (using last 10)",
            len(completed), opponent_team_id,
        )

        formation_history: list[dict] = []
        at_accumulator: dict[str, list] = {}

        for fixture in recent_10:
            mid = fixture.get("match_id")
            if not mid:
                continue

            try:
                stats = self.scrape_match_stats(mid)
            except Exception as exc:
                logger.warning("Skipping match %s: %s", mid, exc)
                continue

            # Determine which side the opponent was on using match report team IDs.
            # Prefer this over the fixture table because opponent calendars on PManager
            # always place the viewed team on the left — making home_team_id unreliable.
            report_home_id = stats.get("home_team_id")
            report_away_id = stats.get("away_team_id")
            if report_home_id or report_away_id:
                is_home = report_home_id == opponent_team_id
            else:
                # Fallback: use fixture table (may be wrong for opponent calendars)
                is_home = fixture.get("home_team_id") == opponent_team_id

            side = "home" if is_home else "away"
            formation_history.append({
                "match_id":  mid,
                "formation": stats.get(f"{side}_formation"),
                "style":     stats.get(f"{side}_style"),
            })

            opp_ats = stats.get(f"{side}_ats", {})
            activations = self.parse_at_activation(
                stats.get("commentary", ""), opponent_team_name
            )

            for at_key, enabled in opp_ats.items():
                if at_key not in at_accumulator:
                    at_accumulator[at_key] = []
                enabled_bool = (
                    enabled if isinstance(enabled, bool)
                    else enabled not in ("Normal", "Not Defined", "")
                )
                at_accumulator[at_key].append({
                    "enabled":   enabled_bool,
                    "activated": activations.get(at_key, False),
                    "value":     enabled,  # raw string for setting (e.g. "High", "Zonal")
                })

        # Predict formation and style (most frequent)
        formations = [f["formation"] for f in formation_history if f.get("formation")]
        predicted_formation = max(set(formations), key=formations.count) if formations else None
        styles = [f["style"] for f in formation_history if f.get("style")]
        predicted_style = max(set(styles), key=styles.count) if styles else None

        # Summarise AT patterns
        total = len(recent_10)
        at_patterns: dict[str, dict] = {}
        for at_key, records in at_accumulator.items():
            # Most common raw value (for setting like "High", "Zonal")
            values = [r["value"] for r in records if r.get("value")]
            most_common_value = max(set(values), key=values.count) if values else None
            at_patterns[at_key] = {
                "enabled_count":   sum(1 for r in records if r["enabled"]),
                "activated_count": sum(1 for r in records if r["activated"]),
                "total_matches":   total,
                "most_common_setting": most_common_value,
            }

        # Enrich roster
        roster = self.scrape_opponent_roster(opponent_team_id)

        # Batch fetch skills for all roster players in a single query
        ids = [p["id"] for p in roster]
        res = sm.client.table("players").select("id, skills").in_("id", ids).execute()
        skills_map = {r["id"]: r["skills"] or {} for r in (res.data or [])}

        known_for_archetype = [
            {**p, "skills": skills_map[p["id"]]} for p in roster if p["id"] in skills_map
        ]
        archetype = self.detect_archetype(known_for_archetype)
        logger.info("Opponent archetype: %s", archetype)

        enriched = self.enrich_roster(roster, archetype, sm, skills_map=skills_map)

        return {
            "opponent_team_id":    opponent_team_id,
            "opponent_team_name":  opponent_team_name or f"Team {opponent_team_id}",
            "season":              season,
            "formation_history":   formation_history,
            "predicted_formation": predicted_formation,
            "predicted_style":     predicted_style,
            "at_patterns":         at_patterns,
            "opponent_players":    enriched,
            "team_archetype":      archetype,
        }
