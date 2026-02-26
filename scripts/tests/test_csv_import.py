#!/usr/bin/env python3
"""
Unit tests for CSV import helper.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Import the module under test
import sys
sys.path.insert(0, "..")
from csv_import_helper import CSVImporter, GristAPI


class TestGristAPI:
    """Test GristAPI client."""

    def test_init(self):
        """Test GristAPI initialization."""
        api = GristAPI(
            api_url="http://localhost:8484/api",
            api_key="test-key",
            doc_id="test-doc"
        )
        assert api.api_url == "http://localhost:8484/api"
        assert api.api_key == "test-key"
        assert api.doc_id == "test-doc"
        assert api.headers["Authorization"] == "Bearer test-key"

    @patch("csv_import_helper.requests.get")
    def test_get_tables(self, mock_get):
        """Test get_tables method."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"tables": [{"id": "table1"}, {"id": "table2"}]}
        mock_response.content = b'{"tables": []}'
        mock_get.return_value = mock_response

        api = GristAPI("http://localhost:8484/api", "key", "doc")
        tables = api.get_tables()

        assert len(tables) == 2
        assert tables[0]["id"] == "table1"


class TestCSVImporter:
    """Test CSVImporter class."""

    @pytest.fixture
    def mock_grist_api(self):
        """Create a mock GristAPI."""
        return MagicMock(spec=GristAPI)

    @pytest.fixture
    def importer(self, mock_grist_api):
        """Create a CSVImporter instance."""
        return CSVImporter(mock_grist_api)

    def test_parse_numeric_valid(self, importer):
        """Test parsing valid numeric values."""
        assert importer._parse_numeric("100.50") == 100.50
        assert importer._parse_numeric(100) == 100.0
        assert importer._parse_numeric(100.50) == 100.50

    def test_parse_numeric_invalid(self, importer):
        """Test parsing invalid numeric values."""
        assert importer._parse_numeric(None) is None
        assert importer._parse_numeric("") is None
        assert importer._parse_numeric("N/A") is None
        assert importer._parse_numeric("abc") is None

    def test_parse_datetime_valid(self, importer):
        """Test parsing valid datetime."""
        result = importer._parse_datetime("2026-01-15T09:30:00")
        assert result is not None
        assert "2026-01-15" in result

    def test_parse_datetime_invalid(self, importer):
        """Test parsing invalid datetime."""
        assert importer._parse_datetime(None) is None
        assert importer._parse_datetime("") is None
        assert importer._parse_datetime("invalid") == "invalid"

    def test_transform_to_bronze(self, importer):
        """Test transforming DataFrame to bronze records."""
        # Create test DataFrame
        df = pd.DataFrame([
            {
                "Side": "Buy",
                "Symbol": "AAPL",
                "Name": "Apple Inc",
                "Order Price": 150.0,
                "Order Qty": 10,
                "Order Amount": 1500.0,
                "Status": "Filled",
                "Filled@Avg Price": "10@150.00",
                "Order Time": "Jan 15, 2026 09:30:00 SGT",
                "Order Type": "Limit",
                "Time-in-Force": "Day",
                "Fill Qty": 10,
                "Fill Price": 150.0,
                "Fill Amount": 1500.0,
                "Fill Time": "Jan 15, 2026 09:35:00 SGT",
                "Markets": "US",
                "Currency": "USD",
                "Platform Fees": 0.99,
                "Consumption Tax": 0.10,
                "Settlement Fees": None,
                "Trading Fees": None,
                "Consolidated Audit Trail Fees": None,
                "Commission": 0.99,
                "Trading Fees": None,
                "Clearing Fees": 0.02,
            }
        ])

        records = importer.transform_to_bronze(df, "test.csv")

        assert len(records) == 1
        record = records[0]
        
        # Check required fields
        assert record["Symbol"] == "AAPL"
        assert record["Side"] == "Buy"
        assert record["Source_File"] == "test.csv"
        assert record["Platform"] == "moomoo"
        assert record["Validation_Status"] == "Pending"
        
        # Check numeric fields
        assert record["Fill_Qty"] == 10
        assert record["Fill_Price"] == 150.0
        
        # Check UUID generation
        assert len(record["Import_ID"]) == 36  # UUID length

    def test_transform_preserves_raw_data(self, importer):
        """Test that raw data is preserved."""
        df = pd.DataFrame([{"Side": "Buy", "Symbol": "TEST"}])
        
        records = importer.transform_to_bronze(df, "test.csv")
        
        # Raw_Data should contain JSON
        raw_data = json.loads(records[0]["Raw_Data"])
        assert raw_data["Side"] == "Buy"
        assert raw_data["Symbol"] == "TEST"


class TestCSVImportIntegration:
    """Integration tests (requires Grist instance)."""
    
    @pytest.mark.skip(reason="Requires running Grist instance")
    def test_full_import(self):
        """Test full import flow."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
