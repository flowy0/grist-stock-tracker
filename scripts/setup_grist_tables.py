#!/usr/bin/env python3
"""
Grist Table Setup Automation

This script automates the creation of all tables and columns for the Stock Tracker
application using the Grist API. It sets up the medallion architecture:
- Bronze Layer: Raw data tables
- Silver Layer: Cleaned and validated tables
- Gold Layer: Aggregated business metrics

Usage:
    uv run python setup_grist_tables.py --env dev
    uv run python setup_grist_tables.py --env test --dry-run
    uv run python setup_grist_tables.py --doc-id <id> --api-key <key>

Environment Variables:
    ENVIRONMENT: Current environment (dev | test | production)
    GRIST_API_KEY / TEST_GRIST_API_KEY / PROD_GRIST_API_KEY
    GRIST_DOC_ID / TEST_GRIST_DOC_ID / PROD_GRIST_DOC_ID
"""

import argparse
import json
import logging
import sys
import time
from typing import Any, Dict, List, Optional

import requests

from config import Config, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================================
# TABLE SCHEMAS - Medallion Architecture
# ============================================================================

# Bronze Layer - Raw data from CSV imports
BRONZE_TRANSACTIONS_SCHEMA = {
    "id": "bronze_transactions",
    "columns": [
        {"id": "Import_ID", "label": "Import ID", "type": "Text"},
        {"id": "Import_Date", "label": "Import Date", "type": "DateTime"},
        {"id": "Source_File", "label": "Source File", "type": "Text"},
        {"id": "Raw_Data", "label": "Raw Data", "type": "Text"},
        {"id": "Side", "label": "Side", "type": "Text"},
        {"id": "Symbol", "label": "Symbol", "type": "Text"},
        {"id": "Name", "label": "Name", "type": "Text"},
        {"id": "Order_Price", "label": "Order Price", "type": "Numeric"},
        {"id": "Order_Qty", "label": "Order Qty", "type": "Numeric"},
        {"id": "Order_Amount", "label": "Order Amount", "type": "Numeric"},
        {"id": "Status", "label": "Status", "type": "Text"},
        {"id": "Filled_Avg_Price", "label": "Filled Avg Price", "type": "Text"},
        {"id": "Order_Time", "label": "Order Time", "type": "DateTime"},
        {"id": "Order_Type", "label": "Order Type", "type": "Text"},
        {"id": "Time_in_Force", "label": "Time in Force", "type": "Text"},
        {"id": "Fill_Qty", "label": "Fill Qty", "type": "Numeric"},
        {"id": "Fill_Price", "label": "Fill Price", "type": "Numeric"},
        {"id": "Fill_Amount", "label": "Fill Amount", "type": "Numeric"},
        {"id": "Fill_Time", "label": "Fill Time", "type": "DateTime"},
        {"id": "Markets", "label": "Markets", "type": "Text"},
        {"id": "Currency", "label": "Currency", "type": "Text"},
        {"id": "Platform_Fees", "label": "Platform Fees", "type": "Numeric"},
        {"id": "Tax", "label": "Tax", "type": "Numeric"},
        {"id": "Settlement_Fees", "label": "Settlement Fees", "type": "Numeric"},
        {"id": "Trading_Fees", "label": "Trading Fees", "type": "Numeric"},
        {"id": "CAT_Fees", "label": "CAT Fees", "type": "Numeric"},
        {"id": "Commission", "label": "Commission", "type": "Numeric"},
        {"id": "Clearing_Fees", "label": "Clearing Fees", "type": "Numeric"},
        {"id": "Platform", "label": "Platform", "type": "Text"},
        {"id": "Validation_Status", "label": "Validation Status", "type": "Choice", 
         "choices": ["Valid", "Invalid", "Pending"]},
        {"id": "Validation_Errors", "label": "Validation Errors", "type": "Text"},
    ]
}

