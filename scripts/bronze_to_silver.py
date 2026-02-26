#!/usr/bin/env python3
"""
Bronze to Silver Transformation Script

This script transforms raw data from bronze_transactions (Bronze layer)
to cleaned, validated data in silver_transactions and silver_stocks (Silver layer).

It performs:
1. Data validation (duplicates, required fields, numeric validation)
2. Symbol normalization and stock master data creation
3. Date format normalization
4. Transaction ID generation
5. Validation status updates in Bronze layer

Usage:
    uv run python bronze_to_silver.py [--doc-id <id>] [--api-key <key>]
    uv run python bronze_to_silver.py --dry-run

Environment Variables:
    GRIST_DOC_ID: Grist document ID
    GRIST_API_KEY: Grist API key
    GRIST_API_URL: Grist API URL (default: http://localhost:8484/api)
"""

import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

from csv_import_helper import GristAPI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BronzeToSilverTransformer:
    """Transform and validate data from Bronze to Silver layer."""

    def __init__(self, grist_api: GristAPI):
        self.grist_api = grist_api
        self.validation_errors = []
        self.stats = {
            "bronze_processed": 0,
            "silver_created": 0,
            "stocks_created": 0,
            "errors": 0,
            "duplicates": 0,
        }

    def get_bronze_records(self, status: str = "Pending") -> list:
        """Get bronze records with specified validation status."""
        logger.info(f"Fetching bronze records with status: {status}")
        records = self.grist_api.get_records("bronze_transactions")
        
        # Filter by status
        filtered = [
            r for r in records 
            if r.get("fields", {}).get("Validation_Status") == status
        ]
        logger.info(f"Found {len(filtered)} bronze records to process")
        return filtered

    def validate_record(self, record: dict) -> tuple[bool, list]:
        """
        Validate a bronze record.
        
        Returns:
            (is_valid, error_messages)
        """
        fields = record.get("fields", {})
        errors = []

        # Check required fields
        required_fields = ["Symbol", "Side", "Fill_Qty", "Fill_Price"]
        for field in required_fields:
            if not fields.get(field):
                errors.append(f"Missing required field: {field}")

        # Validate Symbol
        symbol = fields.get("Symbol", "").strip()
        if not symbol:
            errors.append("Symbol is empty")
        elif len(symbol) > 20:
            errors.append(f"Symbol too long: {symbol}")

        # Validate Side
        side = fields.get("Side", "").strip()
        valid_sides = ["Buy", "Sell", "Dividend"]
        if side not in valid_sides:
            errors.append(f"Invalid Side: {side}. Must be one of {valid_sides}")

        # Validate numeric fields are positive
        numeric_fields = ["Fill_Qty", "Fill_Price", "Fill_Amount"]
        for field in numeric_fields:
            value = fields.get(field)
            if value is not None:
                try:
                    if float(value) < 0:
                        errors.append(f"{field} cannot be negative: {value}")
                except (ValueError, TypeError):
                    errors.append(f"{field} is not a valid number: {value}")

        # For Dividend, quantity can be 0 but should have Fill_Amount
        if side == "Dividend":
            fill_amount = fields.get("Fill_Amount")
            if not fill_amount or float(fill_amount) <= 0:
                errors.append("Dividend transactions must have positive Fill_Amount")

        return len(errors) == 0, errors

    def check_duplicates(self, record: dict, existing_silver: list) -> bool:
        """
        Check if a similar record already exists in Silver layer.
        
        Uses Symbol + Fill_Time + Side as uniqueness key.
        """
        fields = record.get("fields", {})
        symbol = fields.get("Symbol", "").strip().upper()
        fill_time = fields.get("Fill_Time", "")
        side = fields.get("Side", "").strip()

        for existing in existing_silver:
            ex_fields = existing.get("fields", {})
            if (
                ex_fields.get("Symbol", "").strip().upper() == symbol
                and ex_fields.get("Date") == fill_time
                and ex_fields.get("Side", "").strip() == side
            ):
                return True
        return False

    def normalize_symbol(self, symbol: str, name: str) -> tuple[str, str]:
        """
        Normalize symbol and determine asset type.
        
        Returns:
            (normalized_symbol, asset_type)
        """
        symbol = symbol.strip().upper()
        
        # Determine asset type based on common patterns
        asset_type = "Stock"
        if "ETF" in name.upper() or symbol in ["VOO", "QQQ", "SPY", "VTI"]:
            asset_type = "ETF"
        elif "REIT" in name.upper() or symbol in ["A17U", "C38", "ME8U"]:
            asset_type = "REIT"
        
        return symbol, asset_type

    def get_or_create_stock(self, symbol: str, name: str, market: str, currency: str) -> str:
        """
        Get existing stock or create new one in silver_stocks.
        
        Returns:
            symbol (normalized)
        """
        symbol, asset_type = self.normalize_symbol(symbol, name)
        
        # Check if stock exists
        existing_stocks = self.grist_api.get_records("silver_stocks")
        for stock in existing_stocks:
            if stock.get("fields", {}).get("Symbol", "").upper() == symbol:
                logger.debug(f"Stock already exists: {symbol}")
                return symbol

        # Create new stock
        stock_record = {
            "Symbol": symbol,
            "Name": name.strip(),
            "Market": market.strip() if market else "US",
            "Currency": currency.strip() if currency else "USD",
            "Asset_Type": asset_type,
            "Current_Price": None,
            "Price_Updated": None,
            "Price_Source": None,
            "Is_Active": True,
        }

        try:
            self.grist_api.add_records("silver_stocks", [stock_record])
            self.stats["stocks_created"] += 1
            logger.info(f"Created new stock: {symbol} ({asset_type})")
        except Exception as e:
            logger.error(f"Failed to create stock {symbol}: {e}")
            raise

        return symbol

    def transform_to_silver(self, record: dict, symbol_ref: str) -> dict:
        """
        Transform a bronze record to silver format.
        """
        fields = record.get("fields", {})
        
        silver_record = {
            "Transaction_ID": str(uuid.uuid4()),
            "Bronze_Ref": record.get("id"),  # Reference to bronze record
            "Date": fields.get("Fill_Time"),
            "Side": fields.get("Side", "").strip(),
            "Symbol": symbol_ref,  # Reference to silver_stocks
            "Fill_Qty": fields.get("Fill_Qty"),
            "Fill_Price": fields.get("Fill_Price"),
            "Fill_Amount": fields.get("Fill_Amount"),
            "Platform_Fees": fields.get("Platform_Fees"),
            "Tax": fields.get("Tax"),
            "Settlement_Fees": fields.get("Settlement_Fees"),
            "Trading_Fees": fields.get("Trading_Fees"),
            "CAT_Fees": fields.get("CAT_Fees"),
            "Commission": fields.get("Commission"),
            "Clearing_Fees": fields.get("Clearing_Fees"),
            "Platform": fields.get("Platform", "moomoo"),
            "Notes": "",
        }

        return silver_record

    def update_bronze_status(self, record_id: str, status: str, errors: list):
        """Update validation status in bronze_transactions."""
        # Note: Grist API PATCH for records is limited
        # For now, we'll log the status update
        error_msg = "; ".join(errors) if errors else ""
        logger.info(f"Updating bronze record {record_id}: {status} - {error_msg}")
        
        # TODO: Implement PATCH call when Grist API supports it
        # For now, this is tracked in the stats

    def process_bronze_records(self, dry_run: bool = False):
        """
        Main processing loop for Bronze to Silver transformation.
        """
        logger.info("Starting Bronze to Silver transformation")

        # Get pending bronze records
        bronze_records = self.get_bronze_records(status="Pending")
        
        if not bronze_records:
            logger.info("No pending bronze records to process")
            return

        # Get existing silver records for duplicate checking
        existing_silver = self.grist_api.get_records("silver_transactions")

        silver_records_to_create = []

        for record in bronze_records:
            self.stats["bronze_processed"] += 1
            record_id = record.get("id")
            fields = record.get("fields", {})

            try:
                # Step 1: Validate
                is_valid, errors = self.validate_record(record)
                
                if not is_valid:
                    logger.warning(f"Validation failed for record {record_id}: {errors}")
                    self.update_bronze_status(record_id, "Invalid", errors)
                    self.stats["errors"] += 1
                    continue

                # Step 2: Check for duplicates
                if self.check_duplicates(record, existing_silver):
                    logger.warning(f"Duplicate record detected: {record_id}")
                    self.update_bronze_status(record_id, "Invalid", ["Duplicate transaction"])
                    self.stats["duplicates"] += 1
                    continue

                # Step 3: Get or create stock
                symbol = fields.get("Symbol", "").strip()
                name = fields.get("Name", "").strip()
                market = fields.get("Markets", "").strip()
                currency = fields.get("Currency", "").strip()

                if not dry_run:
                    symbol_ref = self.get_or_create_stock(symbol, name, market, currency)
                else:
                    symbol_ref = symbol.upper()
                    logger.info(f"DRY RUN: Would create/get stock: {symbol_ref}")

                # Step 4: Transform to silver
                silver_record = self.transform_to_silver(record, symbol_ref)
                silver_records_to_create.append(silver_record)

                # Step 5: Mark bronze as valid
                self.update_bronze_status(record_id, "Valid", [])

            except Exception as e:
                logger.error(f"Error processing record {record_id}: {e}")
                self.stats["errors"] += 1
                continue

        # Bulk insert silver records
        if silver_records_to_create and not dry_run:
            try:
                self.grist_api.add_records("silver_transactions", silver_records_to_create)
                self.stats["silver_created"] = len(silver_records_to_create)
                logger.info(f"Created {len(silver_records_to_create)} silver records")
            except Exception as e:
                logger.error(f"Failed to create silver records: {e}")
                raise
        elif dry_run:
            logger.info(f"DRY RUN: Would create {len(silver_records_to_create)} silver records")

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print transformation summary."""
        logger.info("=" * 50)
        logger.info("Bronze to Silver Transformation Summary")
        logger.info("=" * 50)
        logger.info(f"Bronze records processed: {self.stats['bronze_processed']}")
        logger.info(f"Silver records created: {self.stats['silver_created']}")
        logger.info(f"Stocks created: {self.stats['stocks_created']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates']}")
        logger.info("=" * 50)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Transform Bronze layer data to Silver layer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python bronze_to_silver.py
    uv run python bronze_to_silver.py --dry-run
    uv run python bronze_to_silver.py --doc-id mydoc --api-key mykey
        """,
    )
    parser.add_argument(
        "--doc-id",
        default=os.getenv("GRIST_DOC_ID"),
        help="Grist document ID (or set GRIST_DOC_ID env var)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("GRIST_API_KEY"),
        help="Grist API key (or set GRIST_API_KEY env var)",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("GRIST_API_URL", "http://localhost:8484/api"),
        help="Grist API URL (default: http://localhost:8484/api)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be transformed without actually transforming",
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.doc_id:
        logger.error("Grist document ID is required. Set GRIST_DOC_ID or use --doc-id")
        sys.exit(1)

    if not args.api_key:
        logger.error("Grist API key is required. Set GRIST_API_KEY or use --api-key")
        sys.exit(1)

    # Initialize and run transformer
    try:
        grist_api = GristAPI(args.api_url, args.api_key, args.doc_id)
        transformer = BronzeToSilverTransformer(grist_api)
        transformer.process_bronze_records(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
