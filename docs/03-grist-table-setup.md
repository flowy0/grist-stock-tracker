# Grist Table Setup Guide

This document describes how to set up the tables in Grist for the Stock Tracker application.

## Prerequisites

1. Grist running at http://localhost:8484 (or your configured URL)
2. Admin user created and logged in
3. A new document created for stock tracking

## Document Configuration

### Step 1: Create New Document

1. Open Grist at http://localhost:8484
2. Click "Create New Document"
3. Name it "Stock Tracker" (or your preferred name)
4. Note the document ID from the URL (e.g., `https://.../doc/<doc-id>`)

### Step 2: Configure Document Settings

1. Click the wrench icon (⚙️) in the left sidebar
2. Go to "Document Settings"
3. Set:
   - **Default Timezone**: Your local timezone (e.g., `Asia/Singapore`)
   - **Default Currency**: `USD` (or your preferred default)
   - **Default Locale**: `en-US` (or your preferred locale)
4. Click "Save"

---

## Table 1: bronze_transactions (Bronze Layer)

### Create Table

1. Click the `+` icon next to "Tables" in the left sidebar
2. Select "Add Table"
3. Name it: `bronze_transactions`

### Configure Columns

Delete the default columns (A, B, C) and add these:

| Column Label | Column ID | Type | Options |
|--------------|-----------|------|---------|
| Import ID | `Import_ID` | Text | Primary key |
| Import Date | `Import_Date` | DateTime | |
| Source File | `Source_File` | Text | |
| Raw Data | `Raw_Data` | Text | Long text for JSON storage |
| Side | `Side` | Text | |
| Symbol | `Symbol` | Text | Uppercase ticker |
| Name | `Name` | Text | Company name |
| Order Price | `Order_Price` | Numeric | |
| Order Qty | `Order_Qty` | Numeric | |
| Order Amount | `Order_Amount` | Numeric | |
| Status | `Status` | Text | |
| Filled Avg Price | `Filled_Avg_Price` | Text | Store as text (e.g., "100@2.91") |
| Order Time | `Order_Time` | DateTime | |
| Order Type | `Order_Type` | Text | |
| Time in Force | `Time_in_Force` | Text | |
| Fill Qty | `Fill_Qty` | Numeric | |
| Fill Price | `Fill_Price` | Numeric | |
| Fill Amount | `Fill_Amount` | Numeric | |
| Fill Time | `Fill_Time` | DateTime | |
| Markets | `Markets` | Text | SG/US/HK/UK |
| Currency | `Currency` | Text | SGD/USD/HKD/GBP |
| Platform Fees | `Platform_Fees` | Numeric | |
| Tax | `Tax` | Numeric | Consumption tax |
| Settlement Fees | `Settlement_Fees` | Numeric | |
| Trading Fees | `Trading_Fees` | Numeric | |
| CAT Fees | `CAT_Fees` | Numeric | Consolidated Audit Trail Fees |
| Commission | `Commission` | Numeric | |
| Clearing Fees | `Clearing_Fees` | Numeric | |
| Platform | `Platform` | Text | Broker name (e.g., moomoo) |
| Validation Status | `Validation_Status` | Choice | Choices: Valid, Invalid, Pending |
| Validation Errors | `Validation_Errors` | Text | Error messages |

### How to Add Columns

1. Click the column header → "Column Options"
2. In the right panel, set:
   - **Column Label**: Display name (can have spaces)
   - **Column ID**: Click 🔗 icon to set (snake_case, no spaces)
   - **Column Type**: Select from dropdown
3. For Choice type, click "Edit" to add choices

---

## Table 2: silver_stocks (Silver Layer)

### Create Table

1. Click `+` → "Add Table"
2. Name: `silver_stocks`

### Configure Columns

| Column Label | Column ID | Type | Options |
|--------------|-----------|------|---------|
| Symbol | `Symbol` | Text | Primary key, uppercase |
| Name | `Name` | Text | Company name |
| Market | `Market` | Choice | Choices: SG, US, HK, UK |
| Currency | `Currency` | Choice | Choices: SGD, USD, HKD, GBP |
| Asset Type | `Asset_Type` | Choice | Choices: Stock, ETF, REIT, Bond |
| Current Price | `Current_Price` | Numeric | |
| Price Updated | `Price_Updated` | DateTime | |
| Price Source | `Price_Source` | Text | e.g., Yahoo, AlphaVantage |
| Is Active | `Is_Active` | Toggle | |

