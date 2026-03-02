# Grist Stock Tracker - Implementation Todo

This document outlines the implementation tasks for the Grist Stock Tracker project.

## Phase 1: Infrastructure & Setup

### Podman Environment
- [ ] Create `.env` from `.env.example` with secure secrets
- [ ] Test `docker compose --profile grist up -d` basic startup (using podman via alias)
- [ ] Test with PostgreSQL profile: `docker compose --profile postgres up -d`
- [ ] Verify Grist accessible at http://localhost:8484
- [ ] Document first-time Grist setup (admin user creation)

> **Note:** This project uses **Podman** as the container runtime with `docker=podman` alias. All `docker` commands execute via Podman.

### Grist Initial Configuration
- [ ] Create Grist document for stock tracking
- [ ] Configure basic document settings (timezone, currency, locale)
- [ ] Set up document permissions

---

## Phase 2: Data Model Implementation (Bronze Layer)

### bronze_transactions Table
- [ ] Create table `bronze_transactions` in Grist
- [ ] Configure all columns with proper IDs and Labels
- [ ] Set column types:
  - [ ] `Import_ID` - Text (Primary)
  - [ ] `Import_Date` - DateTime
  - [ ] `Source_File` - Text
  - [ ] `Raw_Data` - Text
  - [ ] `Side` - Text
  - [ ] `Symbol` - Text
  - [ ] `Name` - Text
  - [ ] `Order_Price`, `Order_Qty`, `Order_Amount` - Numeric
  - [ ] `Status` - Text
  - [ ] `Filled_Avg_Price` - Text
  - [ ] `Order_Time`, `Fill_Time` - DateTime
  - [ ] `Order_Type`, `Time_in_Force` - Text
  - [ ] `Markets` - Text
  - [ ] `Currency` - Text
  - [ ] All fee columns - Numeric
  - [ ] `Validation_Status` - Choice (Valid/Invalid/Pending)
  - [ ] `Validation_Errors` - Text
- [ ] Test manual import of `samples/sample-minimal-test.csv`

### Bronze Import Script (Python)
- [ ] Create `scripts/csv_import_helper.py`
- [ ] Implement CSV file reading
- [ ] Implement row-by-row insertion to bronze_transactions
- [ ] Add UUID generation for `Import_ID`
- [ ] Add timestamp for `Import_Date`
- [ ] Store raw CSV row in `Raw_Data` column
- [ ] Handle different date formats (SGT, ET)
- [ ] Add command-line interface (argparse)
- [ ] Test import with all sample files

---

## Phase 3: Data Model Implementation (Silver Layer)

### silver_stocks Table
- [ ] Create table `silver_stocks` in Grist
- [ ] Configure columns:
  - [ ] `Symbol` - Text (Primary)
  - [ ] `Name` - Text
  - [ ] `Market` - Choice (SG/US/HK/UK)
  - [ ] `Currency` - Choice (SGD/USD/HKD/GBP)
  - [ ] `Asset_Type` - Choice (Stock/ETF/REIT/Bond)
  - [ ] `Current_Price` - Numeric
  - [ ] `Price_Updated` - DateTime
  - [ ] `Price_Source` - Text
  - [ ] `Is_Active` - Toggle
- [ ] Add sample stock data from test files

### silver_transactions Table
- [ ] Create table `silver_transactions` in Grist
- [ ] Configure columns:
  - [ ] `Transaction_ID` - Text (Primary)
  - [ ] `Bronze_Ref` - Reference → bronze_transactions
  - [ ] `Date` - DateTime
  - [ ] `Side` - Choice (Buy/Sell/Dividend)
  - [ ] `Symbol` - Reference → silver_stocks
  - [ ] `Fill_Qty`, `Fill_Price`, `Fill_Amount` - Numeric/Currency
  - [ ] All fee columns - Currency
  - [ ] `Total_Fees` - Formula
  - [ ] `Net_Amount` - Formula
  - [ ] `Platform` - Text
  - [ ] `Notes` - Text
- [ ] Implement formulas:
  ```python
  # Total_Fees
  sum([$Platform_Fees or 0, $Tax or 0, $Settlement_Fees or 0, 
       $Trading_Fees or 0, $CAT_Fees or 0, $Commission or 0, 
       $Clearing_Fees or 0])
  
  # Net_Amount
  $Fill_Amount + $Total_Fees if $Side == "Buy" else $Fill_Amount - $Total_Fees
  ```

