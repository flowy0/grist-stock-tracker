# Grist Stock Tracker - Project Specification

## Overview
Self-hosted stock portfolio tracking application using Grist (spreadsheet-database hybrid)

## Core Features
1. Import broker CSV transactions (moomoo format)
2. Track positions with real-time P/L calculations
3. Live stock price updates via API
4. Monthly position archiving
5. Automated backups

## Tech Stack
- Grist (self-hosted via Docker)
- Python 3.9+ (data processing)
- Docker Compose (orchestration)

## Data Structure

### Table: Stocks
- Symbol (Text, Primary)
- Name (Text)
- Market (Choice: SG/US/HK/UK)
- Currency (Choice: SGD/USD/HKD/GBP)
- Asset_Type (Choice: Stock/ETF/REIT/Bond)
- Current_Price (Numeric)
- Price_Updated (DateTime)

### Table: Transactions
- Date (DateTime)
- Side (Choice: Buy/Sell/Dividend)
- Symbol (Reference → Stocks)
- Fill_Qty (Numeric)
- Fill_Price (Currency)
- Fill_Amount (Currency)
- Platform_Fees, Tax, Settlement_Fees, Trading_Fees, CAT_Fees, Commission, Clearing_Fees (Currency)
- Total_Fees (Formula: sum of all fees)
- Net_Amount (Formula: Buy=+fees, Sell=-fees)
- Platform (Text)

### Table: Positions (Calculated)
- Symbol (Reference → Stocks)
- Total_Shares (Formula)
- Total_Invested (Formula)
- Avg_Cost_Basis (Formula)
- Current_Market_Value (Formula)
- Unrealized_P_L (Formula)
- Realized_P_L (Formula)

### Table: Monthly_Archive
- Month (Date)
- Symbol (Reference)
- Shares_Held, Avg_Cost, Month_End_Price
- Market_Value, Unrealized_PL, Realized_PL

## Key Formulas

Total_Fees:
```python
sum([$Platform_Fees or 0, $Tax or 0, $Settlement_Fees or 0, 
     $Trading_Fees or 0, $CAT_Fees or 0, $Commission or 0, $Clearing_Fees or 0])

Net_Amount:

`$Fill_Amount + $Total_Fees if $Side == "Buy" else $Fill_Amount - $Total_Fees`

Total_Shares:

```
import itertools
txns = Transactions.lookupRecords(Symbol=$Symbol)
return sum(t.Fill_Qty if t.Side=="Buy" else -t.Fill_Qty for t in txns)
```

Avg_Cost_Basis:

`$Total_Invested / $Total_Shares if $Total_Shares > 0 else 0`

Unrealized_P_L:

`$Current_Market_Value - ($Total_Shares * $Avg_Cost_Basis) if $Total_Shares > 0 else 0`