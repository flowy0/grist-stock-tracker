# Grist Stock Tracker

A self-hosted stock portfolio tracking application built on Grist, featuring spreadsheet-like data entry, automated P/L calculations, live price updates, and monthly archiving.

## Features

- 📊 **Spreadsheet Interface**: Familiar row/column editing with database power
- 📈 **Live Price Updates**: Automated price fetching from Yahoo Finance, Alpha Vantage, or Finnhub
- 💰 **P/L Tracking**: Realized and unrealized gains/losses with cost basis calculations
- 📅 **Monthly Archiving**: Snapshot positions at month-end for historical tracking
- 📁 **CSV Import**: Transform and import broker transaction exports (moomoo format supported)
- 🔒 **Self-Hosted**: Complete data privacy and ownership
- 🐳 **Podman-Based**: Easy deployment with Podman Compose (Docker-compatible)
- 🏗️ **Medallion Architecture**: Bronze (raw) → Silver (cleaned) → Gold (aggregated) data layers

## Documentation

| Document | Description |
|----------|-------------|
| `docs/02-setup.md` | **Complete setup guide** - Start here! |
| `AGENTS.md` | Complete technical guide for development |
| `docs/03-grist-table-setup.md` | Step-by-step Grist table creation |
| `docs/05-sample-files-readme.md` | Documentation for sample CSV files |
| `docs/01-project-spec.md` | Detailed project specification |
| `.kimi/README.md` | Kimi Code agent configuration guide |

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/flowy0/grist-stock-tracker.git
cd grist-stock-tracker

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Start Podman (macOS)
podman machine start

# 4. Start Grist
docker-compose up -d grist

# 5. Setup Python environment
cd scripts && uv sync

# 6. Run tests
uv run pytest tests/ -v -m "not ui"
```

**Full setup instructions**: See [`docs/02-setup.md`](docs/02-setup.md)

## Development with Kimi Code

This project includes a custom Kimi Code agent configuration:

```bash
# Start Kimi with the project-specific developer agent
kimi --agent-file .kimi/agent.yaml
```

### Available Subagents

- **reviewer** - Python code review specialist
- **tester** - Test generation specialist  
- **git** - Git workflow specialist (branch/PR management)

See `.kimi/README.md` for detailed configuration.

## Project Structure

```
grist-stock-tracker/
├── docker-compose.yml     # Container orchestration
├── docs/                  # Documentation
│   ├── 02-setup.md          # Complete setup guide
├── scripts/              # Python automation
│   ├── csv_import_helper.py
│   ├── bronze_to_silver.py
│   ├── price_updater.py
│   ├── monthly_archiver.py
│   └── tests/
├── samples/              # Sample CSV files
├── grist-data/           # Grist persistent data
└── backups/              # Backup storage
```

## Sample Data

Test files provided in `samples/`:
- `sample-minimal-test.csv` - Quick validation (7 transactions)
- `sample-singapore-stocks.csv` - Singapore market data (14 transactions)
- `sample-us-stocks.csv` - US market data (17 transactions)
- `sample-mixed-portfolio.csv` - Realistic portfolio (22 transactions)

## License

MIT License - See repository for details.