---

## Table 3: silver_transactions (Silver Layer)

### Create Table

1. Click `+` → "Add Table"
2. Name: `silver_transactions`

### Configure Columns

| Column Label | Column ID | Type | Options |
|--------------|-----------|------|---------|
| Transaction ID | `Transaction_ID` | Text | Primary key (UUID) |
| Bronze Ref | `Bronze_Ref` | Reference | Reference → bronze_transactions |
| Date | `Date` | DateTime | |
| Side | `Side` | Choice | Choices: Buy, Sell, Dividend |
| Symbol | `Symbol` | Reference | Reference → silver_stocks |
| Fill Qty | `Fill_Qty` | Numeric | |
| Fill Price | `Fill_Price` | Numeric | Currency format |
| Fill Amount | `Fill_Amount` | Numeric | Currency format |
| Platform Fees | `Platform_Fees` | Numeric | Currency format |
| Tax | `Tax` | Numeric | Currency format |
| Settlement Fees | `Settlement_Fees` | Numeric | Currency format |
| Trading Fees | `Trading_Fees` | Numeric | Currency format |
| CAT Fees | `CAT_Fees` | Numeric | Currency format |
| Commission | `Commission` | Numeric | Currency format |
| Clearing Fees | `Clearing_Fees` | Numeric | Currency format |
| Total Fees | `Total_Fees` | Formula | See formula below |
| Net Amount | `Net_Amount` | Formula | See formula below |
| Platform | `Platform` | Text | |
| Notes | `Notes` | Text | |

### Formulas for silver_transactions

**Total_Fees**:
```python
sum([$Platform_Fees or 0, $Tax or 0, $Settlement_Fees or 0, 
     $Trading_Fees or 0, $CAT_Fees or 0, $Commission or 0, 
     $Clearing_Fees or 0])
```

**Net_Amount**:
```python
$Fill_Amount + $Total_Fees if $Side == "Buy" else $Fill_Amount - $Total_Fees
```

To add a formula:
1. Add column, set type to "Formula"
2. Enter the formula in the formula box
3. Click "Apply"

---

## Table 4: gold_positions (Gold Layer)

### Create Table

1. Click `+` → "Add Table"
2. Name: `gold_positions`

### Configure Columns

| Column Label | Column ID | Type | Options |
|--------------|-----------|------|---------|
| Position ID | `Position_ID` | Text | Primary key |
| Symbol | `Symbol` | Reference | Reference → silver_stocks |
| Total Shares | `Total_Shares` | Formula | See formula below |
| Total Invested | `Total_Invested` | Formula | See formula below |
| Avg Cost Basis | `Avg_Cost_Basis` | Formula | See formula below |
| Current Market Value | `Current_Market_Value` | Formula | See formula below |
| Unrealized P/L | `Unrealized_P_L` | Formula | See formula below |
| Realized P/L | `Realized_P_L` | Formula | See formula below |
| Return % | `Return_Pct` | Formula | See formula below |
| Days Held | `Days_Held` | Formula | See formula below |

### Formulas for gold_positions

**Total_Shares**:
```python
import itertools
txns = silver_transactions.lookupRecords(Symbol=$Symbol)
return sum(t.Fill_Qty if t.Side=="Buy" else -t.Fill_Qty for t in txns if t.Side!="Dividend")
```

**Total_Invested**:
```python
txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side="Buy")
return sum(t.Net_Amount for t in txns)
```

**Avg_Cost_Basis**:
```python
$Total_Invested / $Total_Shares if $Total_Shares > 0 else 0
```

**Current_Market_Value**:
```python
$Total_Shares * $Symbol.Current_Price if $Total_Shares > 0 else 0
```

**Unrealized_P_L**:
```python
$Current_Market_Value - $Total_Invested if $Total_Shares > 0 else 0
```

**Realized_P_L**:
```python
txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side="Sell")
cost_basis = $Avg_Cost_Basis
return sum(t.Fill_Amount - (t.Fill_Qty * cost_basis) for t in txns)
```