# Silver Layer - Stock master data
SILVER_STOCKS_SCHEMA = {
    "id": "silver_stocks",
    "columns": [
        {"id": "Symbol", "label": "Symbol", "type": "Text"},
        {"id": "Name", "label": "Name", "type": "Text"},
        {"id": "Market", "label": "Market", "type": "Choice", 
         "choices": ["SG", "US", "HK", "UK"]},
        {"id": "Currency", "label": "Currency", "type": "Choice", 
         "choices": ["SGD", "USD", "HKD", "GBP"]},
        {"id": "Asset_Type", "label": "Asset Type", "type": "Choice", 
         "choices": ["Stock", "ETF", "REIT", "Bond"]},
        {"id": "Current_Price", "label": "Current Price", "type": "Numeric"},
        {"id": "Price_Updated", "label": "Price Updated", "type": "DateTime"},
        {"id": "Price_Source", "label": "Price Source", "type": "Text"},
        {"id": "Is_Active", "label": "Is Active", "type": "Toggle"},
    ]
}

# Silver Layer - Validated transactions
SILVER_TRANSACTIONS_SCHEMA = {
    "id": "silver_transactions",
    "columns": [
        {"id": "Transaction_ID", "label": "Transaction ID", "type": "Text"},
        {"id": "Bronze_Ref", "label": "Bronze Ref", "type": "Text"},  # Reference to bronze
        {"id": "Date", "label": "Date", "type": "DateTime"},
        {"id": "Side", "label": "Side", "type": "Choice", 
         "choices": ["Buy", "Sell", "Dividend"]},
        {"id": "Symbol", "label": "Symbol", "type": "Text"},  # Reference to silver_stocks
        {"id": "Fill_Qty", "label": "Fill Qty", "type": "Numeric"},
        {"id": "Fill_Price", "label": "Fill Price", "type": "Numeric"},
        {"id": "Fill_Amount", "label": "Fill Amount", "type": "Numeric"},
        {"id": "Platform_Fees", "label": "Platform Fees", "type": "Numeric"},
        {"id": "Tax", "label": "Tax", "type": "Numeric"},
        {"id": "Settlement_Fees", "label": "Settlement Fees", "type": "Numeric"},
        {"id": "Trading_Fees", "label": "Trading Fees", "type": "Numeric"},
        {"id": "CAT_Fees", "label": "CAT Fees", "type": "Numeric"},
        {"id": "Commission", "label": "Commission", "type": "Numeric"},
        {"id": "Clearing_Fees", "label": "Clearing Fees", "type": "Numeric"},
        {"id": "Total_Fees", "label": "Total Fees", "type": "Formula", 
         "formula": "sum([$Platform_Fees or 0, $Tax or 0, $Settlement_Fees or 0, $Trading_Fees or 0, $CAT_Fees or 0, $Commission or 0, $Clearing_Fees or 0])"},
        {"id": "Net_Amount", "label": "Net Amount", "type": "Formula", 
         "formula": "$Fill_Amount + $Total_Fees if $Side == \"Buy\" else $Fill_Amount - $Total_Fees"},
        {"id": "Platform", "label": "Platform", "type": "Text"},
        {"id": "Notes", "label": "Notes", "type": "Text"},
    ]
}

