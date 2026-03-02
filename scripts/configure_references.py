#!/usr/bin/env python3
"""
Configure Table References in Grist

Automatically sets up reference columns for the Stock Tracker tables.

Usage:
    uv run python configure_references.py --env test
    uv run python configure_references.py --env test --dry-run
"""

import argparse
import json
import logging
import sys
from typing import Optional

import requests

from config import Config, get_config
from csv_import_helper import GristAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ReferenceConfigurator:
    """Configure table references via Grist API."""

    def __init__(self, grist_api: GristAPI):
        self.grist_api = grist_api
        self.stats = {"configured": 0, "skipped": 0, "errors": 0}

    def get_column_info(self, table_id: str, column_id: str) -> Optional[dict]:
        """Get column information from Grist."""
        try:
            # Get all columns for the table
            actual_table_id = self.grist_api.get_actual_table_id(table_id)
            result = self.grist_api._make_request(
                "GET", f"docs/{self.grist_api.doc_id}/tables/{actual_table_id}/columns"
            )
            columns = result.get("columns", [])
            for col in columns:
                if col.get("id") == column_id:
                    return col
            return None
        except Exception as e:
            logger.error(f"Failed to get column info: {e}")
            return None

    def set_reference(
        self,
        table_id: str,
        column_id: str,
        ref_table_id: str,
        ref_column_id: str,
        dry_run: bool = False,
    ) -> bool:
        """Configure a column as a reference to another table."""
        actual_table_id = self.grist_api.get_actual_table_id(table_id)
        actual_ref_table_id = self.grist_api.get_actual_table_id(ref_table_id)

        # Get current column info
        col_info = self.get_column_info(table_id, column_id)
        if not col_info:
            logger.error(f"Column '{column_id}' not found in table '{table_id}'")
            self.stats["errors"] += 1
            return False

        current_type = col_info.get("fields", {}).get("type")

        # Check if already configured as reference
        if current_type == "Ref":
            widget_opts = json.loads(col_info.get("fields", {}).get("widgetOptions", "{}"))
            if widget_opts.get("destinationTable") == actual_ref_table_id:
                logger.info(f"✅ {table_id}.{column_id} already configured as reference")
                self.stats["skipped"] += 1
                return True

        if dry_run:
            logger.info(
                f"[DRY RUN] Would configure {table_id}.{column_id} → {ref_table_id}.{ref_column_id}"
            )
            return True

        # Configure as reference
        try:
            # First update the column type
            endpoint = f"docs/{self.grist_api.doc_id}/tables/{actual_table_id}/columns/{column_id}"
            
            # Set type to Ref and configure widget options
            data = {
                "fields": {
                    "type": "Ref",
                    "widgetOptions": json.dumps({
                        "destinationTable": actual_ref_table_id,
                        "visibleCol": ref_column_id,
                    }),
                }
            }

            # Note: Grist API doesn't support PATCH for columns in the same way
            # This may need to be done via the UI or a different API endpoint
            logger.warning(
                f"⚠️  Cannot configure {table_id}.{column_id} via API - "
                "References must be configured via Grist UI"
            )
            logger.info(f"   Steps: Open table → Click '{column_id}' column → Column Options → Type: Reference")
            logger.info(f"   Set: Table={ref_table_id}, Column={ref_column_id}")
            self.stats["errors"] += 1
            return False

        except Exception as e:
            logger.error(f"Failed to configure reference: {e}")
            self.stats["errors"] += 1
            return False

    def configure_all_references(self, dry_run: bool = False):
        """Configure all required references."""
        logger.info("=" * 60)
        logger.info("Configuring Table References")
        logger.info("=" * 60)

        # Define references to configure
        references = [
            {
                "table": "silver_transactions",
                "column": "Symbol",
                "ref_table": "silver_stocks",
                "ref_column": "Symbol",
            },
            {
                "table": "gold_positions",
                "column": "Symbol",
                "ref_table": "silver_stocks",
                "ref_column": "Symbol",
            },
            {
                "table": "gold_stocks",
                "column": "Symbol",
                "ref_table": "silver_stocks",
                "ref_column": "Symbol",
            },
        ]

        for ref in references:
            logger.info(f"\n📋 Configuring: {ref['table']}.{ref['column']}")
            self.set_reference(
                ref["table"],
                ref["column"],
                ref["ref_table"],
                ref["ref_column"],
                dry_run,
            )

        self.print_summary()

    def print_summary(self):
        """Print configuration summary."""
        logger.info("\n" + "=" * 60)
        logger.info("Reference Configuration Summary")
        logger.info("=" * 60)
        logger.info(f"Configured: {self.stats['configured']}")
        logger.info(f"Already set (skipped): {self.stats['skipped']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)

        if self.stats["errors"] > 0:
            logger.info("\n⚠️  Some references could not be configured via API.")
            logger.info("Please configure manually in Grist UI:")
            logger.info("1. Open the table")
            logger.info("2. Click the column header")
            logger.info("3. Select 'Column Options'")
            logger.info("4. Change Type to 'Reference'")
            logger.info("5. Select the reference table and column")


def main():
    parser = argparse.ArgumentParser(
        description="Configure table references in Grist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python configure_references.py --env test
    uv run python configure_references.py --env test --dry-run
        """,
    )
    parser.add_argument(
        "--env",
        choices=["dev", "test", "production"],
        help="Environment to use (overrides ENVIRONMENT variable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be configured without making changes",
    )

    args = parser.parse_args()

    # Get configuration
    config = get_config(args.env)
    api_url = f"{config.url}/api"
    api_key = config.api_key
    doc_id = config.doc_id

    if not doc_id or not api_key:
        logger.error("GRIST_DOC_ID and GRIST_API_KEY required")
        sys.exit(1)

    env_display = args.env or Config.ENVIRONMENT
    logger.info(f"Environment: {env_display}")
    logger.info(f"URL: {config.url}")

    try:
        grist_api = GristAPI(api_url, api_key, doc_id)
        configurator = ReferenceConfigurator(grist_api)
        configurator.configure_all_references(dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
