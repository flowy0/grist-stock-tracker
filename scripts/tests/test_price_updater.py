#!/usr/bin/env python3
"""
Unit tests for Price Updater.
"""

from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, "..")
from price_updater import YahooFinanceProvider, PriceUpdater, AlphaVantageProvider, FinnhubProvider


class TestYahooFinanceProvider:
    """Test YahooFinanceProvider class."""

    @pytest.fixture
    def provider(self):
        """Create Yahoo Finance provider."""
        return YahooFinanceProvider()

    def test_get_symbol_with_suffix_us(self, provider):
        """Test US symbol has no suffix."""
        result = provider.get_symbol_with_suffix("AAPL", "US")
        assert result == "AAPL"

    def test_get_symbol_with_suffix_sg(self, provider):
        """Test Singapore symbol gets .SI suffix."""
        result = provider.get_symbol_with_suffix("D05", "SG")
        assert result == "D05.SI"

    def test_get_symbol_with_suffix_hk(self, provider):
        """Test Hong Kong symbol gets .HK suffix."""
        result = provider.get_symbol_with_suffix("0700", "HK")
        assert result == "0700.HK"

    def test_get_symbol_with_suffix_uk(self, provider):
        """Test UK symbol gets .L suffix."""
        result = provider.get_symbol_with_suffix("VOD", "UK")
        assert result == "VOD.L"

    @patch("price_updater.requests.Session.get")
    def test_get_price_success(self, mock_get, provider):
        """Test successful price fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "chart": {
                "result": [{
                    "meta": {
                        "regularMarketPrice": 150.50,
                        "currency": "USD",
                        "previousClose": 148.00,
                    }
                }]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_price("AAPL", "US")

        assert result is not None
        assert result["price"] == 150.50
        assert result["currency"] == "USD"
        assert result["change"] == 2.50
        assert result["change_percent"] == pytest.approx(1.689, rel=0.01)
        assert result["source"] == "Yahoo Finance"

    @patch("price_updater.requests.Session.get")
    def test_get_price_no_data(self, mock_get, provider):
        """Test price fetch with no data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"chart": {"result": []}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_price("INVALID", "US")

        assert result is None


class TestAlphaVantageProvider:
    """Test AlphaVantageProvider class."""

    @pytest.fixture
    def provider(self):
        """Create Alpha Vantage provider."""
        return AlphaVantageProvider("test-api-key")

    @patch("price_updater.requests.get")
    def test_get_price_success(self, mock_get, provider):
        """Test successful price fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Global Quote": {
                "05. price": "150.50",
                "09. change": "2.50",
                "10. change percent": "1.689%",
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_price("AAPL")

        assert result is not None
        assert result["price"] == 150.50
        assert result["change"] == 2.50
        assert result["change_percent"] == 1.689
        assert result["source"] == "Alpha Vantage"


class TestFinnhubProvider:
    """Test FinnhubProvider class."""

    @pytest.fixture
    def provider(self):
        """Create Finnhub provider."""
        return FinnhubProvider("test-api-key")

    @patch("price_updater.requests.get")
    def test_get_price_success(self, mock_get, provider):
        """Test successful price fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "c": 150.50,  # Current price
            "pc": 148.00,  # Previous close
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = provider.get_price("AAPL")

        assert result is not None
        assert result["price"] == 150.50
        assert result["change"] == 2.50
        assert result["change_percent"] == pytest.approx(1.689, rel=0.01)
        assert result["source"] == "Finnhub"


class TestPriceUpdater:
    """Test PriceUpdater class."""

    @pytest.fixture
    def mock_grist_api(self):
        """Create mock GristAPI."""
        return MagicMock()

    @pytest.fixture
    def updater(self, mock_grist_api):
        """Create PriceUpdater instance."""
        return PriceUpdater(mock_grist_api)

    def test_get_stocks_active_only(self, updater, mock_grist_api):
        """Test fetching only active stocks."""
        mock_grist_api.get_records.return_value = [
            {"id": 1, "fields": {"Symbol": "AAPL", "Market": "US", "Is_Active": True}},
            {"id": 2, "fields": {"Symbol": "NVDA", "Market": "US", "Is_Active": False}},
            {"id": 3, "fields": {"Symbol": "TSLA", "Market": "US", "Is_Active": True}},
        ]

        stocks = updater.get_stocks(active_only=True)

        assert len(stocks) == 2
        assert stocks[0]["symbol"] == "AAPL"
        assert stocks[1]["symbol"] == "TSLA"

    def test_get_stocks_all(self, updater, mock_grist_api):
        """Test fetching all stocks including inactive."""
        mock_grist_api.get_records.return_value = [
            {"id": 1, "fields": {"Symbol": "AAPL", "Market": "US", "Is_Active": True}},
            {"id": 2, "fields": {"Symbol": "NVDA", "Market": "US", "Is_Active": False}},
        ]

        stocks = updater.get_stocks(active_only=False)

        assert len(stocks) == 2

    def test_get_stocks_filter_by_symbol(self, updater, mock_grist_api):
        """Test filtering stocks by symbol list."""
        mock_grist_api.get_records.return_value = [
            {"id": 1, "fields": {"Symbol": "AAPL", "Market": "US", "Is_Active": True}},
            {"id": 2, "fields": {"Symbol": "NVDA", "Market": "US", "Is_Active": True}},
            {"id": 3, "fields": {"Symbol": "TSLA", "Market": "US", "Is_Active": True}},
        ]

        stocks = updater.get_stocks(symbols=["AAPL", "TSLA"])

        assert len(stocks) == 2
        assert stocks[0]["symbol"] == "AAPL"
        assert stocks[1]["symbol"] == "TSLA"

    def test_stats_initialization(self, updater):
        """Test that stats are initialized correctly."""
        assert updater.stats["processed"] == 0
        assert updater.stats["updated"] == 0
        assert updater.stats["failed"] == 0
        assert updater.stats["skipped"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
