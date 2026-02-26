# Sample Input Files

This document describes the sample CSV files in the `samples/` folder for testing the Grist Stock Tracker import functionality.

## Location

All sample files are located in the `samples/` folder at the project root.

## File Overview

| File | Description | Records | Markets |
|------|-------------|---------|---------|
| `samples/sample-template-input.csv` | Original template with 2 example rows | 2 | SG, US |
| `samples/sample-minimal-test.csv` | Minimal test file for quick validation | 7 | SG, US |
| `samples/sample-singapore-stocks.csv` | Singapore stocks only | 14 | SG |
| `samples/sample-us-stocks.csv` | US stocks only | 17 | US |
| `samples/sample-mixed-portfolio.csv` | Mixed SG/US portfolio with dividends | 22 | SG, US |

## File Details

### sample-minimal-test.csv
**Use case:** Quick validation of Bronze → Silver → Gold pipeline

Contains:
- 2 Singapore stocks (OV8, D05) - Buy transactions
- 2 US stocks (AAPL, NVDA) - Buy transactions
- 1 Sell transaction (NVDA)
- 2 Dividend transactions (D05, AAPL)

### sample-singapore-stocks.csv
**Use case:** Testing Singapore market (SGX) specific features

Contains:
- **Stocks:** OV8, D05, U11, Z74, C38, A17U, ME8U, CJLU, RE2S, CLR
- **Transactions:** 12 Buy + 2 Sell + 2 Dividend = 14 total
- **Currency:** SGD
- **Fee structure:** Platform Fees, Consumption Tax, Settlement Fees, Commission, Trading Fees, Clearing Fees

Key stocks:
- OV8 (Sheng Siong) - Consumer staples
- D05 (DBS) - Banking
- U11 (UOB) - Banking
- Z74 (Singtel) - Telecommunications
- C38 (CapitaLand Integrated Commercial Trust) - REIT
- A17U (Ascendas REIT) - REIT
- ME8U (Mapletree Industrial Trust) - REIT

### sample-us-stocks.csv
**Use case:** Testing US market specific features

Contains:
- **Stocks:** AAPL, NVDA, MSFT, AMD, TSLA, GOOGL, AMZN, VOO, QQQ, INTC, JPM
- **Transactions:** 12 Buy + 2 Sell + 3 Dividend = 17 total
- **Currency:** USD
- **Fee structure:** Platform Fees, Consumption Tax, Settlement Fees, Trading Activity Fees, Consolidated Audit Trail Fees, Commission

Key stocks:
- AAPL (Apple) - Technology
- NVDA (NVIDIA) - Technology
- MSFT (Microsoft) - Technology
- AMD (Advanced Micro Devices) - Technology
- TSLA (Tesla) - Automotive/Technology
- GOOGL (Alphabet) - Technology
- AMZN (Amazon) - Consumer/Technology
- VOO (Vanguard S&P 500 ETF) - ETF
- QQQ (Invesco QQQ Trust) - ETF
- INTC (Intel) - Technology
- JPM (JPMorgan Chase) - Banking

### sample-mixed-portfolio.csv
**Use case:** Testing a realistic multi-currency portfolio

Contains:
- **Mixed markets:** Singapore (SG) and US (US) stocks
- **Transactions:** 15 Buy + 2 Sell + 5 Dividend = 22 total
- **Time period:** January 2026 - March 2026
- **Features tested:** 
  - Multi-currency (SGD, USD)
  - Different fee structures per market
  - Partial sells (realizing gains)
  - Dividend tracking

## CSV Format

All files follow the moomoo export format with the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| Side | Transaction type: Buy, Sell, Dividend | Buy |
| Symbol | Stock ticker | OV8, AAPL |
| Name | Company name | Sheng Siong Group Ltd |
| Order Price | Original order price | 2.92 |
| Order Qty | Original order quantity | 1000 |
| Order Amount | Original order amount | 2920.00 |
| Status | Order status | Filled |
| Filled@Avg Price | Fill summary | 1000@2.91 |
| Order Time | Order timestamp | Feb 9, 2026 11:00:40 SGT |
| Order Type | Order type: Limit, Market | Limit |
| Time-in-Force | Duration: Day, GTC | Day |
| Markets | Market code: SG, US | SG |
| Currency | Currency code: SGD, USD | SGD |
| Fill Qty | Filled quantity | 1000 |
| Fill Price | Filled price per share | 2.91 |
| Fill Amount | Total fill amount | 2910.00 |
| Fill Time | Fill timestamp | Feb 9, 2026 12:58:43 SGT |
| Platform Fees | Platform/broker fees | 0.99 |
| Consumption Tax | Tax amount | 0.19 |
| Settlement Fees | Settlement fees | varies |
| Trading Activity Fees | US-specific trading fees | 0.01 |
| Consolidated Audit Trail Fees | US-specific CAT fees | 0.01 |
| Commission | Commission fees | 0.99 |
| Trading Fees | Trading fees | varies |
| Clearing Fees | Clearing fees | 0.09 |
| Total | Total fees paid | 2.28 |

## Import Process

1. **Bronze Layer:** CSV data is imported as-is into `Bronze_Transactions`
2. **Validation:** Records are validated (check for duplicates, missing fields)
3. **Silver Layer:** Valid records are transformed and inserted into `Silver_Transactions`
4. **Gold Layer:** Positions and metrics are calculated in `Gold_Positions` and `Gold_Stocks`

## Testing Scenarios

### Basic Import Test
```bash
# Use minimal test file for quick validation
uv run python scripts/csv_import_helper.py samples/sample-minimal-test.csv
```

### Full Portfolio Test
```bash
# Test with realistic portfolio
uv run python scripts/csv_import_helper.py samples/sample-mixed-portfolio.csv
```

### Market-Specific Tests
```bash
# Test Singapore market handling
uv run python scripts/csv_import_helper.py samples/sample-singapore-stocks.csv

# Test US market handling
uv run python scripts/csv_import_helper.py samples/sample-us-stocks.csv
```

## Data Validation Notes

- All prices and quantities are realistic for the stated time period (2025-2026)
- Fee calculations follow moomoo's fee structure
- Dividend amounts are estimated based on historical yields
- Exchange rates (SGD/USD) are not included - handle at reporting level
- Time zones: SGT (Singapore Time) for SG market, ET (Eastern Time) for US market
