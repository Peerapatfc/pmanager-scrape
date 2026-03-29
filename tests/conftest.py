"""
Shared pytest fixtures for pmanager-scrape tests.
"""

import pytest


@pytest.fixture
def sample_player() -> dict:
    """A minimal player record as returned by the scraper."""
    return {
        "id": "12345",
        "name": "Test Player",
        "position": "MF",
        "age": "25",
        "Quality": "Excellent",
        "Potential": "World Class",
        "estimated_value": 5_000_000,
        "asking_price": 2_000_000,
        "bids_count": "3",
        "bids_avg": "2500000",
        "deadline": "Today 14:30",
        "url": "https://www.pmanager.org/ver_jogador.asp?jog_id=12345",
    }


@pytest.fixture
def sample_transfer_listing() -> dict:
    """A minimal transfer listing record as stored in Supabase."""
    return {
        "id": "12345",
        "estimated_value": 5_000_000,
        "asking_price": 2_000_000,
        "value_diff": 3_000_000,
        "roi": 150.0,
        "forecast_sell": 2_000_000.0,
        "forecast_profit": 0.0,
        "deadline": "Today 14:30",
        "url": "https://www.pmanager.org/comprar_jog_lista.asp?jg_id=12345",
        "last_updated": "2026-03-29 10:00:00",
    }