# Gold Layer - Position calculations
GOLD_POSITIONS_SCHEMA = {
    "id": "gold_positions",
    "columns": [
        {"id": "Position_ID", "label": "Position ID", "type": "Text"},
        {"id": "Symbol", "label": "Symbol", "type": "Text"},  # Reference to silver_stocks
        {"id": "Total_Shares", "label": "Total Shares", "type": "Formula", 
         "formula": "import itertools\ntxns = silver_transactions.lookupRecords(Symbol=$Symbol)\nreturn sum(t.Fill_Qty if t.Side==\"Buy\" else -t.Fill_Qty for t in txns if t.Side!=\"Dividend\")"},
        {"id": "Total_Invested", "label": "Total Invested", "type": "Formula", 
         "formula": "txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side=\"Buy\")\nreturn sum(t.Net_Amount for t in txns)"},
        {"id": "Avg_Cost_Basis", "label": "Avg Cost Basis", "type": "Formula", 
         "formula": "$Total_Invested / $Total_Shares if $Total_Shares > 0 else 0"},
        {"id": "Current_Market_Value", "label": "Current Market Value", "type": "Formula", 
         "formula": "$Total_Shares * silver_stocks.lookupOne(Symbol=$Symbol).Current_Price if $Total_Shares > 0 else 0"},
        {"id": "Unrealized_P_L", "label": "Unrealized P/L", "type": "Formula", 
         "formula": "$Current_Market_Value - $Total_Invested if $Total_Shares > 0 else 0"},
        {"id": "Realized_P_L", "label": "Realized P/L", "type": "Formula", 
         "formula": "txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side=\"Sell\")\ncost_basis = $Avg_Cost_Basis\nreturn sum(t.Fill_Amount - (t.Fill_Qty * cost_basis) for t in txns)"},
        {"id": "Return_Pct", "label": "Return %", "type": "Formula", 
         "formula": "($Unrealized_P_L + $Realized_P_L) / $Total_Invested * 100 if $Total_Invested > 0 else 0"},
        {"id": "Days_Held", "label": "Days Held", "type": "Formula", 
         "formula": "import datetime\ntxns = silver_transactions.lookupRecords(Symbol=$Symbol, Side=\"Buy\")\nif len(txns) > 0:\n    first_date = min(t.Date for t in txns if t.Date)\n    return (datetime.datetime.now() - first_date).days\nreturn 0"},
    ]
}

# Gold Layer - Portfolio master view
GOLD_STOCKS_SCHEMA = {
    "id": "gold_stocks",
    "columns": [
        {"id": "Symbol", "label": "Symbol", "type": "Text"},  # Reference to silver_stocks
        {"id": "Name", "label": "Name", "type": "Formula", 
         "formula": "silver_stocks.lookupOne(Symbol=$Symbol).Name"},
        {"id": "Market", "label": "Market", "type": "Formula", 
         "formula": "silver_stocks.lookupOne(Symbol=$Symbol).Market"},
        {"id": "Currency", "label": "Currency", "type": "Formula", 
         "formula": "silver_stocks.lookupOne(Symbol=$Symbol).Currency"},
        {"id": "Asset_Type", "label": "Asset Type", "type": "Formula", 
         "formula": "silver_stocks.lookupOne(Symbol=$Symbol).Asset_Type"},
        {"id": "Current_Price", "label": "Current Price", "type": "Formula", 
         "formula": "silver_stocks.lookupOne(Symbol=$Symbol).Current_Price"},
        {"id": "Total_Shares", "label": "Total Shares", "type": "Formula", 
         "formula": "gold_positions.lookupOne(Symbol=$Symbol).Total_Shares"},
        {"id": "Total_Invested", "label": "Total Invested", "type": "Formula", 
         "formula": "gold_positions.lookupOne(Symbol=$Symbol).Total_Invested"},
        {"id": "Avg_Cost_Basis", "label": "Avg Cost Basis", "type": "Formula", 
         "formula": "gold_positions.lookupOne(Symbol=$Symbol).Avg_Cost_Basis"},
        {"id": "Current_Market_Value", "label": "Current Market Value", "type": "Formula", 
         "formula": "gold_positions.lookupOne(Symbol=$Symbol).Current_Market_Value"},
        {"id": "Unrealized_P_L", "label": "Unrealized P/L", "type": "Formula", 
         "formula": "gold_positions.lookupOne(Symbol=$Symbol).Unrealized_P_L"},
        {"id": "Realized_P_L", "label": "Realized P/L", "type": "Formula", 
         "formula": "gold_positions.lookupOne(Symbol=$Symbol).Realized_P_L"},
        {"id": "Total_Return_Pct", "label": "Total Return %", "type": "Formula", 
         "formula": "($Unrealized_P_L + $Realized_P_L) / $Total_Invested * 100 if $Total_Invested > 0 else 0"},
        {"id": "Last_Transaction_Date", "label": "Last Transaction Date", "type": "Formula", 
         "formula": "txns = silver_transactions.lookupRecords(Symbol=$Symbol)\nif len(txns) > 0:\n    return max(t.Date for t in txns if t.Date)\nreturn None"},
    ]
}

