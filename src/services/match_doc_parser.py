"""
Parser for the Round Compiler source document format.

Extracts structured match data (formations, AT flags, stats, goalscorers)
from the Markdown source documents produced by RoundCompiler or assembled
manually.  Returns a dict ready for upsert into league_match_results.
"""

from __future__ import annotations

import re
from typing import Any


def _safe_key(text: str) -> str:
    return re.sub(r"[^\w\-]", "_", text).strip("_") or "Unknown"


def _round_key(date: str, competition: str) -> str:
    return f"{date[:10]}___{_safe_key(competition)}"


# ---------------------------------------------------------------------------
# Top-level parse
# ---------------------------------------------------------------------------

def parse_source_doc(text: str) -> dict[str, Any]:
    """Parse a RoundCompiler source document into structured data.

    Args:
        text: Full Markdown text of the source document.

    Returns:
        Dict with keys:
            competition (str), date (str), round_key (str),
            matches (list[dict]) — one per match section found.

    Raises:
        ValueError: If the document is missing the required header fields.
    """
    competition = _parse_competition(text)
    date        = _parse_date(text)

    if not competition:
        raise ValueError("Could not find **Competition:** in source document")
    if not date:
        raise ValueError("Could not find **Date:** (YYYY-MM-DD) in source document")

    rkey    = _round_key(date, competition)
    matches = _parse_matches(text, competition, date, rkey)

    return {
        "competition": competition,
        "date":        date,
        "round_key":   rkey,
        "matches":     matches,
    }


# ---------------------------------------------------------------------------
# Header fields
# ---------------------------------------------------------------------------

def _parse_competition(text: str) -> str:
    m = re.search(r"\*\*Competition:\*\*\s*(.+)", text)
    return m.group(1).strip() if m else ""


