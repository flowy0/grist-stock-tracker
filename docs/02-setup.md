# Grist Stock Tracker - Setup Guide

Complete setup instructions for the Grist Stock Tracker project.

## Prerequisites

- [Podman](https://podman.io/) (or Docker with `docker=podman` alias)
- [Python 3.11+](https://www.python.org/)
- [UV](https://docs.astral.sh/uv/) - Python package manager
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/flowy0/grist-stock-tracker.git
cd grist-stock-tracker
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env
```

#### Environment Variable Reference

The `ENVIRONMENT` variable controls which configuration is used:

| Variable | Purpose | Example |
|----------|---------|---------|
| `ENVIRONMENT` | Active environment: `dev`, `test`, or `production` | `ENVIRONMENT=dev` |
| `GRIST_API_KEY` | API key for dev environment | (from Grist UI) |
| `GRIST_DOC_ID` | Document ID for dev environment | (from Grist URL) |
| `TEST_GRIST_API_KEY` | API key for test environment | (from Grist UI) |
| `TEST_GRIST_DOC_ID` | Document ID for test environment | (from Grist URL) |
| `PROD_GRIST_API_KEY` | API key for production environment | (from Grist UI) |
| `PROD_GRIST_DOC_ID` | Document ID for production environment | (from Grist URL) |

**How it works:**
- Scripts read `ENVIRONMENT` to determine which config to use
- When `ENVIRONMENT=dev`, scripts use `GRIST_API_KEY` and `GRIST_DOC_ID`
- When `ENVIRONMENT=test`, scripts use `TEST_GRIST_API_KEY` and `TEST_GRIST_DOC_ID`
- Override with `--env` flag: `python script.py --env test`

**Example .env file:**

```bash
# Set your environment: dev | test | production
ENVIRONMENT=dev

# For dev environment (port 8484)
GRIST_API_KEY=your_api_key_here
GRIST_DOC_ID=your_doc_id_here

# For test environment (port 8485)
TEST_GRIST_API_KEY=your_test_api_key_here
TEST_GRIST_DOC_ID=your_test_doc_id_here

# For production environment (port 8484)
PROD_GRIST_API_KEY=your_prod_api_key_here
PROD_GRIST_DOC_ID=your_prod_doc_id_here
```

### 3. Start Podman Machine (macOS)

```bash
# Check if podman machine is running
podman machine list

# Start if not running
podman machine start
```

### 4. Start Grist Services

```bash
# Start Grist container
docker compose up -d grist

# Check logs
docker compose logs -f grist
```

Grist will be available at: http://localhost:8484

### 5. Configure Grist (First Run)

1. Open http://localhost:8484
2. Complete initial setup (create admin user)
3. Create a new document called "Stock Tracker"
4. **Get your Document ID** from the URL: `http://localhost:8484/o/docs/doc/{DOC-ID}/...`
5. **Generate API key**: Profile → Settings → API Key → Create Key
6. **Add to `.env`:**
   ```bash
   echo "GRIST_DOC_ID=your-doc-id-here" >> .env
   echo "GRIST_API_KEY=your-api-key-here" >> .env
   ```

### 6. Setup Python Environment

```bash
cd scripts

# Create virtual environment and install dependencies
uv sync

# Install Playwright browsers (for UI testing)
uv run playwright install chromium
```

### 7. Run Tests

```bash
# Run all unit tests
uv run pytest tests/ -v -m "not ui"

# Expected: 32 tests passing, 2 skipped
```

## Environment Management

The project supports three isolated environments, each with separate data directories and configurations:

| Environment | Port | Data Directory | Config Variables | Use Case |
|-------------|------|----------------|------------------|----------|
| `dev` | 8484 | `./grist-data/dev` | `GRIST_API_KEY`, `GRIST_DOC_ID` | Daily development |
| `test` | 8485 | `./grist-data/test` | `TEST_GRIST_API_KEY`, `TEST_GRIST_DOC_ID` | Testing, experiments |
| `production` | 8484 | `./grist-data/prod` | `PROD_GRIST_API_KEY`, `PROD_GRIST_DOC_ID` | Live data |

### Data Directory Structure

All environment data is organized under the `grist-data/` folder:

```
grist-data/
├── dev/          # Development environment data
│   └── ...
├── test/         # Test environment data (isolated)
│   └── ...
├── prod/         # Production environment data (live)
│   └── ...
└── backups/      # Backup archives (shared across environments)
    └── ...
```

**Key points:**
- Each environment has completely isolated data - switching environments means switching databases
- `dev` is the default for daily development work
- `test` is useful for testing imports or experiments without affecting real data
- `prod` should only be used for live production data
- Backups are stored in a shared `backups/` folder regardless of environment

### How Environment Variables Work

1. **`ENVIRONMENT`** sets the active environment (default: `dev`)
2. Scripts automatically load the correct config based on `ENVIRONMENT`
3. Each environment uses different Grist document IDs and API keys
4. Data is isolated in separate directories

**Example workflow:**
```bash
# .env file
ENVIRONMENT=dev
GRIST_API_KEY=key_for_dev_doc
TEST_GRIST_API_KEY=key_for_test_doc

# This uses dev config (GRIST_API_KEY)
uv run python csv_import_helper.py data.csv

# This uses test config (TEST_GRIST_API_KEY)  
uv run python csv_import_helper.py data.csv --env test
```

### Switching Environments

```bash
cd scripts

# Check current environment and container status
uv run python manage_env.py status

# Switch ENVIRONMENT in .env file
uv run python manage_env.py switch test

# Start containers for current environment
uv run python manage_env.py start

# Or start specific environment (ignores .env)
uv run python manage_env.py start test

# View logs
uv run python manage_env.py logs -f

# Stop environment
uv run python manage_env.py stop
```

### Using Different Environments in Scripts

All scripts support the `--env` flag to override the default:

```bash
# Import to test environment (uses TEST_GRIST_API_KEY)
uv run python csv_import_helper.py data.csv --env test

# Update prices in production (uses PROD_GRIST_API_KEY)
uv run python price_updater.py --env production

# Run transformation using current ENVIRONMENT
uv run python bronze_to_silver.py

# Override doc ID for one-time use
uv run python csv_import_helper.py data.csv --env test --doc-id special_doc
uv run python bronze_to_silver.py
```

### 8. Create Grist Tables

#### Option A: Automated Setup (Recommended)

Use the automation script to create all tables, columns, and formulas via the Grist API.

##### Prerequisites

1. Grist must be running (see Step 4 above)
2. You must have created a document in Grist and have the Doc ID
3. Your API key must be configured in `.env`

##### Step 1: Get Your Document ID and API Key

1. Open Grist at http://localhost:8484
2. Create a new document (or open existing one)
3. Copy the Doc ID from the URL: `http://localhost:8484/o/docs/doc/{DOC-ID}/...`
4. Get your API Key: Profile → API Keys → Create Key
5. Add to your `.env` file:
   ```bash
   GRIST_DOC_ID=your_doc_id_here
   GRIST_API_KEY=your_api_key_here
   ```

##### Step 2: Run the Automation Script

```bash
cd scripts

# Preview what will be created (dry run - no changes made)
uv run python setup_grist_tables.py --env dev --dry-run

# Create all tables, columns, and formulas
uv run python setup_grist_tables.py --env dev
```

**Expected output:**
```
INFO - Setting up Grist Tables - Medallion Architecture
INFO - 📋 Processing table: bronze_transactions
INFO - ✅ Created table 'bronze_transactions' with 30 columns
INFO - 📋 Processing table: silver_stocks
INFO - ✅ Created table 'silver_stocks' with 9 columns
...
INFO - Setup Summary
INFO - ✅ Created: bronze_transactions
INFO - ✅ Created: silver_stocks
...
INFO - ✨ Setup complete!
```

##### Step 3: Verify Tables Were Created

1. Open Grist at http://localhost:8484
2. Open your document
3. Check that all tables appear in the left sidebar:
   - `bronze_transactions`
   - `silver_stocks`
   - `silver_transactions`
   - `gold_positions`
   - `gold_stocks`
   - `gold_monthly_archive`

##### Step 4: Configure Table References

The automation script creates tables and formulas, but **table references must be configured manually**:

| Column | Should Reference |
|--------|------------------|
| `silver_transactions.Symbol` | `silver_stocks.Symbol` |
| `gold_positions.Symbol` | `silver_stocks.Symbol` |
| `gold_stocks.Symbol` | `silver_stocks.Symbol` |

**To set a reference:**
1. Open the table in Grist
2. Click the column header (e.g., "Symbol") → "Column Options"
3. Change "Column Type" to "Reference"
4. Set "Table" to `silver_stocks`
5. Set "Column" to `Symbol`
6. Click "Apply"

##### Troubleshooting

**"Table already exists" messages:**
- This is normal if you run the script multiple times
- The script skips existing tables (idempotent)

**API errors:**
- Check that Grist is running: `docker compose ps`
- Verify your API key and Doc ID in `.env`
- Try with explicit values: `uv run python setup_grist_tables.py --doc-id <id> --api-key <key>`

**Formulas not working:**
- Ensure table references are configured (Step 4 above)
- Check that referenced tables exist
- Formulas referencing other tables need references set up first

#### Option B: Manual Setup

Follow the detailed guide in `docs/03-grist-table-setup.md` to create tables manually:

**Tables to create:**
- `bronze_transactions` - Raw CSV imports
- `silver_stocks` - Stock master data  
- `silver_transactions` - Validated transactions
- `gold_stocks` - Portfolio summary
- `gold_positions` - Position calculations
- `gold_monthly_archive` - Historical snapshots

**Step 3: Add Formulas**

After creating tables, add these key formulas:

**`silver_transactions.Total_Fees`:**
```python
sum([$Platform_Fees or 0, $Tax or 0, $Settlement_Fees or 0, 
     $Trading_Fees or 0, $CAT_Fees or 0, $Commission or 0, 
     $Clearing_Fees or 0])
```

**`silver_transactions.Net_Amount`:**
```python
$Fill_Amount + $Total_Fees if $Side == "Buy" else $Fill_Amount - $Total_Fees
```

See `docs/03-grist-table-setup.md` for all formulas.

## Import Sample Data

### Import CSV to Bronze Layer

```bash
cd scripts

# Import sample Singapore stocks
uv run python csv_import_helper.py ../samples/sample-singapore-stocks.csv --source moomoo

# Import sample US stocks
uv run python csv_import_helper.py ../samples/sample-us-stocks.csv --source moomoo

# Import mixed portfolio
uv run python csv_import_helper.py ../samples/sample-mixed-portfolio.csv --source moomoo
```

### Transform Bronze to Silver

```bash
# Validate and transform bronze records to silver
uv run python bronze_to_silver.py

# With verbose output
uv run python bronze_to_silver.py --verbose

# Dry run (validate without inserting)
uv run python bronze_to_silver.py --dry-run
```

### Update Stock Prices

```bash
# Update prices using Yahoo Finance (default)
uv run python price_updater.py

# With specific provider
uv run python price_updater.py --provider yahoo

# Dry run
uv run python price_updater.py --dry-run

# Set API keys for other providers in .env:
# ALPHA_VANTAGE_API_KEY=your_key
# FINNHUB_API_KEY=your_key
```

### Create Monthly Archive

```bash
# Create month-end snapshot for current month
uv run python monthly_archiver.py

# Create snapshot for specific month
uv run python monthly_archiver.py --year 2024 --month 1

# Dry run
uv run python monthly_archiver.py --year 2024 --month 1 --dry-run
```

## Development Workflow

### Project Structure

```
grist-stock-tracker/
├── docker-compose.yml          # Container orchestration
├── .env                        # Environment variables
├── docs/                       # Documentation
├── samples/                    # Sample CSV files
├── scripts/                    # Python automation
│   ├── csv_import_helper.py    # CSV import to bronze
│   ├── bronze_to_silver.py     # Data transformation
│   ├── price_updater.py        # Price fetching
│   ├── monthly_archiver.py     # Month-end snapshots
│   ├── tests/                  # Test suite
│   └── .venv/                  # Virtual environment
├── grist-data/                 # Grist persistent data
│   ├── dev/                    # Development environment
│   ├── test/                   # Test environment
│   ├── prod/                   # Production environment
│   └── backups/                # Backup archives
```

### Adding Dependencies

```bash
cd scripts

# Add production dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update lock file
uv lock
```

### Running Tests

```bash
cd scripts

# Run all tests except UI
uv run pytest tests/ -v -m "not ui"

# Run with coverage
uv run pytest --cov=. --cov-report=term-missing

# Run UI tests (requires Grist running)
uv run pytest tests/ui/ -v -m ui

# Run UI tests headless
uv run pytest tests/ui/ -v -m ui --headless
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature dev

# Make changes and commit
uv run pytest tests/  # Ensure tests pass
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
# Create PR to merge into dev branch
```

## Troubleshooting

### Podman Issues

**Error: Cannot connect to Podman socket**
```bash
podman machine start
```

**Error: chown: Read-only file system**
- Already fixed in docker-compose.yml (removed `:ro` from volume mounts)

### Grist Issues

**First-time setup hangs**
```bash
# Restart container
docker compose restart grist

# Clear data and start fresh (WARNING: loses all data)
rm -rf grist-data/*
docker compose up -d grist
```

**API calls return 401 Unauthorized**
- Check API key in `.env` matches Grist UI
- Verify `GRIST_DOC_ID` matches your document ID from URL

### Python Issues

**Module not found errors**
```bash
cd scripts
uv sync  # Reinstall dependencies
```

**Tests failing**
```bash
# Check you're in scripts directory
cd scripts

# Run with verbose output
uv run pytest tests/ -v --tb=long
```

## Environment Variables

Create `.env` file in project root:

```bash
# Required
GRIST_API_KEY=your_api_key_here

# Document ID from Grist URL (e.g., abc123 from /doc/abc123/...)
GRIST_DOC_ID=your_doc_id

# Optional - Custom Grist URL
GRIST_URL=http://localhost:8484

# Optional - Price API Keys
ALPHA_VANTAGE_API_KEY=
FINNHUB_API_KEY=

# Optional - Grist credentials for UI testing
GRIST_EMAIL=admin@example.com
GRIST_PASSWORD=admin
```

## Backup and Restore

### Manual Backup

```bash
# Grist data is in grist-data/
cp -r grist-data backups/grist-backup-$(date +%Y%m%d)
```

### Automated Backups

Enable backup service in docker-compose.yml:

```bash
# Start with backup profile
docker compose --profile backup up -d

# Backups stored in ./backups
# Runs daily at 2 AM with 30-day retention
```

### Restore from Backup

```bash
# Stop Grist
docker compose stop grist

# Restore data
rm -rf grist-data/*
cp -r backups/grist-backup-YYYYMMDD/* grist-data/

# Restart
docker compose up -d grist
```

## Next Steps

1. Review `docs/01-project-spec.md` for detailed architecture
2. Check `AGENTS.md` for development guidelines
3. Import your actual brokerage CSV exports
4. Customize stock formulas in Grist as needed

## Support

- [Grist Documentation](https://support.getgrist.com/)
- [Project Issues](https://github.com/flowy0/grist-stock-tracker/issues)
