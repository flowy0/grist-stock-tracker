#!/usr/bin/env python3
"""
CSV Import Helper for Grist Stock Tracker

This script imports moomoo CSV export files into the bronze_transactions table
in Grist. It stores raw data without modification (Medallion Architecture - Bronze layer).

Usage:
    uv run python csv_import_helper.py <csv_file> [--doc-id <id>] [--api-key <key>] [--env <env>]
    uv run python csv_import_helper.py samples/sample-minimal-test.csv
    uv run python csv_import_helper.py samples/test.csv --env test

Environment Variables:
    ENVIRONMENT: Current environment (dev | test | production)
    GRIST_DOC_ID: Grist document ID (dev)
    GRIST_API_KEY: Grist API key (dev)
    TEST_GRIST_DOC_ID: Grist document ID (test)
    TEST_GRIST_API_KEY: Grist API key (test)
    PROD_GRIST_DOC_ID: Grist document ID (production)
    PROD_GRIST_API_KEY: Grist API key (production)
"""

import argparse
import csv
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from config import Config, get_config

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GristAPI:
    """Client for interacting with Grist API."""

    def __init__(self, api_url: str, api_key: str, doc_id: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.doc_id = doc_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> dict:
        """Make a request to the Grist API."""
        url = f"{self.api_url}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def get_tables(self) -> list:
        """Get list of tables in the document."""
        endpoint = f"docs/{self.doc_id}/tables"
        result = self._make_request("GET", endpoint)
        return result.get("tables", [])

    def table_exists(self, table_id: str) -> bool:
        """Check if a table exists (case-insensitive)."""
        tables = self.get_tables()
        existing_ids = [t.get("id", "").lower() for t in tables]
        return table_id.lower() in existing_ids

    def get_records(self, table_id: str) -> list:
        """Get records from a table."""
        endpoint = f"docs/{self.doc_id}/tables/{table_id}/records"
        result = self._make_request("GET", endpoint)
        return result.get("records", [])

    def add_records(self, table_id: str, records: list) -> dict:
        """Add records to a table."""
        endpoint = f"docs/{self.doc_id}/tables/{table_id}/records"
        data = {"records": [{"fields": record} for record in records]}
        return self._make_request("POST", endpoint, data)


class CSVImporter:
    """Import CSV files into Grist bronze_transactions table."""

    def __init__(self, grist_api: GristAPI):
        self.grist_api = grist_api

    def read_csv(self, file_path: str) -> pd.DataFrame:
        """Read CSV file into DataFrame."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        logger.info(f"Reading CSV file: {file_path}")
        
        # Read CSV with moomoo format
        df = pd.read_csv(file_path, skipinitialspace=True)
        logger.info(f"Loaded {len(df)} rows from CSV")
        return df

    def transform_to_bronze(self, df: pd.DataFrame, source_file: str, source: str = "moomoo") -> list:
        """Transform DataFrame to bronze_transactions format."""
        records = []
        import_date = datetime.now().isoformat()

        for _, row in df.iterrows():
            # Generate unique import ID
            import_id = str(uuid.uuid4())
            
            # Store raw data as JSON
            raw_data = row.to_json()

            # Map CSV columns to bronze table columns
            record = {
                "Import_ID": import_id,
                "Import_Date": import_date,
                "Source_File": source_file,
                "Raw_Data": raw_data,
                "Side": str(row.get("Side", "")).strip(),
                "Symbol": str(row.get("Symbol", "")).strip().upper(),
                "Name": str(row.get("Name", "")).strip(),
                "Order_Price": self._parse_numeric(row.get("Order Price")),
                "Order_Qty": self._parse_numeric(row.get("Order Qty")),
                "Order_Amount": self._parse_numeric(row.get("Order Amount")),
                "Status": str(row.get("Status", "")).strip(),
                "Filled_Avg_Price": str(row.get("Filled@Avg Price", "")).strip(),
                "Order_Time": self._parse_datetime(row.get("Order Time")),
                "Order_Type": str(row.get("Order Type", "")).strip(),
                "Time_in_Force": str(row.get("Time-in-Force", "")).strip(),
                "Fill_Qty": self._parse_numeric(row.get("Fill Qty")),
                "Fill_Price": self._parse_numeric(row.get("Fill Price")),
                "Fill_Amount": self._parse_numeric(row.get("Fill Amount")),
                "Fill_Time": self._parse_datetime(row.get("Fill Time")),
                "Markets": str(row.get("Markets", "")).strip(),
                "Currency": str(row.get("Currency", "")).strip(),
                "Platform_Fees": self._parse_numeric(row.get("Platform Fees")),
                "Tax": self._parse_numeric(row.get("Consumption Tax")),
                "Settlement_Fees": self._parse_numeric(row.get("Settlement Fees")),
                "Trading_Fees": self._parse_numeric(row.get("Trading Fees")),
                "CAT_Fees": self._parse_numeric(row.get("Consolidated Audit Trail Fees")),
                "Commission": self._parse_numeric(row.get("Commission")),
                "Clearing_Fees": self._parse_numeric(row.get("Clearing Fees")),
                "Platform": source,
                "Validation_Status": "Pending",
                "Validation_Errors": "",
            }
            records.append(record)

        return records

    def _parse_numeric(self, value) -> Optional[float]:
        """Parse numeric value, return None if invalid."""
        if pd.isna(value) or value == "" or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_datetime(self, value) -> Optional[str]:
        """Parse datetime value to ISO format."""
        if pd.isna(value) or value == "" or value is None:
            return None
        try:
            # Try various date formats
            dt = pd.to_datetime(value)
            return dt.isoformat()
        except (ValueError, TypeError):
            return str(value)

    def import_csv(self, file_path: str, dry_run: bool = False, source: str = "moomoo") -> int:
        """Import CSV file into bronze_transactions table."""
        # Read CSV
        df = self.read_csv(file_path)
        
        if len(df) == 0:
            logger.warning("No data found in CSV file")
            return 0

        # Transform to bronze format
        source_file = Path(file_path).name
        records = self.transform_to_bronze(df, source_file, source)
        logger.info(f"Transformed {len(records)} records for bronze layer")

        if dry_run:
            logger.info("DRY RUN - Would insert the following records:")
            for i, record in enumerate(records[:3], 1):
                logger.info(f"  Record {i}: {record['Symbol']} - {record['Side']}")
            if len(records) > 3:
                logger.info(f"  ... and {len(records) - 3} more")
            return len(records)

        # Check if table exists
        if not self.grist_api.table_exists("bronze_transactions"):
            logger.error("❌ Table 'bronze_transactions' not found in Grist document")
            logger.error("")
            logger.error("Run the setup script first to create the tables:")
            logger.error("  uv run python setup_grist_tables.py --env dev")
            logger.error("")
            logger.error("Or check existing tables:")
            logger.error("  uv run python setup_grist_tables.py --env dev --list-tables")
            raise RuntimeError("Required table 'bronze_transactions' does not exist")

        # Insert into Grist
        try:
            result = self.grist_api.add_records("bronze_transactions", records)
            logger.info(f"Successfully inserted {len(records)} records into bronze_transactions")
            return len(records)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.error("❌ Table 'bronze_transactions' not found (404)")
                logger.error("Run: uv run python setup_grist_tables.py --env dev")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import moomoo CSV files into Grist bronze_transactions table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python csv_import_helper.py samples/sample-minimal-test.csv
    uv run python csv_import_helper.py samples/sample-singapore-stocks.csv --dry-run
    uv run python csv_import_helper.py samples/test.csv --env test
    uv run python csv_import_helper.py samples/data.csv --doc-id mydoc --api-key mykey
    uv run python csv_import_helper.py samples/data.csv --source ibkr
        """,
    )
    parser.add_argument("csv_file", help="Path to moomoo CSV export file")
    parser.add_argument(
        "--env",
        choices=["dev", "test", "production"],
        help="Environment to use (overrides ENVIRONMENT variable)",
    )
    parser.add_argument(
        "--doc-id",
        help="Grist document ID (overrides environment config)",
    )
    parser.add_argument(
        "--api-key",
        help="Grist API key (overrides environment config)",
    )
    parser.add_argument(
        "--api-url",
        help="Grist API URL (overrides environment config)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually importing",
    )
    parser.add_argument(
        "--source",
        default="moomoo",
        help="Source platform (default: moomoo)",
    )

    args = parser.parse_args()

    # Get configuration for environment
    config = get_config(args.env)
    
    # Command line args override config
    api_url = args.api_url or f"{config.url}/api"
    api_key = args.api_key or config.api_key
    doc_id = args.doc_id or config.doc_id

    # Validate required arguments
    if not doc_id:
        logger.error(
            "Grist document ID is required. "
            "Set GRIST_DOC_ID / TEST_GRIST_DOC_ID / PROD_GRIST_DOC_ID "
            "or use --doc-id"
        )
        sys.exit(1)

    if not api_key:
        logger.error(
            "Grist API key is required. "
            "Set GRIST_API_KEY / TEST_GRIST_API_KEY / PROD_GRIST_API_KEY "
            "or use --api-key"
        )
        sys.exit(1)

    env_display = args.env or Config.ENVIRONMENT
    logger.info(f"Using environment: {env_display}")
    logger.info(f"Grist URL: {config.url}")

    # Initialize Grist API and importer
    try:
        grist_api = GristAPI(api_url, api_key, doc_id)
        importer = CSVImporter(grist_api)
        
        # Import CSV
        count = importer.import_csv(args.csv_file, dry_run=args.dry_run, source=args.source)
        
        if args.dry_run:
            logger.info(f"Dry run complete. Would import {count} records.")
        else:
            logger.info(f"Import complete. Imported {count} records.")
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