# Gold Layer - Monthly archive
GOLD_MONTHLY_ARCHIVE_SCHEMA = {
    "id": "gold_monthly_archive",
    "columns": [
        {"id": "Archive_ID", "label": "Archive ID", "type": "Text"},
        {"id": "Month", "label": "Month", "type": "Date"},
        {"id": "Symbol", "label": "Symbol", "type": "Text"},  # Reference to silver_stocks
        {"id": "Shares_Held", "label": "Shares Held", "type": "Numeric"},
        {"id": "Avg_Cost", "label": "Avg Cost", "type": "Numeric"},
        {"id": "Month_End_Price", "label": "Month End Price", "type": "Numeric"},
        {"id": "Market_Value", "label": "Market Value", "type": "Numeric"},
        {"id": "Unrealized_PL", "label": "Unrealized P/L", "type": "Numeric"},
        {"id": "Realized_PL_Month", "label": "Realized P/L (Month)", "type": "Numeric"},
        {"id": "Total_Return_Pct", "label": "Total Return %", "type": "Numeric"},
        {"id": "Snapshot_Taken", "label": "Snapshot Taken", "type": "DateTime"},
    ]
}

# All schemas in creation order
ALL_SCHEMAS = [
    BRONZE_TRANSACTIONS_SCHEMA,
    SILVER_STOCKS_SCHEMA,
    SILVER_TRANSACTIONS_SCHEMA,
    GOLD_POSITIONS_SCHEMA,
    GOLD_STOCKS_SCHEMA,
    GOLD_MONTHLY_ARCHIVE_SCHEMA,
]


# ============================================================================
# GRIST API CLIENT
# ============================================================================

