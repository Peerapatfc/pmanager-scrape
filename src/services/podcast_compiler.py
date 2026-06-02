"""
Podcast source document compiler.

Aggregates post-match data from Supabase (match_reports, upcoming_fixtures,
fixture_analysis, my_squad, team_info) and embeds relevant manual sections to
produce a structured Markdown source document ready for the podcast generator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.logger import logger

# Sections of the game manual that provide podcast context.
# Always included: tactics (13) and match engine (14).
# League/cup-specific sections are added based on match_type.
_MANUAL_DIR = Path(__file__).parent.parent.parent / "docs" / "manual" / "sections"

_ALWAYS_INCLUDE = ["section_13.md", "section_14.md", "section_34.md"]
_LEAGUE_SECTIONS = ["section_20.md"]
_CUP_SECTIONS    = ["section_22.md"]
_CUP_KEYWORDS    = ("cup", "taca", "taça", "copa", "national", "knockout")

# Maximum characters to embed from each manual section to keep the doc concise
_MAX_SECTION_CHARS = 3000


def _read_manual_section(filename: str) -> str:
    path = _MANUAL_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning("Manual section not found: %s", path)
        return ""


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0] + "\n\n[...section truncated...]"


class PodcastCompiler:
    """Compiles all match data into a structured Markdown source document."""

    def __init__(self, match_id: str, sm: Any) -> None:
        """
        Args:
            match_id: PManager jogo_id.
            sm: SupabaseManager instance for data fetching.
        """
        self.match_id = match_id
        self.sm = sm

    def compile(self, fixture_override: dict | None = None) -> str:
        """Fetch all data and return the compiled Markdown source document.

        Args:
            fixture_override: If provided, use this dict as fixture data instead
                              of querying upcoming_fixtures. Used for round matches
                              (other teams in the same league round) that don't have
                              a row in upcoming_fixtures. Reaction defaults to neutral
                              and next fixture section is omitted.
        """
        report = self.sm.get_match_report(self.match_id)
        is_round_match = fixture_override is not None

        if is_round_match:
            fixture          = fixture_override
            team_info        = None
            fixture_analysis = None
            next_fixture     = None
        else:
            fixture   = self.sm.get_fixture_by_match_id(self.match_id)
            team_info = self.sm.get_team_info()

            if not report or not fixture:
                raise ValueError(f"Missing match data for match_id={self.match_id}")

            # Opponent team analysis (pre-match scouting, may be None)
            # team_info has no team_id — derive opponent from fixture
            my_team_name = (team_info or {}).get("team_name", "")
            home_name    = fixture.get("home_team_name", "")
            if my_team_name and home_name == my_team_name:
                opponent_id = report.get("away_team_id")
            else:
                opponent_id = report.get("home_team_id")
            fixture_analysis = self.sm.get_fixture_analysis(opponent_id) if opponent_id else None
            next_fixture     = self.sm.get_next_fixture(fixture.get("match_date", ""))

        if not report:
            raise ValueError(f"Missing match data for match_id={self.match_id}")

        match_type = (fixture.get("match_type") or "").lower()
        is_cup = any(kw in match_type for kw in _CUP_KEYWORDS)

        sections: list[str] = [
            self._section_header(report, fixture, team_info),
            self._section_recap(report, fixture),
            self._section_tactical(report, fixture_analysis),
            self._section_ratings(report),
            self._section_matchday_context(report, fixture),
            self._section_reaction(report, fixture, team_info),
            self._section_next_fixture(next_fixture, fixture_analysis),
            self._section_game_context(is_cup),
            self._section_key_stats_summary(report, fixture),
        ]

        doc = "\n\n---\n\n".join(s for s in sections if s.strip())
        logger.info("Compiled source document: %d characters", len(doc))
        return doc

    # ------------------------------------------------------------------ #
    # Segment builders                                                     #
    # ------------------------------------------------------------------ #

    def _section_header(self, report: dict, fixture: dict, team_info: dict | None) -> str:
        home  = fixture.get("home_team_name", "Home Team")
        away  = fixture.get("away_team_name", "Away Team")
        hs    = report.get("home_score")
        as_   = report.get("away_score")
        score = f"{hs} - {as_}" if hs is not None and as_ is not None else fixture.get("result", "?-?")
        date  = (fixture.get("match_date") or "")[:10]
        mtype = fixture.get("match_type") or "League"
        season = fixture.get("season", "")
        division = (team_info or {}).get("current_division", "")

        lines = [
            "# Match Report Source Document",
            "",
            f"**Competition:** {mtype}  ",
            f"**Season:** {season}  ",
            f"**Division:** {division}  ",
            f"**Date:** {date}  ",
            f"**Match:** {home} vs {away}  ",
            f"**Final Score:** {home} {score} {away}",
        ]
        return "\n".join(lines)

    def _section_recap(self, report: dict, fixture: dict) -> str:
        home = fixture.get("home_team_name", "Home Team")
        away = fixture.get("away_team_name", "Away Team")
        hs   = report.get("home_score")
        as_  = report.get("away_score")
        score = f"{hs}-{as_}" if hs is not None and as_ is not None else fixture.get("result", "?-?")

        lines = [f"## Match Recap\n\n**{home} {score} {away}**\n"]

        # Goals
        goals = report.get("goalscorers") or []
        if goals:
            lines.append("### Goals\n")
            for g in goals:
                min_txt = f"{g['minute']}'" if g.get("minute") else ""
                team    = g.get("team") or ""
                player  = g.get("player_name") or "Unknown"
                lines.append(f"- {min_txt} **{player}** ({team})")
            lines.append("")

        # Substitutions
        subs = report.get("substitutions") or []
        if subs:
            lines.append("### Substitutions\n")
            for s in subs:
                min_txt = f"{s['minute']}'" if s.get("minute") else ""
                lines.append(f"- {min_txt} {s.get('off', '?')} → {s.get('on', '?')} ({s.get('team', '')})")
            lines.append("")

        # Commentary excerpt (first 1500 chars)
        commentary = (report.get("commentary") or "").strip()
        if commentary:
            lines.append("### Match Commentary (excerpt)\n")
            lines.append(commentary[:1500])
            if len(commentary) > 1500:
                lines.append("\n[...commentary continues...]")

        return "\n".join(lines)

    def _section_tactical(self, report: dict, fixture_analysis: dict | None) -> str:
        lines = ["## Tactical Breakdown\n"]

        home_f = report.get("home_formation") or "Unknown"
        away_f = report.get("away_formation") or "Unknown"
        home_s = report.get("home_style") or "Unknown"
        away_s = report.get("away_style") or "Unknown"
        home_at = report.get("home_at_settings") or {}
        away_at = report.get("away_at_settings") or {}

        lines.append(f"**Home Formation:** {home_f} | **Style:** {home_s}")
        lines.append(f"**Away Formation:** {away_f} | **Style:** {away_s}\n")

        def fmt_ats(ats: dict) -> str:
            if not ats:
                return "_No AT data_"
            items = []
            for k, v in ats.items():
                items.append(f"{k.replace('_', ' ').title()}: {v}")
            return " | ".join(items)

        lines.append(f"**Home ATs:** {fmt_ats(home_at)}")
        lines.append(f"**Away ATs:** {fmt_ats(away_at)}\n")

        # vs pre-match prediction
        if fixture_analysis:
            pred_f = fixture_analysis.get("predicted_formation")
            pred_s = fixture_analysis.get("predicted_style")
            lines.append("### Pre-Match Scouting Prediction (Opponent)\n")
            lines.append(f"- Predicted formation: **{pred_f or 'Unknown'}**")
            lines.append(f"- Predicted style: **{pred_s or 'Unknown'}**")

            at_patterns = fixture_analysis.get("at_patterns") or {}
            if at_patterns:
                lines.append("\n**Opponent AT History (last 10 matches):**\n")
                for at_key, data in at_patterns.items():
                    enabled  = data.get("enabled_count", 0)
                    total    = data.get("total_matches", 10)
                    setting  = data.get("most_common_setting", "")
                    lines.append(
                        f"- {at_key.replace('_', ' ').title()}: enabled {enabled}/{total}"
                        + (f" (typical: {setting})" if setting else "")
                    )

        return "\n".join(lines)

    def _section_ratings(self, report: dict) -> str:
        lines = ["## Player Ratings & Standouts\n"]

        mom = report.get("man_of_match")
        if mom:
            lines.append(f"**Man of the Match:** {mom}\n")

        ratings = report.get("player_ratings") or {}
        if ratings:
            sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
            lines.append("| Player | Rating |")
            lines.append("|--------|--------|")
            for name, rating in sorted_ratings:
                lines.append(f"| {name} | {rating:.1f} |")
        else:
            lines.append("_No player ratings available for this match._")

        return "\n".join(lines)

    def _section_matchday_context(self, report: dict, fixture: dict) -> str:
        results = report.get("league_matchday_results") or []
        if not results:
            return ""

        match_type = (fixture.get("match_type") or "").lower()
        is_cup = any(kw in match_type for kw in _CUP_KEYWORDS)
        heading = "Cup Round Results" if is_cup else "Other Results This Matchday"

        lines = [f"## {heading}\n"]
        for r in results:
            home = r.get("home_team") or r.get("home_team_name", "?")
            away = r.get("away_team") or r.get("away_team_name", "?")
            res  = r.get("result", "?")
            lines.append(f"- {home} **{res}** {away}")

        return "\n".join(lines)

    def _section_reaction(self, report: dict, fixture: dict, team_info: dict | None) -> str:
        hs = report.get("home_score")
        as_ = report.get("away_score")
        home = fixture.get("home_team_name", "Home Team")
        away = fixture.get("away_team_name", "Away Team")
        my_team = (team_info or {}).get("team_name", "")

        if hs is None or as_ is None:
            outcome_label = "draw"
        elif home == my_team:
            outcome_label = "win" if hs > as_ else ("draw" if hs == as_ else "loss")
        elif away == my_team:
            outcome_label = "win" if as_ > hs else ("draw" if hs == as_ else "loss")
        else:
            outcome_label = "neutral"

        _quotes = {
            "win":  (
                "We worked hard for that result. The players showed great character today "
                "and I'm delighted with the performance.",
                "Credit to the team — we executed the game plan well. "
                "Three points is what we came for."
            ),
            "draw": (
                "A point is a point. We had chances to win it, but we have to be honest "
                "about where we are right now.",
                "Both sides had spells in the game. I think a draw was a fair result in the end."
            ),
            "loss": (
                "It's a disappointing result. We need to look at the goals we conceded "
                "and improve in those areas quickly.",
                "Credit to the opposition — they were clinical when it mattered. "
                "We'll learn from this and bounce back."
            ),
            "neutral": (
                "Both managers will take different things from this match.",
                "An absorbing contest — the tactical battle was fascinating to watch."
            ),
        }

        home_quote, away_quote = _quotes.get(outcome_label, _quotes["neutral"])

        lines = [
            "## Post-Match Reaction\n",
            f"**{home} Manager:**",
            f"> \"{home_quote}\"\n",
            f"**{away} Manager:**",
            f"> \"{away_quote}\"",
        ]
        return "\n".join(lines)

    def _section_next_fixture(self, next_fixture: dict | None, fixture_analysis: dict | None) -> str:
        if not next_fixture:
            return ""

        home = next_fixture.get("home_team_name", "TBD")
        away = next_fixture.get("away_team_name", "TBD")
        date = (next_fixture.get("match_date") or "")[:10]
        mtype = next_fixture.get("match_type") or "League"

        lines = [
            "## Next Fixture Preview\n",
            f"**{mtype}:** {home} vs {away}",
            f"**Date:** {date}\n",
        ]

        if fixture_analysis:
            pred_f = fixture_analysis.get("predicted_formation")
            archetype = fixture_analysis.get("team_archetype")
            lines.append("**Scouting Notes:**")
            if pred_f:
                lines.append(f"- Opponent typically lines up: **{pred_f}**")
            if archetype:
                lines.append(f"- Team archetype: **{archetype}**")

        return "\n".join(lines)

    def _section_key_stats_summary(self, report: dict, fixture: dict) -> str:
        """Compact stats block — optimised for NotebookLM Slides extraction."""
        home = fixture.get("home_team_name", "Home")
        away = fixture.get("away_team_name", "Away")
        hs   = report.get("home_score")
        as_  = report.get("away_score")
        score = f"{hs}-{as_}" if hs is not None and as_ is not None else fixture.get("result", "?")

        lines = [
            "## Key Stats Summary\n",
            f"- **Final Score:** {home} {score} {away}",
        ]

        mom = report.get("man_of_match")
        if mom:
            lines.append(f"- **Man of the Match:** {mom}")

        goals = report.get("goalscorers") or []
        if goals:
            goal_parts = []
            for g in goals:
                min_txt = f"{g['minute']}'" if g.get("minute") else ""
                player  = g.get("player_name") or "?"
                team    = g.get("team") or ""
                goal_parts.append(f"{player} {min_txt} ({team})".strip())
            lines.append(f"- **Goals:** {', '.join(goal_parts)}")

        home_f = report.get("home_formation") or "?"
        away_f = report.get("away_formation") or "?"
        home_s = report.get("home_style") or "?"
        away_s = report.get("away_style") or "?"
        lines.append(f"- **Formations:** {home} {home_f} ({home_s}) | {away} {away_f} ({away_s})")

        subs = report.get("substitutions") or []
        lines.append(f"- **Substitutions:** {len(subs)}")

        return "\n".join(lines)

    def _section_game_context(self, is_cup: bool) -> str:
        """Embed relevant manual sections as game rules context."""
        filenames = _ALWAYS_INCLUDE[:]
        if is_cup:
            filenames += _CUP_SECTIONS
        else:
            filenames += _LEAGUE_SECTIONS

        lines = ["## PManager Game Rules Context\n"]
        lines.append(
            "_The following excerpts from the PManager game manual provide context "
            "for accurate commentary on tactics, match engine, and competition rules._\n"
        )

        for fname in filenames:
            content = _read_manual_section(fname)
            if content:
                title = content.splitlines()[0].lstrip("# ").strip() if content.splitlines() else fname
                lines.append(f"### {title}\n")
                lines.append(_truncate(content, _MAX_SECTION_CHARS))
                lines.append("")

        return "\n".join(lines)
