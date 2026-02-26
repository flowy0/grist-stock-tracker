#!/usr/bin/env python3
"""
Monthly Archiver for Grist Stock Tracker

Creates month-end snapshots of portfolio positions for historical tracking.
Archives data to gold_monthly_archive table.

Usage:
    uv run python monthly_archiver.py [--env <env>]
    uv run python monthly_archiver.py --month 2026-01 --env dev
    uv run python monthly_archiver.py --latest --env test

Environment Variables:
    ENVIRONMENT: Current environment (dev | test | production)
    GRIST_API_KEY / TEST_GRIST_API_KEY / PROD_GRIST_API_KEY
    GRIST_DOC_ID / TEST_GRIST_DOC_ID / PROD_GRIST_DOC_ID
"""

import argparse
import calendar
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta
from typing import Optional

from csv_import_helper import GristAPI
from config import Config, get_config

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MonthlyArchiver:
    """Create month-end snapshots of portfolio positions."""

    def __init__(self, grist_api: GristAPI):
        self.grist_api = grist_api
        self.stats = {
            "positions_processed": 0,
            "archived": 0,
            "skipped": 0,
            "errors": 0,
        }

    def get_month_end_date(self, year: int, month: int) -> datetime:
        """Get the last day of the month."""
        last_day = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_day, 23, 59, 59)

    def get_positions(self, as_of_date: datetime) -> list:
        """
        Get all active positions from gold_positions as of a specific date.
        
        Note: This gets current positions. For true historical tracking,
        you'd need to filter silver_transactions by date.
        """
        logger.info(f"Fetching positions as of {as_of_date.date()}")
        records = self.grist_api.get_records(self.grist_api.get_actual_table_id("gold_positions"))
        
        positions = []
        for record in records:
            fields = record.get("fields", {})
            
            # Only archive positions with shares
            total_shares = fields.get("Total_Shares", 0)
            if not total_shares or total_shares <= 0:
                continue

            positions.append({
                "id": record.get("id"),
                "symbol": fields.get("Symbol"),  # Reference to silver_stocks
                "shares": total_shares,
                "avg_cost": fields.get("Avg_Cost_Basis", 0),
                "market_value": fields.get("Current_Market_Value", 0),
                "unrealized_pl": fields.get("Unrealized_P_L", 0),
                "realized_pl": fields.get("Realized_P_L", 0),
                "current_price": fields.get("Symbol", {}).get("Current_Price") if isinstance(fields.get("Symbol"), dict) else None,
            })

        logger.info(f"Found {len(positions)} positions to archive")
        return positions

    def get_transactions_for_month(self, year: int, month: int) -> list:
        """Get all transactions for a specific month to calculate realized P/L."""
        logger.info(f"Fetching transactions for {year}-{month:02d}")
        records = self.grist_api.get_records(self.grist_api.get_actual_table_id("silver_transactions"))
        
        # Filter by month
        month_start = datetime(year, month, 1)
        month_end = self.get_month_end_date(year, month)
        
        transactions = []
        for record in records:
            fields = record.get("fields", {})
            date_str = fields.get("Date", "")
            
            if not date_str:
                continue
            
            try:
                # Parse ISO format datetime
                tx_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if month_start <= tx_date <= month_end:
                    transactions.append({
                        "symbol": fields.get("Symbol"),
                        "side": fields.get("Side"),
                        "net_amount": fields.get("Net_Amount", 0),
                        "fill_amount": fields.get("Fill_Amount", 0),
                    })
            except ValueError:
                continue

        logger.info(f"Found {len(transactions)} transactions for the month")
        return transactions

    def calculate_realized_pl_for_month(self, symbol: str, transactions: list) -> float:
        """Calculate realized P/L for a specific symbol in the given transactions."""
        realized = 0.0
        
        for tx in transactions:
            if tx.get("symbol") != symbol:
                continue
            
            if tx.get("side") == "Sell":
                # For sells, the Fill_Amount is the proceeds
                # Realized P/L would be calculated against cost basis
                # For simplicity, we use the net amount
                realized += tx.get("net_amount", 0) or 0

        return realized

    def check_existing_archive(self, year: int, month: int) -> bool:
        """Check if archive already exists for the month."""
        records = self.grist_api.get_records(self.grist_api.get_actual_table_id("gold_monthly_archive"))
        
        for record in records:
            fields = record.get("fields", {})
            month_field = fields.get("Month", "")
            
            if not month_field:
                continue
            
            try:
                # Parse date field
                archive_date = datetime.fromisoformat(month_field.replace("Z", "+00:00"))
                if archive_date.year == year and archive_date.month == month:
                    logger.warning(f"Archive already exists for {year}-{month:02d}")
                    return True
            except ValueError:
                continue

        return False

    def create_archive_records(
        self, 
        positions: list, 
        year: int, 
        month: int,
        transactions: list
    ) -> list:
        """Create archive records for all positions."""
        month_end = self.get_month_end_date(year, month)
        records = []

        for position in positions:
            self.stats["positions_processed"] += 1
            
            # Calculate realized P/L for this symbol in this month
            realized_pl_month = self.calculate_realized_pl_for_month(
                position["symbol"], transactions
            )

            # Calculate total return percentage
            total_invested = position["shares"] * position["avg_cost"] if position["avg_cost"] else 0
            total_return_pct = 0
            if total_invested > 0:
                total_return = (position["unrealized_pl"] or 0) + (position["realized_pl"] or 0)
                total_return_pct = (total_return / total_invested) * 100

            record = {
                "Archive_ID": str(uuid.uuid4()),
                "Month": month_end.isoformat(),
                "Symbol": position["symbol"],
                "Shares_Held": position["shares"],
                "Avg_Cost": position["avg_cost"],
                "Month_End_Price": position["current_price"],
                "Market_Value": position["market_value"],
                "Unrealized_PL": position["unrealized_pl"],
                "Realized_PL_Month": realized_pl_month if realized_pl_month else 0,
                "Total_Return_Pct": round(total_return_pct, 2),
                "Snapshot_Taken": datetime.now().isoformat(),
            }
            records.append(record)

        return records

    def run_archival(self, year: Optional[int] = None, month: Optional[int] = None, dry_run: bool = False):
        """Run the monthly archival process."""
        
        # Default to previous month if not specified
        if year is None or month is None:
            today = datetime.now()
            # Get last day of previous month
            first_day = today.replace(day=1)
            last_month = first_day - timedelta(days=1)
            year = last_month.year
            month = last_month.month

        logger.info(f"Starting archival for {year}-{month:02d}")

        # Check if archive already exists
        if not dry_run and self.check_existing_archive(year, month):
            logger.info("Archival skipped - already exists")
            self.stats["skipped"] = 1
            return

        # Get positions
        as_of_date = self.get_month_end_date(year, month)
        positions = self.get_positions(as_of_date)

        if not positions:
            logger.warning("No positions found to archive")
            return

        # Get transactions for realized P/L calculation
        transactions = self.get_transactions_for_month(year, month)

        # Create archive records
        archive_records = self.create_archive_records(positions, year, month, transactions)

        if dry_run:
            logger.info(f"DRY RUN: Would archive {len(archive_records)} positions")
            for record in archive_records[:3]:
                logger.info(f"  - {record['Symbol']}: {record['Shares_Held']} shares, "
                          f"${record['Market_Value']:.2f}")
            if len(archive_records) > 3:
                logger.info(f"  ... and {len(archive_records) - 3} more")
        else:
            try:
                self.grist_api.add_records(self.grist_api.get_actual_table_id("gold_monthly_archive"), archive_records)
                self.stats["archived"] = len(archive_records)
                logger.info(f"Successfully archived {len(archive_records)} positions")
            except Exception as e:
                logger.error(f"Failed to archive positions: {e}")
                self.stats["errors"] += 1
                raise

        self.print_summary()

    def print_summary(self):
        """Print archival summary."""
        logger.info("=" * 50)
        logger.info("Monthly Archive Summary")
        logger.info("=" * 50)
        logger.info(f"Positions processed: {self.stats['positions_processed']}")
        logger.info(f"Positions archived: {self.stats['archived']}")
        logger.info(f"Skipped (existing): {self.stats['skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 50)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create monthly portfolio snapshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python monthly_archiver.py
    uv run python monthly_archiver.py --month 2026-01
    uv run python monthly_archiver.py --latest
    uv run python monthly_archiver.py --dry-run
        """,
    )
    parser.add_argument(
        "--month",
        help="Month to archive (YYYY-MM format, default: previous month)",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Archive latest month (same as default)",
    )
    parser.add_argument(
        "--doc-id",
        default=os.getenv("GRIST_DOC_ID"),
        help="Grist document ID (or set GRIST_DOC_ID env var)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("GRIST_API_KEY"),
        help="Grist API key (or set GRIST_API_KEY or use --api-key)",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("GRIST_API_URL", "http://localhost:8484/api"),
        help="Grist API URL (default: http://localhost:8484/api)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be archived without actually archiving",
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.doc_id:
        logger.error("Grist document ID is required. Set GRIST_DOC_ID or use --doc-id")
        sys.exit(1)

    if not args.api_key:
        logger.error("Grist API key is required. Set GRIST_API_KEY or use --api-key")
        sys.exit(1)

    # Parse month
    year = None
    month = None
    if args.month:
        try:
            year, month = map(int, args.month.split("-"))
        except ValueError:
            logger.error("Invalid month format. Use YYYY-MM")
            sys.exit(1)

    # Initialize and run archiver
    try:
        grist_api = GristAPI(api_url, api_key, doc_id)
        archiver = MonthlyArchiver(grist_api)
        archiver.run_archival(year=year, month=month, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Archival failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
