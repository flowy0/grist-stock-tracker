# Stock Tracker Dashboard - Setup Instructions

## Overview

This guide walks you through setting up a complete dashboard for your stock tracker in Grist.

---

## Phase 1: Dashboard Setup in Grist UI

### Step 1: Access Your Grist Document

1. Open browser and go to: `http://grist-test.homelb.online/`
2. Open the "Tracker" document
3. You should see your tables: Bronze_transactions, Silver_stocks, Silver_transactions, Gold_positions, Gold_stocks

### Step 2: Create Dashboard Page

1. Click **"Add New"** button (top left)
2. Select **"Add Page"**
3. Name it **"Dashboard - Portfolio Overview"**

### Step 3: Add Summary Table Widget

1. On the new page, you'll see the widget picker
2. Select:
   - **Widget**: Table
   - **Table**: Gold_positions
   - Click **"Add to Page"**

3. Configure the table:
   - Click the **three-dots menu** on the widget → **"Widget options"**
   - In the right panel, under **"Visible Columns"**, keep only:
     - Symbol (the Reference column)
     - Total_Shares
     - Total_Invested
     - Current_Market_Value
     - Unrealized_P_L
     - Return_Pct
   - Hide all other columns
   - Click **"Save"** (green button at top of table)

4. Add conditional formatting for P/L:
   - Click the **Unrealized_P_L** column header
   - In the right panel, click **"Column Options"**
   - Under **"Number Format"**, select **"Currency"** with `$`
   - Under **"Conditional Formatting"**, add:
     - Rule 1: `value > 0` → Green background
     - Rule 2: `value < 0` → Red background

### Step 4: Add Portfolio Allocation Pie Chart

1. Click **"Add New"** → **"Add Widget to Page"**
2. Select:
   - **Widget**: Chart
   - **Table**: Gold_positions
   - Click **"Add to Page"**

3. Configure the chart:
   - In the right panel, under **"Chart"** tab:
     - **Chart Type**: Pie Chart
     - **Label**: Symbol (or Symbol.Symbol if available)
     - **Values**: Current_Market_Value
   - Drag to resize/position next to the table

### Step 5: Add P/L Bar Chart

1. Click **"Add New"** → **"Add Widget to Page"**
2. Select:
   - **Widget**: Chart
   - **Table**: Gold_positions
   - Click **"Add to Page"**

3. Configure:
   - **Chart Type**: Bar Chart
   - **X-Axis**: Symbol
   - **Series**: Unrealized_P_L (drag to top of list)
   - Hide other series by clicking trash icon

### Step 6: Arrange Layout

1. Drag widgets to arrange:
   ```
   ┌─────────────────┬─────────────────┐
   │  Summary Table  │   Pie Chart     │
   │  (Gold Positions)│  (Allocation)   │
   ├─────────────────┴─────────────────┤
   │        Bar Chart (P/L)            │
   └───────────────────────────────────┘
   ```

2. Resize by dragging widget borders

---

## Phase 2: Stock Performance Page

### Step 7: Create Second Page

1. **"Add New"** → **"Add Page"**
2. Name it **"Dashboard - Stock Performance"**

### Step 8: Add Gold Stocks Table

1. Add **Table** widget
2. Select **Gold_stocks** table
3. Show columns: Symbol, Name, Current_Price, Total_Shares, Total_Invested, Avg_Cost_Basis, Current_Market_Value, Total_Return_Pct
4. Save layout

### Step 9: Add Return % Comparison Chart

1. Add **Chart** widget
2. Select **Gold_stocks** table
3. Configure:
   - **Type**: Bar Chart
   - **X-Axis**: Symbol
   - **Series**: Total_Return_Pct

---

## Phase 3: Custom Price History Widget

### Step 10: Host the Widget

**Option A: GitHub Pages (Free)**

1. Create a GitHub repository (e.g., `grist-stock-widgets`)
2. Upload `price-history.html` to the repository
3. Go to **Settings** → **Pages**
4. Select **Deploy from branch** → **main** → **/ (root)**
5. Click **Save**
6. Wait 2-3 minutes
7. Your widget URL will be: `https://yourusername.github.io/grist-stock-widgets/price-history.html`