class GristSetupClient:
    """Client for setting up Grist tables via API."""

    def __init__(self, api_url: str, api_key: str, doc_id: str):
        self.api_url = api_url.rstrip("/")
        self.doc_id = doc_id
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self._existing_tables: Optional[List[str]] = None

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Make a request to the Grist API."""
        url = f"{self.api_url}/{endpoint}"
        try:
            response = requests.request(
                method, url, headers=self.headers, json=data, timeout=30
            )
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise

    def list_tables(self) -> List[Dict]:
        """List all tables in the document."""
        try:
            result = self._request("GET", f"docs/{self.doc_id}/tables")
            return result.get("tables", []) if result else []
        except Exception as e:
            logger.warning(f"Could not list tables: {e}")
            return []

    def table_exists(self, table_id: str) -> bool:
        """Check if a table already exists."""
        if self._existing_tables is None:
            tables = self.list_tables()
            self._existing_tables = [t.get("id") for t in tables]
        return table_id in self._existing_tables

    def create_table(self, table_id: str, columns: List[Dict], dry_run: bool = False) -> bool:
        """Create a table with the given columns."""
        if self.table_exists(table_id):
            logger.info(f"Table '{table_id}' already exists, skipping")
            return False

        if dry_run:
            logger.info(f"[DRY RUN] Would create table '{table_id}' with {len(columns)} columns")
            return True

        # Prepare columns for API
        api_columns = []
        for col in columns:
            col_def = {
                "id": col["id"],
                "fields": {
                    "label": col["label"],
                    "type": col["type"],
                }
            }
            # Add choices for Choice type
            if col["type"] == "Choice" and "choices" in col:
                col_def["fields"]["widgetOptions"] = json.dumps({
                    "choices": col["choices"],
                    "choiceOptions": {c: {"backColor": "#FFFFFF", "textColor": "#000000"} 
                                      for c in col["choices"]}
                })
            # Add formula for Formula type
            if col["type"] == "Formula" and "formula" in col:
                col_def["fields"]["isFormula"] = True
                col_def["fields"]["formula"] = col["formula"]
            api_columns.append(col_def)

        payload = {
            "tables": [{
                "id": table_id,
                "columns": api_columns
            }]
        }

        try:
            result = self._request("POST", f"docs/{self.doc_id}/tables", payload)
            logger.info(f"✅ Created table '{table_id}' with {len(columns)} columns")
            # Refresh existing tables cache
            self._existing_tables = None
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create table '{table_id}': {e}")
            return False

    def setup_all_tables(self, dry_run: bool = False) -> Dict[str, bool]:
        """Set up all tables defined in schemas."""
        results = {}
        
        logger.info("=" * 60)
        logger.info("Setting up Grist Tables - Medallion Architecture")
        logger.info("=" * 60)
        
        # First, refresh tables cache
        self.list_tables()
        
        for schema in ALL_SCHEMAS:
            table_id = schema["id"]
            columns = schema["columns"]
            
            logger.info(f"\n📋 Processing table: {table_id}")
            success = self.create_table(table_id, columns, dry_run)
            results[table_id] = success
            
            # Small delay to avoid rate limiting
            if not dry_run:
                time.sleep(0.5)

        return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Automate Grist table setup for Stock Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python setup_grist_tables.py --env dev
    uv run python setup_grist_tables.py --env test --dry-run
    uv run python setup_grist_tables.py --doc-id abc123 --api-key xyz789
        """,
    )
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
        help="Show what would be created without making changes",
    )
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List existing tables in the document",
    )

    args = parser.parse_args()

    # Get configuration
    config = get_config(args.env)
    api_url = args.api_url or f"{config.url}/api"
    api_key = args.api_key or config.api_key
    doc_id = args.doc_id or config.doc_id

    # Validate
    if not doc_id:
        logger.error(
            "Document ID required. Set GRIST_DOC_ID / TEST_GRIST_DOC_ID / PROD_GRIST_DOC_ID "
            "or use --doc-id"
        )
        sys.exit(1)

    if not api_key:
        logger.error(
            "API key required. Set GRIST_API_KEY / TEST_GRIST_API_KEY / PROD_GRIST_API_KEY "
            "or use --api-key"
        )
        sys.exit(1)

    env_display = args.env or Config.ENVIRONMENT
    logger.info(f"Environment: {env_display}")
    logger.info(f"API URL: {api_url}")
    logger.info(f"Document ID: {doc_id}")

    # Initialize client
    client = GristSetupClient(api_url, api_key, doc_id)

    # List tables if requested
    if args.list_tables:
        logger.info("\nExisting tables:")
        tables = client.list_tables()
        if tables:
            for table in tables:
                logger.info(f"  - {table.get('id')}")
        else:
            logger.info("  (none found)")
        return

    # Setup tables
    try:
        results = client.setup_all_tables(dry_run=args.dry_run)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("Setup Summary")
        logger.info("=" * 60)
        
        created = sum(1 for v in results.values() if v)
        skipped = sum(1 for v in results.values() if not v)
        
        for table_id, success in results.items():
            status = "✅ Created" if success else "⏭️  Skipped/Exists"
            logger.info(f"  {status}: {table_id}")
        
        logger.info(f"\nTotal: {created} created, {skipped} skipped")
        
        if args.dry_run:
            logger.info("\n[DRY RUN] No changes were made")
        else:
            logger.info("\n✨ Setup complete!")
            logger.info("\nNext steps:")
            logger.info("  1. Log into Grist and verify the tables")
            logger.info("  2. Add formulas to formula columns (see docs/03-grist-table-setup.md)")
            logger.info("  3. Configure column formatting as needed")
            
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
