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

# Edit .env with your settings
# Set your environment: development | test | production
ENVIRONMENT=development

# For development (default on port 8484)
GRIST_API_KEY=your_api_key
GRIST_DOC_ID=your_doc_id

# For test environment (port 8485)
TEST_GRIST_API_KEY=your_test_api_key
TEST_GRIST_DOC_ID=your_test_doc_id

# For production environment (port 8484)
PROD_GRIST_API_KEY=your_prod_api_key
PROD_GRIST_DOC_ID=your_prod_doc_id
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
docker-compose up -d grist

# Check logs
docker-compose logs -f grist
```

Grist will be available at: http://localhost:8484

### 5. Configure Grist (First Run)

1. Open http://localhost:8484
2. Complete initial setup (create admin user)
3. Create a new document called "Stock Tracker"
4. Generate API key: Profile → Settings → API Key
5. Add API key to `.env`:
   ```bash
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

The project supports three isolated environments:

| Environment | Port | Data Directory | Use Case |
|-------------|------|----------------|----------|
| `development` | 8484 | `./grist-data` | Daily development |
| `test` | 8485 | `./grist-data-test` | Testing, experiments |
| `production` | 8484 | `./grist-data-prod` | Live data |

### Switching Environments

```bash
cd scripts

# Check current environment
uv run python manage_env.py status

# Switch to test environment
uv run python manage_env.py switch test

# Start test environment (different port)
uv run python manage_env.py start test

# Switch back to development
uv run python manage_env.py switch development
uv run python manage_env.py start
```

### Using Different Environments in Scripts

```bash
# Import to test environment
uv run python csv_import_helper.py data.csv --env test

# Update prices in production
uv run python price_updater.py --env production

# Run transformation in development (default)
uv run python bronze_to_silver.py
```

### 8. Create Grist Tables

Follow the table creation guide in `docs/03-grist-table-setup.md` to create:
- `bronze_transactions` - Raw CSV imports
- `silver_stocks` - Stock master data
- `silver_transactions` - Validated transactions
- `gold_stocks` - Portfolio summary
- `gold_positions` - Position calculations
- `gold_monthly_archive` - Historical snapshots

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
└── backups/                    # Backup storage
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
docker-compose restart grist

# Clear data and start fresh (WARNING: loses all data)
rm -rf grist-data/*
docker-compose up -d grist
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
docker-compose --profile backup up -d

# Backups stored in ./backups
# Runs daily at 2 AM with 30-day retention
```

### Restore from Backup

```bash
# Stop Grist
docker-compose stop grist

# Restore data
rm -rf grist-data/*
cp -r backups/grist-backup-YYYYMMDD/* grist-data/

# Restart
docker-compose up -d grist
```

## Next Steps

1. Review `docs/01-project-spec.md` for detailed architecture
2. Check `AGENTS.md` for development guidelines
3. Import your actual brokerage CSV exports
4. Customize stock formulas in Grist as needed

## Support

- [Grist Documentation](https://support.getgrist.com/)
- [Project Issues](https://github.com/flowy0/grist-stock-tracker/issues)
