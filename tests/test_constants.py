"""
Sanity-check tests for src.constants.

These tests do not test business logic directly — they verify that constants
are defined, have the expected types, and have sensible values so that a
typo or accidental deletion is caught immediately.
"""

from src import constants


class TestConstantTypes:
    """Verify each constant has the expected Python type."""

    def test_utc_offset_is_int(self) -> None:
        assert isinstance(constants.UTC_OFFSET_HOURS, int)

    def test_max_budget_is_int(self) -> None:
        assert isinstance(constants.MAX_BUDGET, int)

    def test_alert_horizon_hours_is_int(self) -> None:
        assert isinstance(constants.ALERT_HORIZON_HOURS, int)

    def test_top_alerts_limit_is_int(self) -> None:
        assert isinstance(constants.TOP_ALERTS_LIMIT, int)

    def test_final_price_grace_hours_is_int(self) -> None:
        assert isinstance(constants.FINAL_PRICE_GRACE_HOURS, int)

    def test_default_batch_size_is_int(self) -> None:
        assert isinstance(constants.DEFAULT_BATCH_SIZE, int)

    def test_bot_eval_batch_size_is_int(self) -> None:
        assert isinstance(constants.BOT_EVAL_BATCH_SIZE, int)

    def test_max_division_is_int(self) -> None:
        assert isinstance(constants.MAX_DIVISION, int)

    def test_bot_accepted_qualities_is_tuple(self) -> None:
        assert isinstance(constants.BOT_ACCEPTED_QUALITIES, tuple)

    def test_forecast_divisor_is_float(self) -> None:
        assert isinstance(constants.FORECAST_SELL_DIVISOR, float)

    def test_forecast_multiplier_is_float(self) -> None:
        assert isinstance(constants.FORECAST_SELL_MULTIPLIER, float)


class TestConstantValues:
    """Verify constants have sensible values (guard against accidental changes)."""

    def test_utc_offset_is_positive(self) -> None:
        assert constants.UTC_OFFSET_HOURS > 0

    def test_max_budget_is_reasonable(self) -> None:
        assert constants.MAX_BUDGET > 1_000_000, "Budget threshold seems too low"

    def test_alert_horizon_is_positive(self) -> None:
        assert constants.ALERT_HORIZON_HOURS > 0

    def test_batch_size_within_supabase_limits(self) -> None:
        assert 1 <= constants.DEFAULT_BATCH_SIZE <= 1_000

    def test_accepted_qualities_not_empty(self) -> None:
        assert len(constants.BOT_ACCEPTED_QUALITIES) > 0

    def test_accepted_qualities_are_strings(self) -> None:
        assert all(isinstance(q, str) for q in constants.BOT_ACCEPTED_QUALITIES)

    def test_forecast_divisor_is_nonzero(self) -> None:
        assert constants.FORECAST_SELL_DIVISOR != 0.0

    def test_max_division_at_least_one(self) -> None:
        assert constants.MAX_DIVISION >= 1