### Bronze to Silver Transformation Script
- [ ] Extend `scripts/csv_import_helper.py` with validation logic
- [ ] Implement validation rules:
  - [ ] Check for duplicate transactions
  - [ ] Validate required fields (Symbol, Side, Fill_Qty, Fill_Price)
  - [ ] Validate numeric fields are positive
  - [ ] Check for existing symbols in silver_stocks
- [ ] Implement transformation:
  - [ ] Generate `Transaction_ID` (UUID or sequential)
  - [ ] Link to `Bronze_Ref`
  - [ ] Parse and normalize dates
  - [ ] Create new stock entries in silver_stocks if needed
  - [ ] Insert validated records into silver_transactions
- [ ] Update `bronze_transactions.Validation_Status` after processing

---

## Phase 4: Data Model Implementation (Gold Layer)

### gold_stocks Table
- [ ] Create table `gold_stocks` in Grist
- [ ] Configure columns:
  - [ ] `Symbol` - Reference → silver_stocks
  - [ ] `Name`, `Market`, `Currency`, `Asset_Type`, `Current_Price` - Formula (lookup from Silver)
  - [ ] `Total_Shares` - Formula
  - [ ] `Total_Invested` - Formula
  - [ ] `Avg_Cost_Basis` - Formula
  - [ ] `Current_Market_Value` - Formula
  - [ ] `Unrealized_P_L` - Formula
  - [ ] `Realized_P_L` - Formula
  - [ ] `Total_Return_Pct` - Formula
  - [ ] `Last_Transaction_Date` - Formula
- [ ] Implement formulas

### gold_positions Table
- [ ] Create table `gold_positions` in Grist
- [ ] Configure columns:
  - [ ] `Position_ID` - Text (Primary)
  - [ ] `Symbol` - Reference → silver_stocks
  - [ ] `Total_Shares` - Formula
  - [ ] `Total_Invested` - Formula
  - [ ] `Avg_Cost_Basis` - Formula
  - [ ] `Current_Market_Value` - Formula
  - [ ] `Unrealized_P_L` - Formula
  - [ ] `Realized_P_L` - Formula
  - [ ] `Return_Pct` - Formula
  - [ ] `Days_Held` - Formula
- [ ] Implement formulas:
  ```python
  # Total_Shares
  txns = silver_transactions.lookupRecords(Symbol=$Symbol)
  return sum(t.Fill_Qty if t.Side=="Buy" else -t.Fill_Qty for t in txns if t.Side!="Dividend")
  
  # Total_Invested
  txns = silver_transactions.lookupRecords(Symbol=$Symbol, Side="Buy")
  return sum(t.Net_Amount for t in txns)
  
  # Avg_Cost_Basis
  $Total_Invested / $Total_Shares if $Total_Shares > 0 else 0
  
  # Current_Market_Value
  $Total_Shares * $Symbol.Current_Price if $Total_Shares > 0 else 0
  
  # Unrealized_P_L
  $Current_Market_Value - $Total_Invested if $Total_Shares > 0 else 0
  ```

### gold_monthly_archive Table
- [ ] Create table `gold_monthly_archive` in Grist
- [ ] Configure columns:
  - [ ] `Archive_ID` - Text (Primary)
  - [ ] `Month` - Date
  - [ ] `Symbol` - Reference → silver_stocks
  - [ ] `Shares_Held` - Numeric
  - [ ] `Avg_Cost` - Currency
  - [ ] `Month_End_Price` - Currency
  - [ ] `Market_Value` - Currency
  - [ ] `Unrealized_PL` - Currency
  - [ ] `Realized_PL_Month` - Currency
  - [ ] `Total_Return_Pct` - Numeric
  - [ ] `Snapshot_Taken` - DateTime

---

## Phase 5: Price Update Automation

### Price Fetching Script
- [ ] Create `scripts/price_updater.py`
- [ ] Implement price fetching from Yahoo Finance (free, no API key)
- [ ] Implement Alpha Vantage fallback (requires API key)
- [ ] Implement Finnhub fallback (requires API key)
- [ ] Support SG, US, HK, UK markets
- [ ] Handle rate limiting and errors
- [ ] Update `silver_stocks.Current_Price` and `Price_Updated`
- [ ] Add command-line interface
- [ ] Add cron/scheduler documentation

