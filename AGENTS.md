# Grist Stock Tracker - Agent Guide

## Project Overview

Grist Stock Tracker is a **self-hosted stock portfolio tracking application** built on [Grist](https://getgrist.com) - a spreadsheet-database hybrid platform. It provides spreadsheet-like data entry with database power, automated P/L calculations, live price updates, and monthly archiving.

This project is designed for personal finance tracking with complete data privacy through self-hosting.

## Core Development Philosophy

**SIMPLICITY FIRST**: Always search for the simplest logic when trying to solve an issue. Complex solutions often introduce more problems than they solve.

**NO LAZINESS RULE**:
- Never use temporary fixes or workarounds
- Always find and fix the root cause of bugs
- Act as a senior developer would - thorough, thoughtful, and complete
- If there's a bug, trace it to its source and resolve it properly

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Core Platform | Grist (Podman/Docker) | Spreadsheet-database hybrid UI |
| Orchestration | Podman Compose / Docker Compose | Container management |
| Database (Optional) | PostgreSQL 15 | External database backend |
| Backup | docker-volume-backup (podman-compatible) | Automated volume backups |
| Data Processing | Python 3.9+ with UV | CSV import, price fetching |

## Critical Development Rules

### 1. UV Package Management (CRITICAL)
**ALWAYS USE UV FOR PYTHON COMMANDS**
- All Python script executions must use `uv run python script.py` instead of `python script.py`
- All Python module executions must use `uv run python -m module` instead of `python -m module`
- Package installation: `uv add package_name` instead of `pip install`
- Package removal: `uv remove package_name`
- Sync dependencies: `uv sync`

**Examples:**
- ✅ `uv run python scripts/ingest_csv.py`
- ❌ `python scripts/ingest_csv.py`
- ✅ `uv run python -m pytest tests/`
- ❌ `python -m pytest tests/`

### 2. Input Data Preservation Rule (CRITICAL)
**DO NOT CHANGE INPUT FILE FORMATS**
- Never modify the structure, format, or schema of input CSV files
- Input files must be processed in their original form as provided by brokers
- Create logic that adapts to and handles the existing data format
- If a table schema mismatch occurs, modify the processing logic, not the input format
- Example: If a table expects 23 columns but CSV has 16, add the missing columns programmatically during processing

### 3. Data Storage Architecture Rule (CRITICAL)
**BRONZE/SILVER/GOLD DATA LAYER SEPARATION**
- Raw data must be stored in tables with `bronze_` prefix (e.g., `bronze_transactions`, `bronze_moomoo`)
- Transformed data at intermediate stages uses `silver_` prefix (e.g., `silver_transactions`, `silver_stocks`)
- Final processed/analytics-ready data uses `gold_` prefix (e.g., `gold_positions`, `gold_holdings`)
- Never mix raw and transformed data in the same table
- Each layer serves distinct purposes:
  - **Bronze**: Exact copy of source data for audit and reprocessing
  - **Silver**: Cleaned, standardized, and validated data
  - **Gold**: Business-ready, aggregated, and enriched data

### 4. Documentation Naming Convention
All documentation files should follow the pattern: `NN-descriptive-name.md`
- `NN` = Two-digit number for ordering (01, 02, 03, etc.)
- Use hyphens for word separation
- Lowercase filenames
- Descriptive names that clearly indicate content

**Examples:**
- ✅ `01-architecture.md`
- ✅ `02-database-schema.md`
- ✅ `03-api-reference.md`
- ❌ `Architecture.md`
- ❌ `database_schema.md`

## Project Structure

```
grist-stock-tracker/
├── docker-compose.yml          # Main orchestration file
├── .env.example                # Environment template (root)
├── README.md                   # User-facing documentation
├── AGENTS.md                   # This file - agent guide
├── docker/                     # Docker configuration (.env file)
├── docs/                       # Documentation
│   ├── 01-project-spec.md      # Detailed project specification
│   ├── prompts.txt             # Original project generation prompt
│   ├── markmap.svg             # Visual project mind map
│   └── sample-files-readme.md  # Documentation for sample files
├── samples/                    # Sample input files for testing
│   ├── sample-template-input.csv   # Original template (2 rows)
│   ├── sample-minimal-test.csv     # Minimal test file (7 rows)
│   ├── sample-singapore-stocks.csv # Singapore stocks test data (14 rows)
│   ├── sample-us-stocks.csv        # US stocks test data (17 rows)
│   └── sample-mixed-portfolio.csv  # Mixed SG/US portfolio test data (22 rows)
├── scripts/                    # Python automation scripts
├── templates/                  # Grist templates (.grist files)
├── grist-data/                 # Persisted Grist data (created at runtime)
└── backups/                    # Backup archives (created at runtime)
```

## Architecture

### Container Services

1. **grist** (Primary)
   - Image: `gristlabs/grist:latest`
   - Port: `8484`
   - Volumes:
     - `./grist-data:/persist` - Persistent data
     - `./scripts:/persist/scripts:ro` - Read-only automation scripts
     - `./templates:/persist/templates:ro` - Read-only templates
     - `./backups:/persist/backups` - Backup storage
   - Note: Runs via Podman (using docker alias)

2. **postgres** (Optional)
   - Image: `postgres:15-alpine`
   - Profile: `postgres` (started with `--profile postgres`)
   - Used for external database storage instead of SQLite

3. **backup** (Optional)
   - Image: `offen/docker-volume-backup:latest`
   - Profile: `backup`
   - Runs daily at 2 AM, 30-day retention
   - Supports S3 upload

### Data Model (Medallion Architecture)

This project follows the **Medallion Architecture** pattern with Bronze, Silver, and Gold layers:

- **Bronze Layer**: Raw data ingestion - stores imported CSV data without any modifications
- **Silver Layer**: Cleaned, validated, and enriched transactional data
- **Gold Layer**: Aggregated, business-level metrics and calculated views

#### Data Flow

```
Broker CSV Export → bronze_transactions → silver_transactions → gold_positions
                                                   ↓
                                           silver_stocks → gold_stocks
                                                   ↓
                                        gold_monthly_archive
```

---

### Bronze Layer (Raw Data)

#### bronze_transactions (Raw Imports)
Stores imported CSV data exactly as exported from brokers without any modifications.

| Column | Type | Description |
|--------|------|-------------|
| Import_ID | Text (Primary) | Unique import identifier (auto-generated) |
| Import_Date | DateTime | When the CSV was imported |
| Source_File | Text | Original CSV filename |
| Raw_Data | Text | Full raw CSV row (JSON or pipe-delimited) |
| Side | Text | Original Side value from CSV |
| Symbol | Text | Original Symbol value from CSV |
| Name | Text | Original Name value from CSV |
| Order_Price | Numeric | Original order price |
| Order_Qty | Numeric | Original order quantity |
| Order_Amount | Numeric | Original order amount |
| Status | Text | Order status |
| Filled_Avg_Price | Numeric | Filled average price |
| Order_Time | DateTime | Original order timestamp |
| Order_Type | Text | Order type |
| Time_in_Force | Text | Time in force setting |
| Fill_Qty | Numeric | Filled quantity |
| Fill_Price | Numeric | Filled price |
| Fill_Amount | Numeric | Filled amount |
| Fill_Time | DateTime | Fill timestamp |
| Platform_Fees | Numeric | Platform fees |
| Tax | Numeric | Tax amount |
| Settlement_Fees | Numeric | Settlement fees |
| Trading_Fees | Numeric | Trading fees |
| CAT_Fees | Numeric | CAT fees |
| Commission | Numeric | Commission |
| Clearing_Fees | Numeric | Clearing fees |
| Platform | Text | Broker platform name |
| Validation_Status | Choice | Valid / Invalid / Pending |
| Validation_Errors | Text | Any validation error messages |

> **Important**: Bronze layer data is never modified. All transformations happen when data flows to Silver layer.

---

### Silver Layer (Cleaned & Enriched)

#### silver_stocks (Master Reference Data)
Cleaned and validated stock master data with price information.

| Column | Type | Description |
|--------|------|-------------|
| Symbol | Text (Primary) | Normalized stock ticker (e.g., AAPL, OV8) |
| Name | Text | Cleaned company name |
| Market | Choice | SG / US / HK / UK |
| Currency | Choice | SGD / USD / HKD / GBP |
| Asset_Type | Choice | Stock / ETF / REIT / Bond |
| Current_Price | Numeric | Latest market price |
| Price_Updated | DateTime | Last update timestamp |
| Price_Source | Text | Source of price data (Yahoo, AlphaVantage, Finnhub) |
| Is_Active | Boolean | Whether this stock is actively held |

#### silver_transactions (Cleaned Activity Log)
Validated and enriched transactions derived from bronze_transactions.

| Column | Type | Description |
|--------|------|-------------|
| Transaction_ID | Text (Primary) | Unique transaction identifier |
| Bronze_Ref | Reference → bronze_transactions | Link to raw source record |
| Date | DateTime | Cleaned transaction date |
| Side | Choice | Buy / Sell / Dividend |
| Symbol | Reference → silver_stocks | Linked stock |
| Fill_Qty | Numeric | Shares traded (validated positive) |
| Fill_Price | Currency | Price per share (validated) |
| Fill_Amount | Currency | Total fill value (calculated/validated) |
| Platform_Fees | Currency | Platform fees |
| Tax | Currency | Tax amount |
| Settlement_Fees | Currency | Settlement fees |
| Trading_Fees | Currency | Trading fees |
| CAT_Fees | Currency | CAT fees |
| Commission | Currency | Commission |
| Clearing_Fees | Currency | Clearing fees |
| Total_Fees | Formula | Sum of all fees |
| Net_Amount | Formula | Fill_Amount + fees (Buy) or Fill_Amount - fees (Sell) |
| Platform | Text | Broker (e.g., moomoo) |
| Notes | Text | Optional notes |

---

### Gold Layer (Aggregated & Business Metrics)

#### gold_stocks (Portfolio Master View)
Aggregated stock-level metrics for portfolio overview.

| Column | Type | Description |
|--------|------|-------------|
| Symbol | Reference → silver_stocks | Linked stock |
| Name | Formula | silver_stocks.Name |
| Market | Formula | silver_stocks.Market |
| Currency | Formula | silver_stocks.Currency |
| Asset_Type | Formula | silver_stocks.Asset_Type |
| Current_Price | Formula | silver_stocks.Current_Price |
| Total_Shares | Formula | Aggregated from gold_positions |
| Total_Invested | Formula | Cost basis across all transactions |
| Avg_Cost_Basis | Formula | Average cost per share |
| Current_Market_Value | Formula | Shares × Current_Price |
| Unrealized_P_L | Formula | Paper gains/losses |
| Realized_P_L | Formula | Realized gains/losses from closed positions |
| Total_Return_Pct | Formula | Total return percentage |
| Last_Transaction_Date | Formula | Most recent transaction date |

#### gold_positions (Calculated Holdings)
Real-time position calculations per stock.

| Column | Type | Description |
|--------|------|-------------|
| Position_ID | Text (Primary) | Unique position identifier |
| Symbol | Reference → silver_stocks | Linked stock |
| Total_Shares | Formula | Running share count from silver_transactions |
| Total_Invested | Formula | Sum of Net_Amount for Buy transactions |
| Avg_Cost_Basis | Formula | Average cost per share |
| Current_Market_Value | Formula | Shares × Current_Price |
| Unrealized_P_L | Formula | Paper gains/losses |
| Realized_P_L | Formula | Closed position P/L |
| Return_Pct | Formula | Percentage return |
| Days_Held | Formula | Days since first purchase |

#### gold_monthly_archive (Historical Snapshots)
Month-end position snapshots for historical tracking.

| Column | Type | Description |
|--------|------|-------------|
| Archive_ID | Text (Primary) | Unique archive record identifier |
| Month | Date | Month-end date |
| Symbol | Reference → silver_stocks | Linked stock |
| Shares_Held | Numeric | Position size at month-end |
| Avg_Cost | Currency | Cost basis at month-end |
| Month_End_Price | Currency | Closing price |
| Market_Value | Currency | Position value |
| Unrealized_PL | Currency | Unrealized P/L |
| Realized_PL_Month | Currency | Realized P/L during the month |
| Total_Return_Pct | Numeric | Total return percentage |
| Snapshot_Taken | DateTime | When snapshot was created |

---

### Column Naming Conventions

Grist supports **dual naming** for columns - a user-friendly display name and a formula-friendly identifier:

| Property | Purpose | Constraints | Example |
|----------|---------|-------------|---------|
| **Column Label** | Display name in UI | Can have spaces, special chars | `Fill Price`, `Order Qty`, `Platform Fees` |
| **Column ID** | Formula/database identifier | Python-friendly, no spaces | `Fill_Price`, `Order_Qty`, `Platform_Fees` |

#### How to Configure

**Via Column Options Panel:**
1. Select a column
2. Open the **Creator Panel** (right sidebar) → **Column** tab
3. **Column Label** - Edit the display name (what users see)
4. **Column ID** - Click the 🔗 icon to edit the formula identifier

**Via Rename Dialog:**
- Double-click column header or select "Rename column"
- Edit the **Label** field
- Click the 🔗 icon to unlock and edit the **ID** field

#### Naming Guidelines

**Column Labels (UI Display):**
- Use readable names with spaces
- Use title case for consistency
- Include units where applicable: `Fill Price`, `Order Qty`, `Total Fees`

**Column IDs (Formula Reference):**
- Use `snake_case` (lowercase with underscores)
- Must be valid Python identifiers
- Must be unique within the table
- Keep them short but descriptive

#### Common Column Name Mapping

| Column Label (UI) | Column ID (Formula) |
|-------------------|---------------------|
| `Import ID` | `Import_ID` |
| `Import Date` | `Import_Date` |
| `Source File` | `Source_File` |
| `Raw Data` | `Raw_Data` |
| `Order Price` | `Order_Price` |
| `Order Qty` | `Order_Qty` |
| `Order Amount` | `Order_Amount` |
| `Filled Avg Price` | `Filled_Avg_Price` |
| `Order Time` | `Order_Time` |
| `Order Type` | `Order_Type` |
| `Time in Force` | `Time_in_Force` |
| `Fill Qty` | `Fill_Qty` |
| `Fill Price` | `Fill_Price` |
| `Fill Amount` | `Fill_Amount` |
| `Fill Time` | `Fill_Time` |
| `Platform Fees` | `Platform_Fees` |
| `Settlement Fees` | `Settlement_Fees` |
| `Trading Fees` | `Trading_Fees` |
| `CAT Fees` | `CAT_Fees` |
| `Clearing Fees` | `Clearing_Fees` |
| `Validation Status` | `Validation_Status` |
| `Validation Errors` | `Validation_Errors` |
| `Transaction ID` | `Transaction_ID` |
| `Bronze Ref` | `Bronze_Ref` |
| `Total Fees` | `Total_Fees` |
| `Net Amount` | `Net_Amount` |
| `Current Price` | `Current_Price` |
| `Price Updated` | `Price_Updated` |
| `Price Source` | `Price_Source` |
| `Is Active` | `Is_Active` |
| `Asset Type` | `Asset_Type` |
| `Position ID` | `Position_ID` |
| `Total Shares` | `Total_Shares` |
| `Total Invested` | `Total_Invested` |
| `Avg Cost Basis` | `Avg_Cost_Basis` |
| `Current Market Value` | `Current_Market_Value` |
| `Unrealized P/L` | `Unrealized_P_L` |
| `Realized P/L` | `Realized_P_L` |
| `Total Return %` | `Total_Return_Pct` |
| `Last Transaction Date` | `Last_Transaction_Date` |
| `Return %` | `Return_Pct` |
| `Days Held` | `Days_Held` |
| `Archive ID` | `Archive_ID` |
| `Month End` | `Month_End` |
| `Shares Held` | `Shares_Held` |
| `Avg Cost` | `Avg_Cost` |
| `Month End Price` | `Month_End_Price` |
| `Market Value` | `Market_Value` |
| `Unrealized P/L` | `Unrealized_PL` |
| `Realized P/L (Month)` | `Realized_PL_Month` |
| `Snapshot Taken` | `Snapshot_Taken` |

> **Note:** In formulas, always reference columns by their **Column ID**: `$Fill_Price * $Order_Qty` not `$Fill Price * $Order Qty`

---

### Key Formulas (Grist Python)

```python
# silver_transactions: Total_Fees
sum([$Platform_Fees or 0, $Tax or 0, $Settlement_Fees or 0, 
     $Trading_Fees or 0, $CAT_Fees or 0, $Commission or 0, 
     $Clearing_Fees or 0])

# silver_transactions: Net_Amount
$Fill_Amount + $Total_Fees if $Side == "Buy" else $Fill_Amount - $Total_Fees

# gold_positions: Total_Shares
import itertools
txns = silver_transactions.lookupRecords(Symbol=$Symbol)
return sum(t.Fill_Qty if t.Side=="Buy" else -t.Fill_Qty for t in txns)

# gold_positions: Total_Invested
txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side="Buy")
return sum(t.Net_Amount for t in txns)

# gold_positions: Avg_Cost_Basis
$Total_Invested / $Total_Shares if $Total_Shares > 0 else 0

# gold_positions: Current_Market_Value
$Total_Shares * $Symbol.Current_Price if $Total_Shares > 0 else 0

# gold_positions: Unrealized_P_L
$Current_Market_Value - $Total_Invested if $Total_Shares > 0 else 0

# gold_positions: Realized_P_L
# Sum of gains from Sell transactions
txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side="Sell")
return sum(t.Fill_Amount - (t.Fill_Qty * $Avg_Cost_Basis) for t in txns)

# gold_stocks: Total_Return_Pct
($Unrealized_P_L + $Realized_P_L) / $Total_Invested * 100 if $Total_Invested > 0 else 0
```

## Build and Run Commands (Podman/Docker)

> **Note:** This project uses **Podman** as the container runtime. An alias is configured as `docker=podman`, so all commands use `docker` syntax but execute via Podman.

### Quick Start

```bash
# 1. Clone and configure
cp .env.example docker/.env  # Note: docker/.env is used by compose
# Edit docker/.env with your settings

# 2. Start the application (using podman via docker alias)
docker-compose up -d

# 3. Access Grist at http://localhost:8484
```

### Common Operations

```bash
# Start with PostgreSQL
docker-compose --profile postgres up -d

# Start with backup service
docker-compose --profile backup up -d

# Start all services
docker-compose --profile postgres --profile backup up -d

# View logs
docker-compose logs -f grist

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Backup manually
docker-compose exec backup backup

# Restore from backup
# 1. Stop containers: docker-compose down
# 2. Extract backup to grist-data/
# 3. Restart: docker-compose up -d
```

### Podman-Specific Notes

- Podman runs containers rootless by default (more secure)
- No Docker daemon required
- Uses `docker-compose` command via alias to `podman-compose` or compatible tool
- Volume mounts work the same way as Docker
- All `docker` commands in this guide are executed via the `docker=podman` alias

## Environment Configuration

Copy `.env.example` to `docker/.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `GRIST_SESSION_SECRET` | Yes | Session encryption key |
| `POSTGRES_PASSWORD` | No | PostgreSQL password (if using postgres profile) |
| `S3_BUCKET` | No | S3 bucket for backups |
| `AWS_ACCESS_KEY` | No | AWS access key for S3 |
| `AWS_SECRET_KEY` | No | AWS secret key for S3 |
| `AWS_REGION` | No | AWS region (default: us-east-1) |
| `ALPHAVANTAGE_API_KEY` | No | Alpha Vantage API for prices |
| `FINNHUB_API_KEY` | No | Finnhub API for prices |
| `ADMIN_EMAIL` | No | Admin email address |

## Development Conventions

### Working Directory

The project working directory is preset to:
```
/Users/g/Library/CloudStorage/Dropbox/Code/grist-stock-tracker
```

All commands run from this directory. No `cd` needed:
- ✅ `git status`
- ✅ `ls samples/`
- ✅ `docker-compose up -d`

### Code Organization

- **scripts/**: Python automation scripts (CSV import, price updates)
- **templates/**: Grist document templates (.grist files)
- **docs/**: Additional documentation
- **docker/**: Container configuration (Podman/Docker)

### Python Best Practices

#### Type Hints
- Use type hints for all function parameters and return values
- Use `from typing import` for complex types (List, Dict, Optional, etc.)

```python
from typing import Optional, List

def process_transactions(file_path: str, limit: Optional[int] = None) -> List[dict]:
    pass
```

#### Function Design
- Keep functions small and focused (single responsibility)
- Maximum ~50 lines per function (prefer smaller)
- Use descriptive function names that indicate what they do

#### Error Handling
- Use specific exception types, not bare `except:`
- Always log errors with context
- Fail fast - validate inputs early

```python
try:
    data = process_file(path)
except FileNotFoundError as e:
    logger.error(f"File not found: {path}", exc_info=True)
    raise
except pd.errors.ParserError as e:
    logger.error(f"Failed to parse CSV: {path}", exc_info=True)
    raise
```

#### Logging
- Use Python's `logging` module, not `print()` statements
- Log at appropriate levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include context in log messages

```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Processing {len(transactions)} transactions from {source}")
```

#### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Separate each group with a blank line

```python
import os
from datetime import datetime
from typing import Optional

import pandas as pd
from peewee import Model

from src.database.models import Transaction
from src.utils.logging import setup_logger
```

### Python Scripts (Future)

Planned scripts to add to `scripts/`:

1. **csv_import_helper.py**: 
   - Read moomoo CSV exports
   - Store raw data in bronze_transactions without modification
   - Validate and transform to silver_transactions
   
2. **price_updater.py**: 
   - Fetch live prices from Yahoo Finance/Alpha Vantage/Finnhub
   - Update silver_stocks.Current_Price
   
3. **monthly_archiver.py**: 
   - Generate month-end snapshots
   - Populate gold_monthly_archive

### CSV Import Format

The project supports importing from moomoo export format. See `docs/sample-files-readme.md` for detailed documentation of the CSV format and available sample files.

**Sample Files Available** (in `samples/` folder):

| File | Description | Use Case |
|------|-------------|----------|
| `sample-minimal-test.csv` | 7 transactions (SG + US) | Quick validation testing |
| `sample-singapore-stocks.csv` | 14 SG stocks transactions | Singapore market testing |
| `sample-us-stocks.csv` | 17 US stocks transactions | US market testing |
| `sample-mixed-portfolio.csv` | 22 mixed transactions | Realistic portfolio testing |

**CSV Columns:** Side, Symbol, Name, Order Price, Order Qty, Order Amount, Status, Filled@Avg Price, Order Time, Order Type, Time-in-Force, Fill Qty, Fill Price, Fill Amount, Fill Time, Markets, Currency, Platform Fees, Tax/Consumption Tax, Settlement Fees, Trading Activity Fees, Consolidated Audit Trail Fees, Commission, Trading Fees, Clearing Fees, Total

**Import Process**:
1. CSV is uploaded via script or UI
2. Data is stored **as-is** in bronze_transactions
3. Validation runs on Bronze data
4. Valid records are transformed and inserted into silver_transactions
5. silver_stocks is updated with new symbols if needed

## Testing Strategy

Currently, this project relies on:

1. **Manual testing** through Grist UI
2. **CSV validation** at Bronze layer
3. **Formula verification** in Grist formula columns
4. **Data quality checks** between Bronze → Silver → Gold layers

No automated test suite exists yet. Consider adding:
- Unit tests for Python scripts in `scripts/`
- Integration tests for CSV transformation (Bronze → Silver)
- API tests for price fetching
- Data quality tests (e.g., Silver totals match Bronze source)

## Security Considerations

1. **Change default secrets**: Always change `GRIST_SESSION_SECRET` in production
2. **Secure passwords**: Use strong PostgreSQL passwords
3. **Access control**: Grist is configured with login required (`GRIST_LOGIN_REQUIRED=true`)
4. **Sandboxing**: Grist uses gvisor for formula sandboxing (`GRIST_SANDBOX_FLAVOR=gvisor`)
5. **Backups**: Backup files may contain sensitive financial data - secure accordingly
6. **API keys**: Store price API keys in `.env`, never commit them
7. **Bronze layer**: Raw CSV data may contain sensitive info - treated with same security as other layers

## Deployment Notes

### Production Checklist

- [ ] Change `GRIST_SESSION_SECRET` to a secure random string
- [ ] Set strong PostgreSQL password
- [ ] Configure S3 backup (recommended)
- [ ] Set up reverse proxy (nginx/traefik) for SSL
- [ ] Configure proper admin email
- [ ] Disable telemetry (`GRIST_TELEMETRY_LEVEL=off` is already set)
- [ ] Review and set appropriate backup retention

### Reverse Proxy Configuration

When using a reverse proxy, ensure WebSocket support is enabled (required for Grist real-time collaboration).

## Key Files Reference

| File/Folder | Purpose |
|-------------|---------|
| `docker-compose.yml` | Service definitions and orchestration |
| `.env.example` | Configuration template |
| `docs/01-project-spec.md` | Detailed specification with formulas |
| `docs/sample-files-readme.md` | Documentation for sample CSV files |
| `docs/markmap.svg` | Visual project structure diagram |
| `samples/sample-template-input.csv` | Original template (2 rows) |
| `samples/sample-minimal-test.csv` | Minimal test file (7 rows) |
| `samples/sample-singapore-stocks.csv` | Singapore stocks test data (14 rows) |
| `samples/sample-us-stocks.csv` | US stocks test data (17 rows) |
| `samples/sample-mixed-portfolio.csv` | Mixed SG/US portfolio test data (22 rows) |

## Important Implementation Notes

1. **Empty directories**: The `scripts/` and `docs/` directories are currently empty and intended to be populated with Python automation scripts and documentation.

2. **Grist-specific**: This is not a traditional web application. Most business logic is implemented as Grist formulas within the Grist UI, not in application code.

3. **Medallion Architecture**: Data flows unidirectionally from Bronze (raw) → Silver (cleaned) → Gold (aggregated). Never modify Bronze layer data after ingestion.

4. **CSV-first workflow**: The primary data entry method is importing broker CSV exports into bronze_transactions, not manual entry.

5. **Podman/Docker profiles**: PostgreSQL and backup services are optional and require explicit profile flags to start.

6. **Formula language**: Grist uses Python for formulas, but with a restricted environment. See Grist documentation for available functions.

7. **Bronze layer immutability**: The bronze_transactions table should be append-only. If data needs correction, add a correction record or fix in Silver layer, never modify Bronze.

8. **Column naming convention**: Always use **Column Label** for user-friendly display names (with spaces) and **Column ID** for formula references (snake_case). This ensures readable UI while maintaining valid Python identifiers in formulas.

9. **Table naming convention**: Use lowercase with `bronze_`, `silver_`, `gold_` prefixes for table names in Grist (e.g., `bronze_transactions`, `silver_stocks`, `gold_positions`).

## Code Review Checklist

Before considering code complete:
- [ ] Uses `uv run` for all Python commands
- [ ] Includes type hints for function parameters and return values
- [ ] Has appropriate error handling (specific exceptions, not bare `except`)
- [ ] Includes logging instead of print statements
- [ ] Follows data layer separation (bronze_/silver_/gold_ prefixes)
- [ ] Does not modify input file formats
- [ ] Makes minimal, simple changes (simplicity first)
- [ ] Documentation is updated if needed
- [ ] Uses lowercase with prefixes for table names

## External Documentation

- [Grist Documentation](https://support.getgrist.com/)
- [Grist Formula Reference](https://support.getgrist.com/formulas/)
- [Podman Documentation](https://docs.podman.io/)
- [Podman Compose](https://github.com/containers/podman-compose)
- [Docker Compose Reference](https://docs.docker.com/compose/) (compatible)
- [Medallion Architecture Pattern](https://www.databricks.com/glossary/medallion-architecture)
