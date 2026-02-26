#!/usr/bin/env python3
"""
Unit tests for Bronze to Silver transformation.
"""

from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, "..")
from bronze_to_silver import BronzeToSilverTransformer


class TestBronzeToSilverTransformer:
    """Test BronzeToSilverTransformer class."""

    @pytest.fixture
    def mock_grist_api(self):
        """Create a mock GristAPI."""
        mock = MagicMock()
        mock.get_records.return_value = []
        return mock

    @pytest.fixture
    def transformer(self, mock_grist_api):
        """Create a transformer instance."""
        return BronzeToSilverTransformer(mock_grist_api)

    def test_validate_record_valid_buy(self, transformer):
        """Test validation of valid Buy record."""
        record = {
            "id": 1,
            "fields": {
                "Symbol": "AAPL",
                "Side": "Buy",
                "Fill_Qty": 10,
                "Fill_Price": 150.0,
                "Fill_Amount": 1500.0,
            }
        }
        
        is_valid, errors = transformer.validate_record(record)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_record_missing_symbol(self, transformer):
        """Test validation with missing symbol."""
        record = {
            "id": 1,
            "fields": {
                "Symbol": "",
                "Side": "Buy",
                "Fill_Qty": 10,
                "Fill_Price": 150.0,
            }
        }
        
        is_valid, errors = transformer.validate_record(record)
        assert is_valid is False
        assert any("Symbol" in e for e in errors)

    def test_validate_record_invalid_side(self, transformer):
        """Test validation with invalid side."""
        record = {
            "id": 1,
            "fields": {
                "Symbol": "AAPL",
                "Side": "Invalid",
                "Fill_Qty": 10,
                "Fill_Price": 150.0,
            }
        }
        
        is_valid, errors = transformer.validate_record(record)
        assert is_valid is False
        assert any("Side" in e for e in errors)

    def test_validate_record_negative_quantity(self, transformer):
        """Test validation with negative quantity."""
        record = {
            "id": 1,
            "fields": {
                "Symbol": "AAPL",
                "Side": "Buy",
                "Fill_Qty": -10,
                "Fill_Price": 150.0,
            }
        }
        
        is_valid, errors = transformer.validate_record(record)
        assert is_valid is False
        assert any("Qty" in e or "quantity" in e.lower() for e in errors)

    def test_validate_record_dividend_no_amount(self, transformer):
        """Test validation of Dividend without amount."""
        record = {
            "id": 1,
            "fields": {
                "Symbol": "AAPL",
                "Side": "Dividend",
                "Fill_Qty": 0,
                "Fill_Price": 0,
                "Fill_Amount": 0,
            }
        }
        
        is_valid, errors = transformer.validate_record(record)
        assert is_valid is False
        assert any("Dividend" in e for e in errors)

    def test_check_duplicates_true(self, transformer):
        """Test duplicate detection - duplicate exists."""
        record = {
            "id": 1,
            "fields": {
                "Symbol": "AAPL",
                "Fill_Time": "2026-01-15T09:30:00",
                "Side": "Buy",
            }
        }
        
        existing_silver = [
            {
                "fields": {
                    "Symbol": "AAPL",
                    "Date": "2026-01-15T09:30:00",
                    "Side": "Buy",
                }
            }
        ]
        
        is_duplicate = transformer.check_duplicates(record, existing_silver)
        assert is_duplicate is True

    def test_check_duplicates_false(self, transformer):
        """Test duplicate detection - no duplicate."""
        record = {
            "id": 1,
            "fields": {
                "Symbol": "AAPL",
                "Fill_Time": "2026-01-15T09:30:00",
                "Side": "Buy",
            }
        }
        
        existing_silver = [
            {
                "fields": {
                    "Symbol": "NVDA",  # Different symbol
                    "Date": "2026-01-15T09:30:00",
                    "Side": "Buy",
                }
            }
        ]
        
        is_duplicate = transformer.check_duplicates(record, existing_silver)
        assert is_duplicate is False

    def test_normalize_symbol_stock(self, transformer):
        """Test symbol normalization for regular stock."""
        symbol, asset_type = transformer.normalize_symbol("AAPL", "Apple Inc")
        assert symbol == "AAPL"
        assert asset_type == "Stock"

    def test_normalize_symbol_etf(self, transformer):
        """Test symbol normalization for ETF."""
        symbol, asset_type = transformer.normalize_symbol("VOO", "Vanguard S&P 500 ETF")
        assert symbol == "VOO"
        assert asset_type == "ETF"

    def test_normalize_symbol_reit(self, transformer):
        """Test symbol normalization for REIT."""
        symbol, asset_type = transformer.normalize_symbol("A17U", "Ascendas REIT")
        assert symbol == "A17U"
        assert asset_type == "REIT"

    def test_transform_to_silver(self, transformer):
        """Test transformation to silver format."""
        record = {
            "id": 123,
            "fields": {
                "Symbol": "AAPL",
                "Side": "Buy",
                "Fill_Time": "2026-01-15T09:30:00",
                "Fill_Qty": 10,
                "Fill_Price": 150.0,
                "Fill_Amount": 1500.0,
                "Platform_Fees": 0.99,
                "Tax": 0.10,
                "Platform": "moomoo",
            }
        }
        
        silver_record = transformer.transform_to_silver(record, "AAPL")
        
        assert silver_record["Bronze_Ref"] == 123
        assert silver_record["Symbol"] == "AAPL"
        assert silver_record["Side"] == "Buy"
        assert silver_record["Fill_Qty"] == 10
        assert silver_record["Fill_Price"] == 150.0
        assert silver_record["Platform"] == "moomoo"
        assert "Transaction_ID" in silver_record
        assert len(silver_record["Transaction_ID"]) == 36  # UUID

    def test_stats_initialization(self, transformer):
        """Test that stats are initialized correctly."""
        assert transformer.stats["bronze_processed"] == 0
        assert transformer.stats["silver_created"] == 0
        assert transformer.stats["stocks_created"] == 0
        assert transformer.stats["errors"] == 0
        assert transformer.stats["duplicates"] == 0


class TestIntegration:
    """Integration tests."""

    @pytest.mark.skip(reason="Requires running Grist instance")
    def test_full_transformation(self):
        """Test full Bronze to Silver transformation."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
