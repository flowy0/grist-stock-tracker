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
| `AGENTS.md` | Complete technical guide for development |
| `docs/implementation-todo.md` | Step-by-step implementation checklist |
| `docs/sample-files-readme.md` | Documentation for sample CSV files |
| `docs/01-project-spec.md` | Detailed project specification |

## Sample Data

Test files are provided in the `samples/` folder:
- `sample-minimal-test.csv` - Quick validation (7 transactions)
- `sample-singapore-stocks.csv` - Singapore market data (14 transactions)
- `sample-us-stocks.csv` - US market data (17 transactions)
- `sample-mixed-portfolio.csv` - Realistic portfolio (22 transactions)

## Quick Start

### Prerequisites

- Podman (with docker alias) or Docker installed
- Podman Compose or Docker Compose
- 2GB RAM minimum, 4GB recommended

### 1. Clone and Configure

```bash
cd grist-stock-tracker
cp docker/.env.example docker/.env
# Edit docker/.env with your settings