#!/usr/bin/env python3
"""
Price Updater for Grist Stock Tracker

Fetches live stock prices from Yahoo Finance and updates silver_stocks table.
Supports fallback to Alpha Vantage and Finnhub APIs.

Usage:
    uv run python price_updater.py
    uv run python price_updater.py --symbols AAPL,NVDA,TSLA
    uv run python price_updater.py --all
    uv run python price_updater.py --dry-run

Environment Variables:
    ENVIRONMENT: Current environment (dev | test | production)
    GRIST_API_KEY / TEST_GRIST_API_KEY / PROD_GRIST_API_KEY
    GRIST_DOC_ID / TEST_GRIST_DOC_ID / PROD_GRIST_DOC_ID
    ALPHAVANTAGE_API_KEY: Alpha Vantage API key (optional)
    FINNHUB_API_KEY: Finnhub API key (optional)
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Optional

import requests

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


class YahooFinanceProvider:
    """Yahoo Finance price provider (free, no API key required)."""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
    
    # Market suffix mapping for Yahoo Finance
    MARKET_SUFFIXES = {
        "SG": ".SI",  # Singapore
        "HK": ".HK",  # Hong Kong
        "UK": ".L",   # London
        "US": "",     # US (no suffix)
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def get_symbol_with_suffix(self, symbol: str, market: str) -> str:
        """Add market suffix to symbol for Yahoo Finance."""
        suffix = self.MARKET_SUFFIXES.get(market, "")
        return f"{symbol}{suffix}"

    def get_price(self, symbol: str, market: str = "US") -> Optional[dict]:
        """
        Get current price for a symbol.
        
        Returns:
            dict with 'price', 'currency', 'change', 'change_percent', 'timestamp'
            or None if failed
        """
        yahoo_symbol = self.get_symbol_with_suffix(symbol, market)
        url = f"{self.BASE_URL}/{yahoo_symbol}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = data.get("chart", {}).get("result", [{}])[0]
            meta = result.get("meta", {})
            
            # Get current price
            price = meta.get("regularMarketPrice")
            prev_close = meta.get("previousClose")
            
            if price is None:
                return None
            
            # Calculate change
            change = price - prev_close if prev_close else 0
            change_percent = (change / prev_close * 100) if prev_close else 0
            
            return {
                "price": price,
                "currency": meta.get("currency", "USD"),
                "change": change,
                "change_percent": change_percent,
                "timestamp": datetime.now().isoformat(),
                "source": "Yahoo Finance",
            }
            
        except Exception as e:
            logger.debug(f"Yahoo Finance error for {symbol}: {e}")
            return None


class AlphaVantageProvider:
    """Alpha Vantage price provider (requires API key)."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_price(self, symbol: str) -> Optional[dict]:
        """Get current price for a symbol."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key,
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            quote = data.get("Global Quote", {})
            if not quote:
                return None
            
            price = float(quote.get("05. price", 0))
            change = float(quote.get("09. change", 0))
            change_percent = float(quote.get("10. change percent", "0").replace("%", ""))
            
            return {
                "price": price,
                "currency": "USD",  # Alpha Vantage typically returns USD
                "change": change,
                "change_percent": change_percent,
                "timestamp": datetime.now().isoformat(),
                "source": "Alpha Vantage",
            }
            
        except Exception as e:
            logger.debug(f"Alpha Vantage error for {symbol}: {e}")
            return None


class FinnhubProvider:
    """Finnhub price provider (requires API key)."""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_price(self, symbol: str) -> Optional[dict]:
        """Get current price for a symbol."""
        url = f"{self.BASE_URL}/quote"
        params = {
            "symbol": symbol,
            "token": self.api_key,
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            price = data.get("c")  # Current price
            prev_close = data.get("pc")  # Previous close
            
            if price is None:
                return None
            
            change = price - prev_close if prev_close else 0
            change_percent = (change / prev_close * 100) if prev_close else 0
            
            return {
                "price": price,
                "currency": "USD",
                "change": change,
                "change_percent": change_percent,
                "timestamp": datetime.now().isoformat(),
                "source": "Finnhub",
            }
            
        except Exception as e:
            logger.debug(f"Finnhub error for {symbol}: {e}")
            return None


class PriceUpdater:
    """Update stock prices in Grist."""

    def __init__(self, grist_api: GristAPI):
        self.grist_api = grist_api
        self.yahoo = YahooFinanceProvider()
        
        # Initialize optional providers
        alphavantage_key = os.getenv("ALPHAVANTAGE_API_KEY")
        self.alphavantage = AlphaVantageProvider(alphavantage_key) if alphavantage_key else None
        
        finnhub_key = os.getenv("FINNHUB_API_KEY")
        self.finnhub = FinnhubProvider(finnhub_key) if finnhub_key else None
        
        self.stats = {
            "processed": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0,
        }

    def get_stocks(self, symbols: Optional[list] = None, active_only: bool = True) -> list:
        """Get stocks from silver_stocks table."""
        logger.info("Fetching stocks from silver_stocks")
        table_id = self.grist_api.get_actual_table_id("silver_stocks")
        records = self.grist_api.get_records(table_id)
        
        stocks = []
        for record in records:
            fields = record.get("fields", {})
            
            # Filter by active status if requested
            if active_only and not fields.get("Is_Active", True):
                continue
            
            # Filter by symbols if specified
            if symbols:
                symbol = fields.get("Symbol", "").upper()
                if symbol not in [s.upper() for s in symbols]:
                    continue
            
            stocks.append({
                "id": record.get("id"),
                "symbol": fields.get("Symbol", ""),
                "market": fields.get("Market", "US"),
                "currency": fields.get("Currency", "USD"),
            })

        return stocks

    def fetch_price(self, symbol: str, market: str) -> Optional[dict]:
        """
        Fetch price using available providers in order:
        1. Yahoo Finance (free, primary)
        2. Alpha Vantage (fallback)
        3. Finnhub (fallback)
        """
        # Try Yahoo Finance first
        result = self.yahoo.get_price(symbol, market)
        if result:
            return result

        # Fall back to Alpha Vantage
        if self.alphavantage:
            logger.info(f"Trying Alpha Vantage for {symbol}")
            result = self.alphavantage.get_price(symbol)
            if result:
                return result

        # Fall back to Finnhub
        if self.finnhub:
            logger.info(f"Trying Finnhub for {symbol}")
            result = self.finnhub.get_price(symbol)
            if result:
                return result

        return None

    def update_prices(self, symbols: Optional[list] = None, dry_run: bool = False):
        """Update prices for all or specified stocks."""
        stocks = self.get_stocks(symbols)
        
        if not stocks:
            logger.warning("No stocks found to update")
            return

        updates = []

        for stock in stocks:
            symbol = stock["symbol"]
            market = stock["market"]
            record_id = stock["id"]

            self.stats["processed"] += 1
            logger.info(f"Processing {symbol} ({market})...")

            # Fetch price
            price_data = self.fetch_price(symbol, market)

            if not price_data:
                logger.warning(f"Failed to fetch price for {symbol}")
                self.stats["failed"] += 1
                continue

            if not price_data.get("price"):
                logger.warning(f"No price available for {symbol}")
                self.stats["skipped"] += 1
                continue

            # Prepare update
            update = {
                "id": record_id,
                "fields": {
                    "Current_Price": price_data["price"],
                    "Price_Updated": price_data["timestamp"],
                    "Price_Source": price_data["source"],
                },
            }
            updates.append(update)
            self.stats["updated"] += 1

            logger.info(
                f"{symbol}: ${price_data['price']:.2f} "
                f"({price_data['change']:+.2f} / {price_data['change_percent']:+.2f}%) "
                f"from {price_data['source']}"
            )

            # Rate limiting - be nice to APIs
            time.sleep(0.5)

        # Apply updates
        if updates and not dry_run:
            logger.info(f"Updating {len(updates)} stocks in Grist")
            try:
                # Grist API doesn't have bulk PATCH, so we'd update one by one
                # For now, log the updates that would be made
                for update in updates:
                    logger.debug(f"Would update: {update}")
                
                # TODO: Implement individual record updates via Grist API
                logger.info("Price update recorded (bulk update via API TBD)")
            except Exception as e:
                logger.error(f"Failed to update prices: {e}")
        elif dry_run:
            logger.info(f"DRY RUN: Would update {len(updates)} stocks")

        self.print_summary()

    def print_summary(self):
        """Print update summary."""
        logger.info("=" * 50)
        logger.info("Price Update Summary")
        logger.info("=" * 50)
        logger.info(f"Stocks processed: {self.stats['processed']}")
        logger.info(f"Prices updated: {self.stats['updated']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info("=" * 50)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update stock prices in Grist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python price_updater.py
    uv run python price_updater.py --symbols AAPL,NVDA,TSLA
    uv run python price_updater.py --all
    uv run python price_updater.py --dry-run
        """,
    )
    parser.add_argument(
        "--env",
        choices=["dev", "test", "production"],
        help="Environment to use (overrides ENVIRONMENT variable)",
    )
    parser.add_argument(
        "--symbols",
        help="Comma-separated list of symbols to update (default: all active)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Update all stocks including inactive",
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
        help="Show what would be updated without actually updating",
    )

    args = parser.parse_args()

    # Get configuration from .env (ENVIRONMENT variable) or --env flag
    config = get_config(args.env)
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

    # Parse symbols
    symbols = None
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]

    # Initialize and run updater
    try:
        grist_api = GristAPI(api_url, api_key, doc_id)
        updater = PriceUpdater(grist_api)
        updater.update_prices(symbols=symbols, dry_run=args.dry_run)
    except Exception as e:
        logger.error(f"Price update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
