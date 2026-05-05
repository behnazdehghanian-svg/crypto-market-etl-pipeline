import os
import json
import pytest
from unittest.mock import patch, MagicMock
from src.extractors.coingecko import extract_market_data, save_raw_data

# ─── Fake Data ───────────────────────────────────────────────────────────────
# We use fake data in tests so we don't hit the real API every time
# Real API = slow, costs rate limit, might be down during tests

MOCK_COIN = {
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 76736,
    "market_cap": 1536857757702,
    "market_cap_rank": 1,
    "total_volume": 41328952346,
    "price_change_24h": -1258.82,
    "price_change_percentage_24h": -1.61,
    "circulating_supply": 20021531.0,
    "total_supply": 20021531.0,
    "max_supply": 21000000.0,
    "roi": None,
    "last_updated": "2026-04-27T17:07:55.995Z",
}


# ─── Tests for extract_market_data ───────────────────────────────────────────

class TestExtractMarketData:

    @patch("src.extractors.coingecko.requests.get")
    def test_returns_list(self, mock_get):
        """extract_market_data must return a list"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [MOCK_COIN]

        data, filepath = extract_market_data()

        assert isinstance(data, list)

    @patch("src.extractors.coingecko.requests.get")
    def test_returns_correct_coin_count(self, mock_get):
        """must return same number of coins as API sent"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [MOCK_COIN]

        data, filepath = extract_market_data()

        assert len(data) == 1

    @patch("src.extractors.coingecko.requests.get")
    def test_coin_has_required_fields(self, mock_get):
        """every coin must have these critical fields"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [MOCK_COIN]

        data, filepath = extract_market_data()
        coin = data[0]

        assert "id" in coin
        assert "current_price" in coin
        assert "market_cap" in coin
        assert "last_updated" in coin

    @patch("src.extractors.coingecko.requests.get")
    def test_price_is_positive(self, mock_get):
        """current_price must be a positive number"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [MOCK_COIN]

        data, filepath = extract_market_data()

        assert data[0]["current_price"] > 0

    @patch("src.extractors.coingecko.requests.get")
    def test_saves_file_to_disk(self, mock_get):
        """must save a JSON file to data/raw/"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [MOCK_COIN]

        data, filepath = extract_market_data()

        assert os.path.exists(filepath)

    @patch("src.extractors.coingecko.requests.get")
    def test_saved_file_has_envelope(self, mock_get):
        """saved JSON must have metadata envelope"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [MOCK_COIN]

        data, filepath = extract_market_data()

        with open(filepath) as f:
            saved = json.load(f)

        assert "extracted_at" in saved
        assert "source" in saved
        assert "coin_count" in saved
        assert "data" in saved