def _parse_date(text: str) -> str:
    m = re.search(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Match section splitting
# ---------------------------------------------------------------------------

_MATCH_HEADER_RE = re.compile(
    r"^##\s+(.+?)\s+(\d+)\s*[-–]\s*(\d+)\s+(.+?)\s*$",
    re.MULTILINE,
)


def _parse_matches(
    text: str,
    competition: str,
    date: str,
    round_key: str,
) -> list[dict[str, Any]]:
    """Split doc into per-match sections and parse each one."""
    # Find all match-section start positions
    headers = list(_MATCH_HEADER_RE.finditer(text))
    if not headers:
        return []

    # Find where PManager context section starts so we stop before it
    context_start = len(text)
    m = re.search(r"^##\s+PManager Game Rules Context", text, re.MULTILINE)
    if m:
        context_start = m.start()

    matches = []
    for i, header in enumerate(headers):
        section_start = header.start()
        if section_start >= context_start:
            break
        section_end = headers[i + 1].start() if i + 1 < len(headers) else context_start
        section_text = text[section_start:section_end]

        home_team  = header.group(1).strip()
        home_score = int(header.group(2))
        away_score = int(header.group(3))
        away_team  = header.group(4).strip()

        matches.append(
            _parse_match_section(
                section_text,
                home_team, away_team,
                home_score, away_score,
                competition, date, round_key,
            )
        )

    return matches


# ---------------------------------------------------------------------------
# Single match section parser
# ---------------------------------------------------------------------------

def _parse_match_section(
    section: str,
    home_team: str,
    away_team: str,
    home_score: int,
    away_score: int,
    competition: str,
    date: str,
    round_key: str,
) -> dict[str, Any]:
    game_id = _parse_game_id(section)

    home_formation, home_style, home_at = _parse_tactical_line(section, home_team)
    away_formation, away_style, away_at = _parse_tactical_line(section, away_team)

    stats       = _parse_stats(section)
    goalscorers = _parse_goalscorers(section, home_team, away_team)

    return {
        "game_id":        game_id,
        "round_key":      round_key,
        "match_date":     date,
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


# ---------------------------------------------------------------------------
# Game ID
# ---------------------------------------------------------------------------

def _parse_game_id(section: str) -> str | None:
    m = re.search(r"Game\s+ID\s+(\d+)", section)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Tactical line parser
# ---------------------------------------------------------------------------

# Matches:  **TeamName:** formation · style | ATs: Key: Val | ...
_TACTICAL_LINE_RE = re.compile(
    r"-\s+\*\*(.+?):\*\*\s+(.+?)\s+[·•]\s+(.+?)\s+\|\s+ATs:\s+(.+)",
)

_AT_PAIR_RE = re.compile(r"([^:]+):\s*([^|]+)")

_AT_KEY_MAP = {
    "marking":        "marking",
    "pressing":       "pressing",
    "first time":     "first_time",
    "high balls":     "high_balls",
    "long shots":     "long_shots",
    "one on ones":    "one_on_ones",
    "offside trap":   "offside_trap",
    "counter attack": "counter_attack",
}


def _parse_tactical_line(
    section: str,
    team_name: str,
) -> tuple[str | None, str | None, dict[str, Any]]:
    """Return (formation, style, at_dict) for a given team in the Tactical subsection."""
    # Search only within the Tactical subsection
    tac_match = re.search(r"###\s+Tactical\s*\n(.*?)(?=\n###|\Z)", section, re.DOTALL)
    search_text = tac_match.group(1) if tac_match else section

    for line in search_text.splitlines():
        m = _TACTICAL_LINE_RE.match(line.strip())
        if not m:
            continue
        line_team = m.group(1).strip()
        if line_team.lower() != team_name.lower():
            continue

        formation = m.group(2).strip()
        style     = m.group(3).strip()
        at_raw    = m.group(4)

        at_dict: dict[str, Any] = {}
        for piece in at_raw.split("|"):
            piece = piece.strip()
            if ":" not in piece:
                continue
            raw_key, _, raw_val = piece.partition(":")
            key = raw_key.strip().lower()
            val = raw_val.strip()
            mapped = _AT_KEY_MAP.get(key)
            if mapped:
                if val.lower() == "true":
                    at_dict[mapped] = True
                elif val.lower() == "false":
                    at_dict[mapped] = False
                else:
                    at_dict[mapped] = val

        return formation, style, at_dict

    return None, None, {}


# ---------------------------------------------------------------------------
# Stats parser  (from Commentary Excerpt block)
# ---------------------------------------------------------------------------

# Stats appear in a dense block like:
#   Possession 78% 22% Shots 3 10 Shots on Goal 2 7 Effectiveness 33% 40%
#   Short Passes (%) 91% 37% Long Passes (%) 9% 63% Fouls 31 28

_STAT_PATTERNS: list[tuple[str, str, str]] = [
    # (stat_key_home, stat_key_away, regex)
    ("possession_home", "possession_away",
     r"Possession\s+(\d+)%\s+(\d+)%"),
    ("shots_home", "shots_away",
     r"(?<!\bShots on Goal\b)Shots\s+(\d+)\s+(\d+)(?!\s+on)"),
    ("shots_on_goal_home", "shots_on_goal_away",
     r"Shots on Goal\s+(\d+)\s+(\d+)"),
    ("effectiveness_home", "effectiveness_away",
     r"Effectiveness\s+(\d+)%\s+(\d+)%"),
    ("short_passes_pct_home", "short_passes_pct_away",
     r"Short Passes\s*\(%\)\s+(\d+)%\s+(\d+)%"),
    ("long_passes_pct_home", "long_passes_pct_away",
     r"Long Passes\s*\(%\)\s+(\d+)%\s+(\d+)%"),
    ("fouls_home", "fouls_away",
     r"Fouls\s+(\d+)\s+(\d+)"),
]

# Separate pattern for plain "Shots N M" that isn't "Shots on Goal"
_SHOTS_RE = re.compile(r"\bShots\s+(\d+)\s+(\d+)")
_SHOTS_OG_RE = re.compile(r"\bShots on Goal\s+(\d+)\s+(\d+)")


def _parse_stats(section: str) -> dict[str, Any]:
    # Focus on Commentary Excerpt subsection for the dense stats block
    comm_match = re.search(
        r"###\s+Commentary Excerpt\s*\n(.*?)(?=\n###|\Z)", section, re.DOTALL
    )
    search_text = comm_match.group(1) if comm_match else section

    stats: dict[str, Any] = {}

    for key_h, key_a, pattern in _STAT_PATTERNS:
        # Skip the ambiguous "Shots" pattern — handle separately below
        if key_h == "shots_home":
            continue
        m = re.search(pattern, search_text)
        if m:
            stats[key_h] = int(m.group(1))
            stats[key_a] = int(m.group(2))

    # Shots on goal first, then plain shots (avoid overlap)
    m_og = _SHOTS_OG_RE.search(search_text)
    if m_og:
        stats["shots_on_goal_home"] = int(m_og.group(1))
        stats["shots_on_goal_away"] = int(m_og.group(2))

    # For plain "Shots", find first occurrence that isn't part of "Shots on Goal"
    for m_s in _SHOTS_RE.finditer(search_text):
        # Confirm the match isn't inside "Shots on Goal"
        if "on Goal" in search_text[m_s.start():m_s.start() + 20]:
            continue
        stats["shots_home"] = int(m_s.group(1))
        stats["shots_away"] = int(m_s.group(2))
        break

    return stats


# ---------------------------------------------------------------------------
# Goalscorer parser  (from Commentary Excerpt)
# ---------------------------------------------------------------------------

# Commentary format (after header block):
#   Home scorers listed, then away scorers — each as "PlayerName (min', min')"
# The boundary is the "Game ID" line; before it are scorers, after it are stats.

_SCORER_RE = re.compile(
    r"([A-ZÁÀÂÄÃÅÆÇÉÈÊËÍÌÎÏÑÓÒÔÖÕØÚÙÛÜÝŸŠŽŒ][^\(]+?)\s+\((\d+(?:',?\s*\d+)*')\)",
)


def _parse_goalscorers(
    section: str,
    home_team: str,
    away_team: str,
) -> list[dict[str, Any]]:
    """Extract goalscorers from the Commentary Excerpt.

    The commentary block lists all scorers before the "Game ID" line.
    Team attribution is done by position: home scorers first, then away.
    When score splits are known we assign exactly (home_score) goals to home.
    """
    comm_match = re.search(
        r"###\s+Commentary Excerpt\s*\n(.*?)(?=\n###|\Z)", section, re.DOTALL
    )
    if not comm_match:
        return []

    comm_text = comm_match.group(1)

    # Only the portion before "Game ID"
    gid_pos = re.search(r"Game\s+ID\s+\d+", comm_text)
    scorer_text = comm_text[: gid_pos.start()] if gid_pos else comm_text[:500]

    goals: list[dict[str, Any]] = []
    for m in _SCORER_RE.finditer(scorer_text):
        player = m.group(1).strip()
        minutes_raw = m.group(2)
        for min_str in re.findall(r"\d+", minutes_raw):
            goals.append({"player": player, "minute": int(min_str), "team": None})

    # Attribute teams using score line from header.
    # PManager commentary lists goals first then substitutions (same format).
    # Slice to total_goals to drop substitution entries.
    header_m = re.search(r"##\s+.+?\s+(\d+)\s*[-–]\s*(\d+)\s+", section)
    if header_m:
        home_score = int(header_m.group(1))
        away_score = int(header_m.group(2))
        goals = goals[: home_score + away_score]
        for i, g in enumerate(goals):
            g["team"] = home_team if i < home_score else away_team

    return goals
