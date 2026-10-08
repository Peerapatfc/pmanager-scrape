"""Tests for the daily skill snapshot rows."""

from src.scrapers.squad import SKILL_COLUMNS
from src.services.skill_history import build_skill_history_rows


def _record(player_id: str, base: int, age: int = 25) -> dict:
    return {
        "player_id": player_id,
        "age": age,
        **{name: base + i for i, name in enumerate(SKILL_COLUMNS)},
    }


def test_new_player_gets_a_row_in_game_column_order() -> None:
    rows = build_skill_history_rows([_record("7", 1)], {}, "2026-10-08")
    assert rows == [
        {"player_id": 7, "day": "2026-10-08", "skills": list(range(1, 13)), "age": 25}
    ]


def test_unchanged_skills_add_nothing() -> None:
    latest = {7: list(range(1, 13))}
    assert build_skill_history_rows([_record("7", 1)], latest, "2026-10-08") == []


def test_changed_skill_adds_a_row() -> None:
    latest = {7: [0] + list(range(2, 13))}
    rows = build_skill_history_rows([_record("7", 1)], latest, "2026-10-08")
    assert len(rows) == 1 and rows[0]["skills"][0] == 1


def test_unreadable_all_zero_player_is_skipped() -> None:
    zero = {"player_id": "9", "age": 30, **{name: 0 for name in SKILL_COLUMNS}}
    assert build_skill_history_rows([zero], {}, "2026-10-08") == []