---

## Phase 6: Monthly Archiving

### Monthly Archive Script
- [ ] Create `scripts/monthly_archiver.py`
- [ ] Query all active positions from gold_positions
- [ ] Calculate month-end metrics for each position
- [ ] Calculate realized P/L for the month
- [ ] Insert records into gold_monthly_archive
- [ ] Prevent duplicate archives for same month
- [ ] Add command-line interface
- [ ] Add cron/scheduler documentation

---

## Phase 7: Testing & Validation

### Unit Tests
- [ ] Create `scripts/tests/test_csv_import.py`
- [ ] Create `scripts/tests/test_price_updater.py`
- [ ] Create `scripts/tests/test_calculations.py`

### Integration Tests
- [ ] Test full Bronze → Silver → Gold pipeline
- [ ] Verify formula calculations are correct
- [ ] Test with all sample files
- [ ] Test edge cases:
  - [ ] Partial sells
  - [ ] Multiple buys at different prices
  - [ ] Dividend-only stocks
  - [ ] Closed positions (0 shares)

### Data Quality Checks
- [ ] Verify Silver totals match Bronze source
- [ ] Verify Gold position calculations match transaction history
- [ ] Verify unrealized P/L calculations
- [ ] Verify realized P/L calculations after sells

---

## Phase 8: Documentation & Deployment

### Documentation
- [ ] Update `README.md` with setup instructions
- [ ] Document Grist table setup process
- [ ] Document formula implementations
- [ ] Document script usage
- [ ] Document backup/restore procedures

### Production Deployment
- [ ] Production checklist review
- [ ] Secure secrets configuration
- [ ] S3 backup configuration (optional)
- [ ] Reverse proxy setup (optional)
- [ ] SSL/TLS configuration (optional)

---

## Quick Reference: Column Naming

When creating tables in Grist, use this naming convention:

| Display Label | Column ID |
|---------------|-----------|
| `Import ID` | `Import_ID` |
| `Import Date` | `Import_Date` |
| `Source File` | `Source_File` |
| `Raw Data` | `Raw_Data` |
| `Transaction ID` | `Transaction_ID` |
| `Bronze Ref` | `Bronze_Ref` |
| `Fill Qty` | `Fill_Qty` |
| `Fill Price` | `Fill_Price` |
| `Fill Amount` | `Fill_Amount` |
| `Order Time` | `Order_Time` |
| `Fill Time` | `Fill_Time` |
| `Platform Fees` | `Platform_Fees` |
| `Settlement Fees` | `Settlement_Fees` |
| `Trading Fees` | `Trading_Fees` |
| `CAT Fees` | `CAT_Fees` |
| `Clearing Fees` | `Clearing_Fees` |
| `Total Fees` | `Total_Fees` |
| `Net Amount` | `Net_Amount` |
| `Current Price` | `Current_Price` |
| `Price Updated` | `Price_Updated` |
| `Price Source` | `Price_Source` |
| `Is Active` | `Is_Active` |
| `Asset Type` | `Asset_Type` |
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
| `Snapshot Taken` | `Snapshot_Taken` |

---

## Implementation Order Recommendation

1. **Start with Phase 1** - Get Docker and Grist running
2. **Create bronze_transactions manually** in Grist, test CSV import via UI
3. **Build Bronze import script** to automate raw data ingestion
4. **Create Silver tables** one by one, starting with silver_stocks
5. **Build Silver transformation logic** - this is the core validation layer
6. **Create Gold tables** with formulas
7. **Test end-to-end** with sample files
8. **Add price updater** for live prices
9. **Add monthly archiver** for historical tracking
10. **Document everything**

---

## Notes

- Grist formula sandbox uses Python with restrictions
- Formula column IDs must be valid Python identifiers (snake_case)
- Column Labels can have spaces and are user-facing
- Use Reference columns to link tables (e.g., Bronze_Ref, Symbol)
- Bronze layer is immutable - never delete or modify after import
- Validation errors go in Bronze.Validation_Errors, not Silver