**Return_Pct**:
```python
($Unrealized_P_L + $Realized_P_L) / $Total_Invested * 100 if $Total_Invested > 0 else 0
```

**Days_Held**:
```python
import datetime
txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side="Buy")
if len(txns) > 0:
    first_date = min(t.Date for t in txns if t.Date)
    return (datetime.datetime.now() - first_date).days
return 0
```

---

## Table 5: gold_stocks (Gold Layer)

### Create Table

1. Click `+` → "Add Table"
2. Name: `gold_stocks`

### Configure Columns

| Column Label | Column ID | Type | Options |
|--------------|-----------|------|---------|
| Symbol | `Symbol` | Reference | Reference → silver_stocks |
| Name | `Name` | Formula | `=$Symbol.Name` |
| Market | `Market` | Formula | `=$Symbol.Market` |
| Currency | `Currency` | Formula | `=$Symbol.Currency` |
| Asset Type | `Asset_Type` | Formula | `=$Symbol.Asset_Type` |
| Current Price | `Current_Price` | Formula | `=$Symbol.Current_Price` |
| Total Shares | `Total_Shares` | Formula | Lookup from gold_positions |
| Total Invested | `Total_Invested` | Formula | Lookup from gold_positions |
| Avg Cost Basis | `Avg_Cost_Basis` | Formula | Lookup from gold_positions |
| Current Market Value | `Current_Market_Value` | Formula | Lookup from gold_positions |
| Unrealized P/L | `Unrealized_P_L` | Formula | Lookup from gold_positions |
| Realized P/L | `Realized_P_L` | Formula | Lookup from gold_positions |
| Total Return % | `Total_Return_Pct` | Formula | See below |
| Last Transaction Date | `Last_Transaction_Date` | Formula | See below |

### Formulas for gold_stocks

**Total_Return_Pct**:
```python
($Unrealized_P_L + $Realized_P_L) / $Total_Invested * 100 if $Total_Invested > 0 else 0
```

**Last_Transaction_Date**:
```python
txns = silver_transactions.lookupRecords(Symbol=$Symbol)
if len(txns) > 0:
    return max(t.Date for t in txns if t.Date)
return None
```

---

## Table 6: gold_monthly_archive (Gold Layer)

### Create Table

1. Click `+` → "Add Table"
2. Name: `gold_monthly_archive`

### Configure Columns

| Column Label | Column ID | Type | Options |
|--------------|-----------|------|---------|
| Archive ID | `Archive_ID` | Text | Primary key |
| Month | `Month` | Date | Month-end date |
| Symbol | `Symbol` | Reference | Reference → silver_stocks |
| Shares Held | `Shares_Held` | Numeric | |
| Avg Cost | `Avg_Cost` | Currency | |
| Month End Price | `Month_End_Price` | Currency | |
| Market Value | `Market_Value` | Currency | |
| Unrealized P/L | `Unrealized_PL` | Currency | |
| Realized P/L (Month) | `Realized_PL_Month` | Currency | |
| Total Return % | `Total_Return_Pct` | Numeric | |
| Snapshot Taken | `Snapshot_Taken` | DateTime | |

---

## Next Steps

After setting up all tables:

1. **Generate API Key**:
   - Click your profile picture → "API Keys"
   - Click "Create API Key"
   - Copy the key and save it

2. **Get Document ID**:
   - Look at the URL: `https://.../doc/<doc-id>`
   - The `<doc-id>` part is your document ID

3. **Configure Environment**:
   ```bash
   cd scripts
   cp .env.example .env
   # Edit .env with your doc ID and API key
   ```

4. **Test Import**:
   ```bash
   uv run python csv_import_helper.py ../samples/sample-minimal-test.csv --dry-run
   ```

---

## Troubleshooting

### "Table not found" error
- Check the table name matches exactly (case-sensitive)
- Ensure you're using the Column ID, not Column Label, in API calls

### Formula errors
- Check that referenced tables exist
- Verify column IDs are correct
- Use `$ColumnName` format to reference columns

### Date parsing issues
- Ensure DateTime columns use ISO format
- Grist stores dates internally; display format is configurable
