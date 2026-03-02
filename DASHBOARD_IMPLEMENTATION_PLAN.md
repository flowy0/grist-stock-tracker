# Stock Tracker Dashboard - Implementation Plan

## Dashboard Structure

### Page 1: "Portfolio Overview"
High-level portfolio summary with key metrics

**Widgets:**
1. **Summary Table** - Gold Positions (Symbol, Shares, Invested, Market Value, P/L, Return %)
2. **Pie Chart** - Portfolio Allocation by Market Value
3. **Bar Chart** - Unrealized P/L by Position
4. **Card** - Total Portfolio Summary (Total Value, Total P/L, Best/Worst performers)

### Page 2: "Stock Performance"
Individual stock analysis

**Widgets:**
1. **Table** - Gold Stocks (all metrics)
2. **Custom Widget** - Price History Chart
3. **Bar Chart** - Return % comparison
4. **Card** - Selected Stock Details

### Page 3: "Transaction History"
Historical transaction view

**Widgets:**
1. **Table** - Silver Transactions (filtered/sorted by date)
2. **Summary Table** - Transactions by Month
3. **Chart** - Buy/Sell activity over time

---

## Implementation Steps

### Phase 1: Native Charts (No Code)

1. Create new "Dashboard" page
2. Add Summary Table widget (Gold Positions)
3. Add Pie Chart for portfolio allocation
4. Add Bar Chart for P/L visualization
5. Configure widget linking

### Phase 2: Custom Price History Widget

1. Create HTML/JS widget with Plotly
2. Fetch historical price data from Yahoo Finance
3. Render interactive line chart
4. Host on GitHub Pages
5. Embed in Grist

### Phase 3: Advanced Features

1. Add calculated fields for dashboard metrics
2. Create summary tables for aggregations
3. Add conditional formatting for P/L colors
4. Configure auto-refresh workaround

---

## Widget Configuration Details

### Summary Table: Gold Positions
```
Widget: Table
Table: Gold_positions
Columns: Symbol.Symbol, Total_Shares, Total_Invested, Current_Market_Value, Unrealized_P_L, Return_Pct
```

### Pie Chart: Portfolio Allocation
```
Widget: Chart
Table: Gold_positions
Type: Pie Chart
Label: Symbol.Symbol
Values: Current_Market_Value
```

### Bar Chart: P/L by Position
```
Widget: Chart
Table: Gold_positions
Type: Bar Chart
X-Axis: Symbol.Symbol
Series: Unrealized_P_L
```

### Custom Widget: Price History
```
Widget: Custom
URL: https://your-github-pages-url/price-history.html
Table: Gold_stocks
```

---

## Technical Requirements

### For Custom Widget
```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <script src="https://docs.getgrist.com/grist-plugin-api.js"></script>
</head>
<body>
  <div id="chart"></div>
  <script>
    // Fetch data from Grist
    // Fetch historical prices from Yahoo Finance
    // Render with Plotly
  </script>
</body>
</html>
```

### Data Flow
```
Grist Gold_stocks table → Custom Widget → Yahoo Finance API → Plotly Chart
```

---

## Success Criteria

- [ ] Portfolio Overview page shows all positions with correct metrics
- [ ] Pie chart accurately reflects portfolio allocation
- [ ] Bar chart shows P/L with color coding (green/red)
- [ ] Clicking a position updates the price history widget
- [ ] All data updates when prices are refreshed
