"""
Unit tests for the business logic formulas used in main_all_transfer.py
and ai_recommendation.py.

These formulas are not currently extracted to named functions — the tests
document and verify the expected behaviour so that any accidental change
to the calculation is caught.
"""

import pytest

from src import constants


def forecast_sell(estimated_value: float) -> float:
    """Conservative resale price estimate.

    Mirrors the calculation in main_all_transfer.py:
        (estimated_value / FORECAST_SELL_DIVISOR) * FORECAST_SELL_MULTIPLIER
    """
    return (estimated_value / constants.FORECAST_SELL_DIVISOR) * constants.FORECAST_SELL_MULTIPLIER


def roi(estimated_value: float, asking_price: float) -> float:
    """Return-on-investment percentage.

    Mirrors the calculation in main_all_transfer.py:
        ((estimated_value - asking_price) / asking_price) * 100
    """
    if asking_price == 0:
        return 0.0
    return round(((estimated_value - asking_price) / asking_price) * 100, 2)


def value_diff(estimated_value: float, asking_price: float) -> float:
    """Absolute difference between estimated value and asking price."""
    return estimated_value - asking_price


def profit_margin(estimated_value: float, asking_price: float) -> float:
    """Profit margin percentage used for BOT opportunities."""
    if asking_price == 0:
        return 0.0
    diff = estimated_value - asking_price
    return round((diff / asking_price) * 100, 2)


class TestForecastSell:
    def test_standard_value(self) -> None:
        result = forecast_sell(5_000_000)
        assert result == pytest.approx(2_000_000.0)

    def test_zero_value(self) -> None:
        assert forecast_sell(0) == 0.0

    def test_formula_coefficient(self) -> None:
        """Verify the formula uses the constants (not hardcoded literals)."""
        val = 10_000_000
        expected = (val / constants.FORECAST_SELL_DIVISOR) * constants.FORECAST_SELL_MULTIPLIER
        assert forecast_sell(val) == pytest.approx(expected)


class TestROI:
    def test_positive_roi(self) -> None:
        result = roi(5_000_000, 2_000_000)
        assert result == pytest.approx(150.0)

    def test_zero_roi(self) -> None:
        result = roi(2_000_000, 2_000_000)
        assert result == pytest.approx(0.0)

    def test_negative_roi(self) -> None:
        """Asking price exceeds estimated value."""
        result = roi(1_000_000, 2_000_000)
        assert result == pytest.approx(-50.0)

    def test_zero_asking_price_returns_zero(self) -> None:
        """Guard against division by zero."""
        assert roi(5_000_000, 0) == 0.0


class TestValueDiff:
    def test_positive_diff(self) -> None:
        assert value_diff(5_000_000, 2_000_000) == 3_000_000

    def test_negative_diff(self) -> None:
        assert value_diff(1_000_000, 2_000_000) == -1_000_000

    def test_zero_diff(self) -> None:
        assert value_diff(2_000_000, 2_000_000) == 0


class TestProfitMargin:
    def test_standard_margin(self) -> None:
        result = profit_margin(5_000_000, 2_000_000)
        assert result == pytest.approx(150.0)

    def test_zero_asking_price(self) -> None:
        assert profit_margin(5_000_000, 0) == 0.0

    def test_no_profit(self) -> None:
        assert profit_margin(2_000_000, 2_000_000) == pytest.approx(0.0)

    def test_negative_margin(self) -> None:
        result = profit_margin(1_000_000, 2_000_000)
        assert result == pytest.approx(-50.0)