**Option B: Local Server (Testing)**

```bash
cd /Users/g/Library/CloudStorage/Dropbox/Code/grist-stock-tracker/dashboard-widgets
python -m http.server 8080
```
Widget URL: `http://localhost:8080/price-history.html`

### Step 11: Add Custom Widget to Grist

1. Go to **"Dashboard - Stock Performance"** page
2. **"Add New"** → **"Add Widget to Page"**
3. Select:
   - **Widget**: Custom
   - **Table**: Gold_stocks
4. Paste your widget URL in the **"Custom Widget URL"** field
5. Click **"Add to Page"**

### Step 12: Configure Custom Widget

1. Click the **three-dots menu** on the custom widget
2. Select **"Widget options"**
3. In the **"Custom"** tab:
   - Check **"Full document access"** (allows widget to read Silver_stocks table)
4. The widget should now load and show price history for the selected stock

---

## Phase 4: Link Widgets (Interactivity)

### Step 13: Link Table to Charts

1. On **"Dashboard - Portfolio Overview"** page:
   - Click the **three-dots menu** on the **Pie Chart**
   - Select **"Widget options"**
   - Go to **"Data"** tab
   - Under **"Select By"**, choose your **Gold_positions** table widget
   - Click **"Save"**

2. Now when you click a row in the table, the pie chart will filter to show that stock highlighted

### Step 14: Link Stock Performance Page

1. On **"Dashboard - Stock Performance"** page:
   - Configure the **Return % Bar Chart** to **"Select By"** the Gold_stocks table
   - Configure the **Price History Custom Widget** to **"Select By"** the Gold_stocks table

2. Now clicking a stock in the table updates both charts

---

## Phase 5: Transaction History Page

### Step 15: Create Third Page

1. **"Add New"** → **"Add Page"**
2. Name it **"Dashboard - Transactions"**

### Step 16: Add Transaction Table

1. Add **Table** widget
2. Select **Silver_transactions** table
3. Sort by Date (descending) - click column header
4. Save sort settings

### Step 17: Add Monthly Summary

1. Add **Table** widget
2. Select **Silver_transactions** table
3. Click the **summation icon** (∑) next to table name
4. Select **"Group By"** → **Date** (this creates a summary by month)
5. This will show transaction counts and totals by month

---

## Phase 6: Final Touches

### Step 18: Add Summary Card (Optional)

1. On Portfolio Overview page:
   - Add **Card** widget
   - Select **Gold_positions** table
   - This shows details of the selected position

### Step 19: Set Default Page

1. Click the **Dashboard - Portfolio Overview** page in the left sidebar
2. Click **three-dots menu** → **"Set as default"**
3. Now the dashboard opens first when you open the document

---

## Testing Checklist

- [ ] Portfolio Overview shows all 4 positions with correct data
- [ ] Pie chart shows allocation percentages
- [ ] Bar chart shows green bars for gains, red for losses
- [ ] Clicking a position highlights it in charts
- [ ] Stock Performance page loads custom price history widget
- [ ] Price history updates when selecting different stocks
- [ ] Transaction page shows all 5 transactions sorted by date

---

## Troubleshooting

### Custom Widget Not Loading
- Check browser console for errors (F12)
- Verify URL is accessible (open in new tab)
- Ensure "Full document access" is enabled
- Try refreshing the page

### Charts Not Updating
- Verify "Select By" is configured correctly
- Check that the source table has records selected
- Save the document and reload

### Data Showing as None
- Check that formulas are calculated (they should be now)
- Verify references are set up correctly
- Check browser console for formula errors

---

## Next Steps

1. **Automate Price Updates**: Set up n8n to fetch prices daily
2. **Add More Metrics**: Create calculated fields for portfolio-level stats
3. **Mobile Access**: Grist is responsive, test on mobile browser
4. **Share Dashboard**: Use Grist's sharing to give view-only access
