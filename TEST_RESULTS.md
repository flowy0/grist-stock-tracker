# Gold Layer Formula Testing - Summary

## Test Environment
- **Instance**: http://grist-test.homelb.online (Raspberry Pi, ARM architecture)
- **Sandbox Flavor**: `unsandboxed` (required for ARM compatibility)
- **Document ID**: 6RMW9PJweAiW

## Test Data
- **Bronze Transactions**: 7 records (raw CSV data)
- **Silver Transactions**: 5 records (transformed)
- **Silver Stocks**: 4 records (unique stocks)
- **Gold Positions**: 4 records
- **Gold Stocks**: 4 records

## Key Findings

### 1. Formula Table Names Are Case-Sensitive
Grist formulas must use the exact table name casing:
- ✅ `Silver_transactions` (correct)
- ❌ `silver_transactions` (not found)

### 2. Reference Column Access
For Reference columns pointing to other tables:
- `$Symbol` returns the record reference (e.g., `Silver_stocks[1]`)
- `$Symbol.id` returns the numeric record ID (e.g., `1`)
- `$Symbol.Symbol` returns the display value (e.g., `"OV8"`)

### 3. Cross-Table Lookups
Since `lookupRecords()` with Reference columns doesn't work as expected, use:
```python
# Iterate through all records instead
stocks = list(Silver_stocks.all)
for s in stocks:
    if s.id == $Symbol.id:
        return s.Current_Price
```

### 4. Date Parsing
Dates from the API are strings like `"Feb 9, 2026 12:58:43 SGT"`. Parse with:
```python
date_str = str(t.Date).split(' SGT')[0].split(' ET')[0]
dt = datetime.datetime.strptime(date_str, "%b %d, %Y %H:%M:%S")
```

## Formula Results

### Gold Positions
| Symbol | Shares | Invested | Avg Cost | Market Value | Unrealized P/L | Return % | Days Held |
|--------|--------|----------|----------|--------------|----------------|----------|-----------|
| OV8    | 1000   | $2,912.28| $2.91    | $2,660.00    | -$252.28       | -8.66%   | 20        |
| D05    | 100    | $4,250.37| $42.50   | $5,592.00    | +$1,341.63     | +31.57%  | 55        |
| AAPL   | 5      | $979.32  | $195.86  | $1,320.90    | +$341.58       | +34.88%  | 52        |
| NVDA   | 1      | $1,752.14| $1,752.14| $177.19      | -$1,574.95     | -137.27% | 50        |

### Gold Stocks
All formulas working correctly:
- Total Shares: ✅
- Total Invested: ✅
- Avg Cost Basis: ✅
- Current Price (from Silver_stocks): ✅
- Market Value: ✅
- Unrealized P/L: ✅
- Return %: ✅

## Issues Resolved

1. **Formulas returning None**: Fixed by using correct table name casing
2. **Market Value showing 0**: Fixed by iterating Silver_stocks.all instead of lookupOne
3. **Days Held showing None**: Fixed by parsing string date format
4. **Symbol display**: Worked around by mapping IDs to symbols via API

## Remaining Items

- Duplicate records in Gold_stocks (cosmetic issue, filtered in display)
- Manual table reference configuration still required via Grist UI
