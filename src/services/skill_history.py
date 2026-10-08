"""
Daily skill snapshots for the PManager Helper extension.

The extension keeps a per-player skill history in the ``ext_skill_history``
table (one row per player and day, ``skills`` = the 12 skills in game column
order). This module builds the rows the squad sync adds so the history keeps
growing on days nobody opens the Squad page.
"""

from __future__ import annotations

from typing import Any

from src.scrapers.squad import SKILL_COLUMNS


def build_skill_history_rows(
    records: list[dict[str, Any]],
    latest: dict[int, list[int]],
    day: str,
) -> list[dict[str, Any]]:
    """Rows to upsert into ``ext_skill_history`` for one squad snapshot.

    Mirrors the extension: a player gets a new row only when his 12 skills
    differ from the latest stored ones (or he has none yet), so an unchanged
    day adds nothing. Players whose skills could not be read (all zero) are
    skipped.

    Args:
        records: Squad scraper output (``player_id``, ``age`` and one key
            per skill in :data:`SKILL_COLUMNS`).
        latest: Latest stored skills per player id.
        day: Snapshot date, ``YYYY-MM-DD`` (UTC, as the extension uses).

    Returns:
        List of row dicts ready for upsert.
    """
    rows: list[dict[str, Any]] = []
    for r in records:
        skills = [int(r.get(name, 0)) for name in SKILL_COLUMNS]
        if not any(skills):
            continue
        player_id = int(r["player_id"])
        if latest.get(player_id) == skills:
            continue
        rows.append(
            {"player_id": player_id, "day": day, "skills": skills, "age": r.get("age")}
        )
    return rows
